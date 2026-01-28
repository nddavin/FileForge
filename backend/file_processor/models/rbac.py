"""RBAC Database Models for Role-Based Access Control"""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from backend.file_processor.database import Base

# Many-to-many relationship tables
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True)
)

user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
)


class Role(Base):
    """Role model for RBAC"""
    __tablename__ = 'roles'
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Mapped[Optional[str]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission", 
        secondary=role_permissions, 
        back_populates="roles"
    )
    users: Mapped[List["User"]] = relationship(
        "User", 
        secondary=user_roles, 
        back_populates="roles"
    )
    
    def __repr__(self):
        return f"<Role(name='{self.name}')>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "permissions": [p.name for p in self.permissions]
        }


class Permission(Base):
    """Permission model for granular access control"""
    __tablename__ = 'permissions'
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    resource: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # create, read, update, delete
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).isoformat())
    
    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role", 
        secondary=role_permissions, 
        back_populates="permissions"
    )
    
    def __repr__(self):
        return f"<Permission(name='{self.name}')>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "resource": self.resource,
            "action": self.action,
            "description": self.description,
            "is_active": self.is_active
        }


class AuditLog(Base):
    """Audit log for tracking access and permission changes"""
    __tablename__ = 'audit_logs'
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # login, logout, upload, delete, etc.
    resource: Mapped[str] = mapped_column(String(100), nullable=False)  # file, user, role, etc.
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    details: Mapped[Optional[str]] = Column(Text, nullable=True)  # JSON string
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='success')  # success, failure
    created_at: Mapped[str] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).isoformat())
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(action='{self.action}', resource='{self.resource}')>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "resource": self.resource,
            "resource_id": self.resource_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "status": self.status,
            "created_at": self.created_at
        }


# Default roles and permissions seed data
DEFAULT_ROLES = [
    # Admin - Full access
    {
        "name": "admin",
        "description": "Administrator with full system access",
        "permissions": [
            # Files
            "files:upload", "files:download", "files:view", "files:delete", "files:share",
            "files:view_all", "files:delete_all", "files:manage_sharing",
            # Users
            "users:view", "users:create", "users:update", "users:delete", "users:manage",
            # Roles
            "roles:view", "roles:create", "roles:update", "roles:delete", "roles:manage",
            # Workflows
            "workflows:view", "workflows:create", "workflows:execute", "workflows:delete", "workflows:manage",
            # Settings
            "settings:view", "settings:update", "settings:manage",
            # Audit
            "audit:view", "audit:export",
            # Integrations
            "integrations:view", "integrations:manage", "integrations:configure",
            # Monitoring
            "monitoring:view", "monitoring:manage",
        ]
    },
    # Manager - File and workflow operations
    {
        "name": "manager",
        "description": "Manager with file and workflow management capabilities",
        "permissions": [
            # Files
            "files:upload", "files:download", "files:view", "files:delete", "files:share",
            "files:view_all",
            # Users
            "users:view", "users:create", "users:update",
            # Workflows
            "workflows:view", "workflows:create", "workflows:execute", "workflows:delete",
            # Audit
            "audit:view",
            # Integrations
            "integrations:view",
            # Monitoring
            "monitoring:view",
        ]
    },
    # User - Basic file operations
    {
        "name": "user",
        "description": "Standard user with basic file operations",
        "permissions": [
            # Files
            "files:upload", "files:download", "files:view", "files:share",
            # Workflows
            "workflows:view", "workflows:execute",
        ]
    },
    # Viewer - Read-only access
    {
        "name": "viewer",
        "description": "Read-only access to files and workflows",
        "permissions": [
            # Files
            "files:view", "files:download",
            # Workflows
            "workflows:view",
        ]
    },
]


# Permission definitions
DEFAULT_PERMISSIONS = [
    # Files
    {"name": "files:upload", "resource": "files", "action": "create", "description": "Upload new files"},
    {"name": "files:download", "resource": "files", "action": "read", "description": "Download files"},
    {"name": "files:view", "resource": "files", "action": "read", "description": "View own files"},
    {"name": "files:delete", "resource": "files", "action": "delete", "description": "Delete own files"},
    {"name": "files:share", "resource": "files", "action": "update", "description": "Share files with others"},
    {"name": "files:view_all", "resource": "files", "action": "read", "description": "View all files in system"},
    {"name": "files:delete_all", "resource": "files", "action": "delete", "description": "Delete any file"},
    {"name": "files:manage_sharing", "resource": "files", "action": "update", "description": "Manage file sharing settings"},
    # Users
    {"name": "users:view", "resource": "users", "action": "read", "description": "View user profiles"},
    {"name": "users:create", "resource": "users", "action": "create", "description": "Create new users"},
    {"name": "users:update", "resource": "users", "action": "update", "description": "Update user profiles"},
    {"name": "users:delete", "resource": "users", "action": "delete", "description": "Delete users"},
    {"name": "users:manage", "resource": "users", "action": "update", "description": "Manage user roles and permissions"},
    # Roles
    {"name": "roles:view", "resource": "roles", "action": "read", "description": "View roles"},
    {"name": "roles:create", "resource": "roles", "action": "create", "description": "Create new roles"},
    {"name": "roles:update", "resource": "roles", "action": "update", "description": "Update roles"},
    {"name": "roles:delete", "resource": "roles", "action": "delete", "description": "Delete roles"},
    {"name": "roles:manage", "resource": "roles", "action": "update", "description": "Manage role permissions"},
    # Workflows
    {"name": "workflows:view", "resource": "workflows", "action": "read", "description": "View workflows"},
    {"name": "workflows:create", "resource": "workflows", "action": "create", "description": "Create workflows"},
    {"name": "workflows:execute", "resource": "workflows", "action": "update", "description": "Execute workflows"},
    {"name": "workflows:delete", "resource": "workflows", "action": "delete", "description": "Delete workflows"},
    {"name": "workflows:manage", "resource": "workflows", "action": "update", "description": "Manage workflow configurations"},
    # Settings
    {"name": "settings:view", "resource": "settings", "action": "read", "description": "View system settings"},
    {"name": "settings:update", "resource": "settings", "action": "update", "description": "Update system settings"},
    {"name": "settings:manage", "resource": "settings", "action": "update", "description": "Manage all settings"},
    # Audit
    {"name": "audit:view", "resource": "audit", "action": "read", "description": "View audit logs"},
    {"name": "audit:export", "resource": "audit", "action": "read", "description": "Export audit logs"},
    # Integrations
    {"name": "integrations:view", "resource": "integrations", "action": "read", "description": "View integrations"},
    {"name": "integrations:manage", "resource": "integrations", "action": "update", "description": "Manage integrations"},
    {"name": "integrations:configure", "resource": "integrations", "action": "update", "description": "Configure integration settings"},
    # Monitoring
    {"name": "monitoring:view", "resource": "monitoring", "action": "read", "description": "View monitoring data"},
    {"name": "monitoring:manage", "resource": "monitoring", "action": "update", "description": "Manage monitoring settings"},
]
