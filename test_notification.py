# Save this as test_notification.py in your project root
from utils.notification import NotificationSystem  # Adjust import based on your implementation
import datetime

def test_notification():
    print("Testing notification system...")
    
    # Create notification instance
    notification = NotificationSystem()
    
    # Test data for a violation
    test_data = {
        "license_plate": "TEST123",
        "speed": 85.5,
        "speed_limit": 60.0,
        "location": "Test Location",
        "timestamp": datetime.datetime.now(),
        "image_path": "output/violations/TEST123_violation.jpg"
    }
    
    # Send test notification
    try:
        result = notification.send_violation_notification(test_data)
        print(f"Notification sent: {result}")
    except Exception as e:
        print(f"Error sending notification: {e}")

if __name__ == "__main__":
    test_notification()