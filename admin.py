# Save this as admin.py in your project root
from utils.database import ViolationDatabase
import os
import datetime

def admin_interface():
    db = ViolationDatabase()
    
    while True:
        print("\n===== Vehicle Detection System Admin =====")
        print("1. View recent violations")
        print("2. Search by license plate")
        print("3. View violation details")
        print("4. Delete a violation")
        print("5. View system statistics")
        print("6. Exit")
        
        choice = input("Enter your choice (1-6): ")
        
        if choice == "1":
            limit = input("How many violations to display? (default 10): ")
            limit = int(limit) if limit.isdigit() else 10
            violations = db.get_violations(limit)
            print(f"\nFound {len(violations)} recent violations:")
            for v in violations:
                over_by = v.speed - v.speed_limit
                print(f"ID: {v.id}, Plate: {v.license_plate}, Speed: {v.speed}/{v.speed_limit} km/h (+{over_by:.1f}), Time: {v.timestamp}")
                
        elif choice == "2":
            plate = input("Enter license plate to search: ")
            violations = db.get_violations_by_plate(plate)
            print(f"\nFound {len(violations)} violations for plate {plate}:")
            for v in violations:
                print(f"ID: {v.id}, Speed: {v.speed}/{v.speed_limit} km/h, Time: {v.timestamp}")
                
        elif choice == "3":
            vid = input("Enter violation ID: ")
            if not vid.isdigit():
                print("Invalid ID")
                continue
            v = db.get_violation_by_id(int(vid))
            if v:
                print("\nViolation Details:")
                print(f"ID: {v.id}")
                print(f"License Plate: {v.license_plate}")
                print(f"Speed: {v.speed} km/h")
                print(f"Speed Limit: {v.speed_limit} km/h")
                print(f"Violation Amount: {v.speed - v.speed_limit:.1f} km/h over limit")
                print(f"Location: {v.location}")
                print(f"Time: {v.timestamp}")
                print(f"Image: {v.image_path}")
                
                # Check if image exists
                if v.image_path and os.path.exists(v.image_path):
                    print(f"Image file exists: Yes ({os.path.getsize(v.image_path)/1024:.1f} KB)")
                else:
                    print("Image file exists: No")
            else:
                print("Violation not found")
                
        elif choice == "4":
            vid = input("Enter violation ID to delete: ")
            if not vid.isdigit():
                print("Invalid ID")
                continue
            confirm = input(f"Are you sure you want to delete violation ID {vid}? (y/n): ")
            if confirm.lower() == 'y':
                success = db.delete_violation(int(vid))
                if success:
                    print("Violation deleted successfully")
                else:
                    print("Failed to delete violation (ID not found)")
            else:
                print("Deletion cancelled")
                
        elif choice == "5":
            # System statistics
            all_violations = db.get_violations(9999)  # Get all violations
            print("\nSystem Statistics:")
            print(f"Total violations recorded: {len(all_violations)}")
            
            if all_violations:
                avg_speed = sum(v.speed for v in all_violations) / len(all_violations)
                avg_over = sum(v.speed - v.speed_limit for v in all_violations) / len(all_violations)
                print(f"Average detected speed: {avg_speed:.1f} km/h")
                print(f"Average speed over limit: {avg_over:.1f} km/h")
                
                # Most frequent offenders
                plates = {}
                for v in all_violations:
                    plates[v.license_plate] = plates.get(v.license_plate, 0) + 1
                    
                print("\nTop offenders:")
                top_plates = sorted(plates.items(), key=lambda x: x[1], reverse=True)[:5]
                for plate, count in top_plates:
                    print(f"License plate {plate}: {count} violations")
                
        elif choice == "6":
            break
            
        else:
            print("Invalid choice")
    
    db.close()
    print("Admin interface closed")

if __name__ == "__main__":
    admin_interface()