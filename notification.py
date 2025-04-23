# Save this as utils/notification.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='notifications.log'
)
logger = logging.getLogger('ViolationNotification')

class NotificationSystem:
    """System for sending notifications about speed violations"""
    
    def __init__(self, email_config=None):
        """
        Initialize notification system
        
        Args:
            email_config: Dictionary with email configuration (optional)
                          Should contain: 'smtp_server', 'port', 'username', 'password',
                          'sender', 'recipients'
        """
        # Default to log-based notifications if no email config provided
        self.email_config = email_config
        self.notification_log = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                         'output', 'notifications.log')
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(self.notification_log), exist_ok=True)
        
    def send_violation_notification(self, violation_data):
        """
        Send notification about a speed violation
        
        Args:
            violation_data: Dictionary with violation details
                            Should contain: license_plate, speed, speed_limit,
                            location, timestamp, image_path
                            
        Returns:
            Boolean indicating success or failure
        """
        try:
            # Log the violation
            self._log_violation(violation_data)
            
            # Send email if configured
            if self.email_config:
                self._send_email_notification(violation_data)
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            return False
            
    def _log_violation(self, violation_data):
        """Log violation to file"""
        timestamp = violation_data['timestamp']
        license_plate = violation_data['license_plate']
        speed = violation_data['speed']
        speed_limit = violation_data['speed_limit']
        location = violation_data['location']
        
        message = (f"VIOLATION: {timestamp} - License Plate: {license_plate}, "
                  f"Speed: {speed} km/h, Limit: {speed_limit} km/h, "
                  f"Location: {location}")
        
        # Log to system log
        logger.info(message)
        
        # Write to specific notification log file
        with open(self.notification_log, 'a') as f:
            f.write(f"{message}\n")
            
    def _send_email_notification(self, violation_data):
        """Send email notification"""
        if not self.email_config:
            return False
            
        # Create message
        msg = MIMEMultipart()
        msg['From'] = self.email_config['sender']
        msg['To'] = ', '.join(self.email_config['recipients'])
        msg['Subject'] = f"Speed Violation: {violation_data['license_plate']}"
        
        # Message body
        body = f"""
        Speed Violation Detected:
        
        License Plate: {violation_data['license_plate']}
        Speed: {violation_data['speed']} km/h
        Speed Limit: {violation_data['speed_limit']} km/h
        Location: {violation_data['location']}
        Time: {violation_data['timestamp']}
        
        This is an automated notification.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to server and send
        try:
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['port'])
            server.starttls()
            server.login(self.email_config['username'], self.email_config['password'])
            server.send_message(msg)
            server.quit()
            logger.info(f"Email notification sent for {violation_data['license_plate']}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False