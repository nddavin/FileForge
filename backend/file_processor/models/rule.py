from sqlalchemy import Column, Integer, String, ForeignKey

from ..database import Base


class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    condition = Column(String)  # JSON string
    action = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
