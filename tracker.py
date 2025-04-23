import time
import numpy as np

class ObjectTracker:
    """
    Simple IOU-based tracker for vehicles
    """
    def __init__(self, iou_threshold=0.3, max_age=1.0):
        """
        Initialize the tracker
        
        Args:
            iou_threshold: Minimum IOU to consider it's the same object
            max_age: Maximum time (in seconds) to keep tracking an object after it disappears
        """
        self.tracked_objects = {}  # Dictionary of tracked objects
        self.next_id = 0  # Next available object ID
        self.iou_threshold = iou_threshold
        self.max_age = max_age
    
    def update(self, detections):
        """
        Update tracker with new detections
        
        Args:
            detections: List of detection dictionaries with 'bbox', 'confidence', 'class_id'
            
        Returns:
            Dictionary of tracked objects with their IDs
        """
        # Result will contain currently tracked objects
        current_tracked = {}
        
        # Match detections to existing tracked objects
        for detection in detections:
            bbox = detection['bbox']
            matched = False
            
            # Find the best match among tracked objects
            best_iou = self.iou_threshold
            best_id = None
            
            for obj_id, obj_data in self.tracked_objects.items():
                iou = self.calculate_iou(bbox, obj_data['bbox'])
                if iou > best_iou:
                    best_iou = iou
                    best_id = obj_id
            
            if best_id is not None:
                # Update the tracked object
                self.tracked_objects[best_id].update({
                    'bbox': bbox,
                    'confidence': detection['confidence'],
                    'class_id': detection['class_id'],
                    'last_seen': time.time()
                })
                current_tracked[best_id] = self.tracked_objects[best_id]
                matched = True
            
            if not matched:
                # Create new tracked object
                new_id = self.next_id
                self.next_id += 1
                self.tracked_objects[new_id] = {
                    'bbox': bbox,
                    'confidence': detection['confidence'],
                    'class_id': detection['class_id'],
                    'last_seen': time.time(),
                    'first_seen': time.time()
                }
                current_tracked[new_id] = self.tracked_objects[new_id]
        
        # Remove old tracked objects
        current_time = time.time()
        for obj_id in list(self.tracked_objects.keys()):
            if current_time - self.tracked_objects[obj_id]['last_seen'] > self.max_age:
                del self.tracked_objects[obj_id]
        
        return current_tracked
    
    @staticmethod
    def calculate_iou(bbox1, bbox2):
        """
        Calculate the Intersection over Union between two bounding boxes
        
        Args:
            bbox1: First bounding box (x1, y1, x2, y2)
            bbox2: Second bounding box (x1, y1, x2, y2)
            
        Returns:
            IOU value between 0 and 1
        """
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        
        # Calculate intersection area
        x_left = max(x1_1, x1_2)
        y_top = max(y1_1, y1_2)
        x_right = min(x2_1, x2_2)
        y_bottom = min(y2_1, y2_2)
        
        if x_right < x_left or y_bottom < y_top:
            return 0.0
            
        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        
        # Calculate union area
        bbox1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
        bbox2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
        union_area = bbox1_area + bbox2_area - intersection_area
        
        # Calculate IOU
        return intersection_area / union_area if union_area > 0 else 0