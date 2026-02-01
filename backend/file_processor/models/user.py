from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime, timezone

from ..database import Base

if TYPE_CHECKING:
    from .rbac import AuditLog
    from .task_assignment import TeamMember


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    roles = Column(String, default="user")  # comma-separated roles
    
    # Additional fields for task assignment integration
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    team_member: Mapped[Optional["TeamMember"]] = relationship(
        "TeamMember", back_populates="user", uselist=False
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="user")
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role"""
        return role_name in (self.roles or "").split(",")
    
    def is_team_member(self) -> bool:
        """Check if user is registered as a team member"""
        return self.team_member is not None and self.team_member.is_active
