import cv2
import numpy as np
import easyocr
import re

class LicensePlateRecognizer:
    """
    Detects and recognizes license plates on vehicles
    """
    def __init__(self, min_confidence=0.5, min_plate_size=(60, 20)):
        """
        Initialize the license plate recognizer
        
        Args:
            min_confidence: Minimum confidence for OCR results
            min_plate_size: Minimum width and height for license plate candidates
        """
        print("Initializing EasyOCR license plate reader...")
        self.reader = easyocr.Reader(['en'])  # Initialize EasyOCR with English
        self.min_confidence = min_confidence
        self.min_width, self.min_height = min_plate_size
        print("License plate reader initialized")
    
    def find_license_plate_area(self, vehicle_img):
        """
        Find potential license plate regions in the vehicle image
        
        Args:
            vehicle_img: Image of the vehicle
            
        Returns:
            Image of potential license plate or None
        """
        if vehicle_img is None or vehicle_img.size == 0:
            return None
            
        # Make a copy to avoid modifying the original
        img = vehicle_img.copy()
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply filters to enhance edges
        gray = cv2.bilateralFilter(gray, 11, 17, 17)
        edged = cv2.Canny(gray, 30, 200)
        
        # Find contours
        contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
        
        plate_img = None
        
        # Iterate through contours to find license plate candidates
        for c in contours:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            
            # License plates typically have 4 corners (rectangle)
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(c)
                
                # Check minimum size to avoid small noise
                if w < self.min_width or h < self.min_height:
                    continue
                    
                # Calculate aspect ratio (width/height)
                plate_aspect_ratio = w / float(h)
                
                # Typical license plate aspect ratios
                if 1.5 <= plate_aspect_ratio <= 5.0:
                    plate_img = img[y:y+h, x:x+w]
                    break
        
        return plate_img
    
    def clean_plate_text(self, text):
        """
        Clean and normalize license plate text
        
        Args:
            text: Recognized text
            
        Returns:
            Cleaned license plate text
        """
        if not text:
            return None
            
        # Remove spaces and special characters
        plate_text = ''.join(c for c in text if c.isalnum())
        
        # Convert to uppercase
        plate_text = plate_text.upper()
        
        # Filter out obviously wrong recognitions
        if len(plate_text) < 4 or len(plate_text) > 10:
            return None
            
        return plate_text
    
    def recognize_text(self, img):
        """
        Recognize text in an image using EasyOCR
        
        Args:
            img: Image containing text
            
        Returns:
            Recognized text or None
        """
        if img is None:
            return None
            
        try:
            # Use EasyOCR to recognize text
            results = self.reader.readtext(img)
            
            # Filter results by confidence
            high_conf_results = [res for res in results if res[2] > self.min_confidence]
            
            if high_conf_results:
                # Join all detected text
                plate_text = ' '.join([res[1] for res in high_conf_results])
                return self.clean_plate_text(plate_text)
            return None
        except Exception as e:
            print(f"Error in OCR: {e}")
            return None
    
    def process_vehicle(self, vehicle_img):
        """
        Main function to process a vehicle image and extract license plate
        
        Args:
            vehicle_img: Image of the vehicle
            
        Returns:
            License plate text or None
        """
        plate_img = self.find_license_plate_area(vehicle_img)
        if plate_img is not None:
            plate_text = self.recognize_text(plate_img)
            return plate_text
        return None