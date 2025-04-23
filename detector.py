import torch
from ultralytics import YOLO
import numpy as np

class VehicleDetector:
    """
    Handles vehicle detection using YOLOv8 model
    """
    def __init__(self, model_name='yolov8n', confidence_threshold=0.5, classes=None):
        """
        Initialize the vehicle detector
        
        Args:
            model_name: YOLOv8 model variant to use ('yolov8n', 'yolov8s', etc.)
            confidence_threshold: Minimum confidence score for detection
            classes: List of class IDs to detect (COCO dataset class IDs)
                     [2: car, 3: motorcycle, 5: bus, 7: truck]
        """
        print(f"Loading {model_name} model...")
        self.model = YOLO(model_name)
        self.confidence_threshold = confidence_threshold
        self.classes = classes  # List of class IDs to detect
        print(f"Model loaded. Detecting classes: {classes}")
    
    def detect(self, frame):
        """
        Detect vehicles in a frame
        
        Args:
            frame: OpenCV image (numpy array)
            
        Returns:
            List of dictionaries containing detection information
        """
        # Run detection
        results = self.model(frame, conf=self.confidence_threshold, classes=self.classes)
        
        # Process results
        detections = []
        for r in results:
            boxes = r.boxes
            for box in boxes:
                # Get box coordinates (xyxy format)
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                
                # Get confidence and class
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                
                # Add to detections
                detections.append({
                    'bbox': (int(x1), int(y1), int(x2), int(y2)),
                    'confidence': confidence,
                    'class_id': class_id
                })
        
        return detections