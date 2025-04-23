import numpy as np
import time

class SpeedEstimator:
    """
    Estimates vehicle speed based on movement between frames
    """
    def __init__(self, distance_calibration=10.0, max_age_frames=30):
        """
        Initialize the speed estimator
        
        Args:
            distance_calibration: Real-world distance in meters that corresponds to specific pixel distance
            max_age_frames: Maximum frames to keep object in tracking queue
        """
        self.distance_calibration = distance_calibration
        self.tracked_objects = {}
        self.fps = 30  # Default FPS, will be updated
        self.max_age_frames = max_age_frames
        self.last_cleanup = 0
    
    def set_fps(self, fps):
        """Set the frames per second for speed calculation"""
        self.fps = fps if fps > 0 else 30
    
    def update_object(self, object_id, bbox, frame_number):
        """
        Update object position and calculate speed
        
        Args:
            object_id: Unique ID of tracked object
            bbox: Bounding box (x1, y1, x2, y2)
            frame_number: Current frame number
            
        Returns:
            Estimated speed in km/h
        """
        # Calculate center of bounding box
        center_x = (bbox[0] + bbox[2]) / 2
        center_y = (bbox[1] + bbox[3]) / 2
        
        current_time = frame_number / self.fps if self.fps > 0 else time.time()
        
        if object_id in self.tracked_objects:
            # Calculate speed based on pixel movement and time difference
            prev_pos = self.tracked_objects[object_id]['positions'][-1]
            prev_time = self.tracked_objects[object_id]['timestamps'][-1]
            
            pixel_distance = np.sqrt((center_x - prev_pos[0])**2 + (center_y - prev_pos[1])**2)
            time_diff = current_time - prev_time
            
            if time_diff > 0:
                # Convert pixel distance to real-world distance using calibration
                # and calculate speed in km/h
                speed = (pixel_distance / self.distance_calibration) * (1.0 / time_diff) * 3.6  # km/h
                self.tracked_objects[object_id]['speeds'].append(speed)
                
                # Update position and timestamp
                self.tracked_objects[object_id]['positions'].append((center_x, center_y))
                self.tracked_objects[object_id]['timestamps'].append(current_time)
                self.tracked_objects[object_id]['frame_numbers'].append(frame_number)
                
                # Return average speed over last few measurements to smooth results
                recent_speeds = self.tracked_objects[object_id]['speeds'][-5:]
                return sum(recent_speeds) / len(recent_speeds) if recent_speeds else 0
            else:
                return 0
        else:
            # Initialize tracking for new object
            self.tracked_objects[object_id] = {
                'positions': [(center_x, center_y)],
                'timestamps': [current_time],
                'frame_numbers': [frame_number],
                'speeds': []
            }
            return 0
    
    def cleanup_old_objects(self, current_frame_number):
        """
        Remove objects that haven't been seen recently
        
        Args:
            current_frame_number: Current frame number
        """
        if current_frame_number - self.last_cleanup > 10:  # Do cleanup every 10 frames
            objects_to_remove = []
            
            for obj_id, data in self.tracked_objects.items():
                if current_frame_number - data['frame_numbers'][-1] > self.max_age_frames:
                    objects_to_remove.append(obj_id)
            
            for obj_id in objects_to_remove:
                del self.tracked_objects[obj_id]
            
            self.last_cleanup = current_frame_number