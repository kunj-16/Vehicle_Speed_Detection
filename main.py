import cv2
import time
import argparse
import os
import yaml
from datetime import datetime

# Import our modules
from models.detector import VehicleDetector
from models.tracker import ObjectTracker
from models.speed_estimator import SpeedEstimator
from models.license_plate_recognizer import LicensePlateRecognizer
from utils.database import ViolationDatabase
from utils.notification import NotificationSystem

def parse_args():
    parser = argparse.ArgumentParser(description='Vehicle Detection and Speed Enforcement System')
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to configuration file')
    parser.add_argument('--input', type=str, help='Override input source from config')
    parser.add_argument('--speed_limit', type=float, help='Override speed limit from config')
    return parser.parse_args()

def load_config(config_path):
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

class VehicleDetectionSystem:
    def __init__(self, config):
        self.config = config
        
        # Initialize detector with YOLOv8n
        self.detector = VehicleDetector(
            model_name=config['detection']['model'],
            confidence_threshold=config['detection']['confidence_threshold'],
            classes=config['detection']['classes']
        )
        
        # Initialize tracker
        self.tracker = ObjectTracker()
        
        # Initialize speed estimator
        self.speed_estimator = SpeedEstimator(
            distance_calibration=config['speed']['distance_calibration'],
            max_age_frames=config['speed']['max_tracking_age']
        )
        
        # Initialize license plate recognizer
        self.license_recognizer = LicensePlateRecognizer(
            min_confidence=config['license_plate']['min_confidence'],
            min_plate_size=config['license_plate']['min_plate_size']
        )
        
        # Initialize database
        self.db = ViolationDatabase(config['database']['path'])
        
        # Initialize notification system
        if config['notification']['enabled']:
            self.notification = NotificationSystem(config['notification'])
        else:
            self.notification = None
        
        # Create output directories
        os.makedirs(config['system']['output_dir'], exist_ok=True)
        os.makedirs(os.path.join(config['system']['output_dir'], 'violations'), exist_ok=True)
        
        # Track violations to prevent duplicates
        self.violation_cooldown = {}
        
    def process_frame(self, frame, frame_number):
        # Detect vehicles
        detections = self.detector.detect(frame)
        
        # Update tracker with new detections
        tracked_objects = self.tracker.update(detections)
        
        # Process each tracked object
        for obj_id, detection in tracked_objects.items():
            x1, y1, x2, y2 = detection['bbox']
            confidence = detection['confidence']
            class_id = detection['class_id']
            
            # Get vehicle image
            vehicle_img = frame[y1:y2, x1:x2]
            
            # Calculate speed
            speed = self.speed_estimator.update_object(obj_id, (x1, y1, x2, y2), frame_number)
            
            # Draw bounding box and speed
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"ID: {obj_id}, Speed: {speed:.1f} km/h", 
                      (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Check for speed violation
            speed_limit = self.config['speed']['limit_kmh']
            if speed > speed_limit and speed < 200:  # Upper limit to filter outliers
                # Process license plate if speed is over the limit
                license_plate = self.license_recognizer.process_vehicle(vehicle_img)
                
                if license_plate and len(license_plate) >= 4:
                    # Create a cooldown key (one violation per minute per plate)
                    cooldown_key = f"{license_plate}_{frame_number // (self.config['system']['fps'] * 60)}"
                    
                    if cooldown_key not in self.violation_cooldown:
                        self.violation_cooldown[cooldown_key] = True
                        
                        # Save violation image
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        violation_img_path = os.path.join(
                            self.config['system']['output_dir'], 
                            'violations', 
                            f"{license_plate}_{timestamp}.jpg"
                        )
                        cv2.imwrite(violation_img_path, vehicle_img)
                        
                        # Record violation in database
                        self.db.record_violation(
                            license_plate=license_plate,
                            speed=speed,
                            speed_limit=speed_limit,
                            location=self.config['system']['location'],
                            image_path=violation_img_path
                        )
                        
                        # Send notification if enabled
                        if self.notification:
                            violation_data = {
                                'license_plate': license_plate,
                                'speed': speed,
                                'speed_limit': speed_limit,
                                'location': self.config['system']['location'],
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                            self.notification.send_email_notification(violation_data)
                        
                        print(f"Violation detected: {license_plate} at {speed:.1f} km/h")
                        
                        # Display violation on frame
                        cv2.putText(frame, f"VIOLATION: {license_plate}", 
                                  (x1, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Clean up old tracking objects
        self.speed_estimator.cleanup_old_objects(frame_number)
        
        return frame
    
    def cleanup(self):
        """Clean up resources"""
        self.db.close()

def main():
    # Parse arguments and load config
    args = parse_args()
    config = load_config(args.config)
    
    # Override config with command line arguments if provided
    if args.input:
        config['input'] = args.input
    if args.speed_limit:
        config['speed']['limit_kmh'] = args.speed_limit
    
    # Initialize the system
    system = VehicleDetectionSystem(config)
    
    # Open video capture
    try:
        if config['input'].isdigit():
            cap = cv2.VideoCapture(int(config['input']))
        else:
            cap = cv2.VideoCapture(config['input'])
    except:
        print(f"Error: Could not open video source {config['input']}")
        return
        
    if not cap.isOpened():
        print(f"Error: Could not open video source {config['input']}")
        return
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30  # Default FPS if not available
    config['system']['fps'] = fps
    system.speed_estimator.set_fps(fps)
    
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Create output video writer
    output_path = os.path.join(config['system']['output_dir'], 'output.mp4')
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (frame_width, frame_height))
    
    frame_number = 0
    start_time = time.time()
    frames_processed = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Process the frame
            processed_frame = system.process_frame(frame, frame_number)
            
            # Write frame to output video
            out.write(processed_frame)
            
            # Add speed limit display
            cv2.putText(processed_frame, f"Speed Limit: {config['speed']['limit_kmh']} km/h", 
                      (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Calculate and display FPS
            frames_processed += 1
            if frames_processed % 10 == 0:
                elapsed_time = time.time() - start_time
                current_fps = frames_processed / elapsed_time if elapsed_time > 0 else 0
                cv2.putText(processed_frame, f"FPS: {current_fps:.1f}", 
                          (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Display the processed frame
            cv2.imshow('Vehicle Detection System', processed_frame)
            
            # Increment frame number
            frame_number += 1
            
            # Check for exit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("Processing interrupted by user")
    finally:
        # Clean up resources
        cap.release()
        out.release()
        cv2.destroyAllWindows()
        system.cleanup()
        
    print(f"Processing complete. Output saved to {output_path}")
    print(f"Processed {frame_number} frames in {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    main()