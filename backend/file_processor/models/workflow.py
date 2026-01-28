from sqlalchemy import Column, Integer, String, ForeignKey

from ..database import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    steps = Column(String)  # JSON string
    user_id = Column(Integer, ForeignKey("users.id"))
