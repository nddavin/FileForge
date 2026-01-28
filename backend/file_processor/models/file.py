from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from ..database import Base


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    file_path = Column(String)
    file_type = Column(String)
    size = Column(Integer)
    uploaded_at = Column(DateTime)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")
