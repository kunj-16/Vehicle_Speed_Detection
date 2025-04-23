from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()

class ViolationRecord(Base):
    """Database model for speed violations"""
    __tablename__ = 'violations'
    
    id = Column(Integer, primary_key=True)
    license_plate = Column(String)
    speed = Column(Float)
    speed_limit = Column(Float)
    timestamp = Column(DateTime)
    location = Column(String)
    image_path = Column(String)
    
    def __repr__(self):
        return f"<Violation(license_plate='{self.license_plate}', speed={self.speed})>"

class ViolationDatabase:
    """Handles database operations for vehicle violations"""
    def __init__(self, db_path='sqlite:///violations.db'):
        """
        Initialize database connection
        
        Args:
            db_path: SQLAlchemy database connection string
        """
        self.engine = create_engine(db_path)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        print(f"Database initialized at {db_path}")
    
    def record_violation(self, license_plate, speed, speed_limit, location="Unknown", image_path=None):
        """
        Record a new speed violation
        
        Args:
            license_plate: Vehicle license plate
            speed: Detected speed in km/h
            speed_limit: Speed limit in km/h
            location: Location name
            image_path: Path to saved violation image
            
        Returns:
            ID of the new violation record
        """
        violation = ViolationRecord(
            license_plate=license_plate,
            speed=speed,
            speed_limit=speed_limit,
            timestamp=datetime.datetime.now(),
            location=location,
            image_path=image_path
        )
        
        self.session.add(violation)
        self.session.commit()
        return violation.id
    
    def get_violations(self, limit=100):
        """
        Get recent violations
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of violation records ordered by timestamp (newest first)
        """
        return self.session.query(ViolationRecord).order_by(
            ViolationRecord.timestamp.desc()
        ).limit(limit).all()
    
    def get_violation_by_id(self, violation_id):
        """
        Get a specific violation by ID
        
        Args:
            violation_id: ID of the violation to retrieve
            
        Returns:
            ViolationRecord object or None if not found
        """
        return self.session.query(ViolationRecord).filter(
            ViolationRecord.id == violation_id
        ).first()
    
    def get_violations_by_plate(self, license_plate):
        """
        Get all violations for a specific license plate
        
        Args:
            license_plate: License plate to search for
            
        Returns:
            List of violation records for the given plate
        """
        return self.session.query(ViolationRecord).filter(
            ViolationRecord.license_plate == license_plate
        ).order_by(ViolationRecord.timestamp.desc()).all()
    
    def delete_violation(self, violation_id):
        """
        Delete a violation record
        
        Args:
            violation_id: ID of the violation to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        violation = self.get_violation_by_id(violation_id)
        if violation:
            self.session.delete(violation)
            self.session.commit()
            return True
        return False
    
    def close(self):
        """Close the database session"""
        self.session.close()