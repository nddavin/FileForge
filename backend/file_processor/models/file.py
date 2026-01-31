from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship

from ..database import Base


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    file_path = Column(String)
    file_type = Column(String)
    size = Column(Integer)
    content_type = Column(String, default="application/octet-stream")
    uploaded_at = Column(DateTime)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Extended fields for sermon processing
    name = Column(String)  # Display name
    path = Column(String)  # File path
    status = Column(String, default="pending")  # pending, processing, processed, error
    metadata = Column(JSON, default=dict)  # Sermon metadata
    tags = Column(JSON, default=list)  # File tags
    folder_id = Column(String, nullable=True)  # Target folder for sorting
    sermon_package_id = Column(String, nullable=True)  # Package ID for grouped files
    
    # Quality and analysis fields
    quality_score = Column(Integer, nullable=True)
    preacher_id = Column(String, nullable=True)
    location_city = Column(String, nullable=True)
    primary_language = Column(String, nullable=True)
    
    user = relationship("User")
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "filename": self.filename,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "size": self.size,
            "content_type": self.content_type,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "name": self.name,
            "path": self.path,
            "status": self.status,
            "metadata": self.metadata or {},
            "tags": self.tags or [],
            "folder_id": self.folder_id,
            "sermon_package_id": self.sermon_package_id,
            "quality_score": self.quality_score,
            "preacher_id": self.preacher_id,
            "location_city": self.location_city,
            "primary_language": self.primary_language,
        }


class SortingRule(Base):
    """Sorting rules for smart file organization"""
    __tablename__ = "sorting_rules"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(String, default="default")
    name = Column(String, nullable=False)
    conditions = Column(JSON, default=list)  # List of condition objects
    target_folder = Column(String, nullable=False)
    priority = Column(Integer, default=0)
    auto_apply = Column(Boolean, default=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "church_id": self.church_id,
            "name": self.name,
            "conditions": self.conditions or [],
            "target_folder": self.target_folder,
            "priority": self.priority,
            "auto_apply": self.auto_apply,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
