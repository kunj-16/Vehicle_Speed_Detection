# Save this as test_database.py in your project root
from utils.database import ViolationDatabase

def test_database():
    print("Initializing database connection...")
    db = ViolationDatabase()
    
    # Check if violations are being stored
    violations = db.get_violations()
    print(f"Found {len(violations)} violations in database")
    
    # Print some details if violations exist
    if violations:
        print("\nMost recent violations:")
        for v in violations[:5]:  # Show up to 5 most recent
            print(f"ID: {v.id}, Plate: {v.license_plate}, Speed: {v.speed} km/h, " +
                f"Limit: {v.speed_limit} km/h, Time: {v.timestamp}")
    else:
        print("No violations found in database.")
    
    db.close()
    print("Database connection closed.")

if __name__ == "__main__":
    test_database()