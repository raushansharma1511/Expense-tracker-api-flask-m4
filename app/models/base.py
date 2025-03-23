import uuid
from ..extensions import db
from datetime import datetime,timezone

class BaseModel(db.Model):
    """Base model with default fields"""
    
    __abstract__ = True 
    
    def utc_now():
        """Return the current UTC time with timezone awareness"""
        return datetime.now(timezone.utc)
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    
    def delete(self):
        """Soft delete the instance."""
        self.is_deleted = True
        db.session.commit()


