"""File Processor Models

This module exports all database models for the file processor application.
"""

# User and RBAC models
from .user import User
from .rbac import Role, Permission, AuditLog, role_permissions, user_roles

# File models
from .file import File

# Workflow models
from .workflow import Workflow
from .rule import SortingRule

# Task Assignment models
from .task_assignment import (
    # Enums
    TaskType,
    TaskStatus,
    WorkflowStatus,
    TeamRole,
    # Models
    Skill,
    TeamMember,
    TaskWorkflow,
    TaskAssignment,
    TaskAuditLog,
    # Association tables
    team_member_skills,
    # Constants
    DEFAULT_SKILLS,
    TASK_TYPE_REQUIRED_SKILLS,
)

__all__ = [
    # User and RBAC
    "User",
    "Role",
    "Permission",
    "AuditLog",
    "role_permissions",
    "user_roles",
    # File
    "File",
    # Workflow
    "Workflow",
    "SortingRule",
    # Task Assignment
    "TaskType",
    "TaskStatus",
    "WorkflowStatus",
    "TeamRole",
    "Skill",
    "TeamMember",
    "TaskWorkflow",
    "TaskAssignment",
    "TaskAuditLog",
    "team_member_skills",
    "DEFAULT_SKILLS",
    "TASK_TYPE_REQUIRED_SKILLS",
]
