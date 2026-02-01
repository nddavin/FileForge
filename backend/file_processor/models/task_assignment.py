"""Task Assignment Models for Skill-Based Workflow Orchestration

This module defines database models for:
- Team members with skills (transcription, video processing, location tagging, quality checks)
- Tasks assigned to team members based on skills
- Workflow state tracking
- Task assignments with RLS support
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from enum import Enum as PyEnum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Table,
    JSON,
    Enum,
    Float,
    Index,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ARRAY
import uuid

from file_processor.database import Base


# ==================== Enums ====================

class TaskType(str, PyEnum):
    """Types of tasks that can be assigned"""
    TRANSCRIPTION = "transcription"           # Whisper AI
    VIDEO_PROCESSING = "video_processing"     # FFmpeg
    LOCATION_TAGGING = "location_tagging"     # EXIFTool
    ARTWORK_QUALITY = "artwork_quality"       # Artwork/quality checks
    METADATA_AI = "metadata_ai"               # AI metadata extraction
    THUMBNAIL_GENERATION = "thumbnail_generation"
    SOCIAL_CLIP = "social_clip"
    DISTRIBUTION = "distribution"


class TaskStatus(str, PyEnum):
    """Status of a task"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REVIEW_REQUIRED = "review_required"


class WorkflowStatus(str, PyEnum):
    """Status of a workflow"""
    CREATED = "created"
    INTAKE = "intake"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL_FAILURE = "partial_failure"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TeamRole(str, PyEnum):
    """Team member roles"""
    EDITOR = "editor"           # Full access to all tasks
    PROCESSOR = "processor"     # Task-specific access
    MANAGER = "manager"         # Can view and manage all tasks
    ADMIN = "admin"             # Full system access
    AUDIO_ENGINEER = "audio_engineer"       # Audio processing and quality
    VIDEO_PROCESSOR = "video_processor"     # Video optimization and encoding
    TRANSCRIBER = "transcriber"             # Transcription and metadata
    LOCATION_TAGGER = "location_tagger"     # GPS and geocoding
    MEDIA_COORDINATOR = "media_coordinator" # Task assignment and workflow


# ==================== Association Tables ====================

team_member_skills = Table(
    "team_member_skills",
    Base.metadata,
    Column(
        "team_member_id",
        Integer,
        ForeignKey("team_members.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "skill_id",
        Integer,
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


# ==================== Models ====================

class Skill(Base):
    """Skills that team members can have"""
    
    __tablename__ = "skills"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # e.g., 'transcription', 'video', 'metadata', 'quality'
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    required_tools: Mapped[List[str]] = mapped_column(
        ARRAY(String), default=list
    )  # e.g., ['whisper', 'ffmpeg', 'exiftool']
    proficiency_levels: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict
    )  # {"beginner": 1, "intermediate": 2, "expert": 3}
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    team_members: Mapped[List["TeamMember"]] = relationship(
        "TeamMember", secondary=team_member_skills, back_populates="skills"
    )
    
    def __repr__(self):
        return f"<Skill(name='{self.name}', category='{self.category}')>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "required_tools": self.required_tools,
            "proficiency_levels": self.proficiency_levels,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TeamMember(Base):
    """Team members with skills for task assignment"""
    
    __tablename__ = "team_members"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    supabase_uid: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )  # Supabase user ID for RLS
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    team_role: Mapped[TeamRole] = mapped_column(
        Enum(TeamRole), default=TeamRole.PROCESSOR, nullable=False, index=True
    )
    
    # Workload and availability
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    max_concurrent_tasks: Mapped[int] = mapped_column(Integer, default=3)
    current_workload: Mapped[int] = mapped_column(Integer, default=0)
    workload_score: Mapped[float] = mapped_column(Float, default=0.0)  # Lower is better
    
    # Performance metrics
    completed_tasks_count: Mapped[int] = mapped_column(Integer, default=0)
    average_completion_time: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # in hours
    rating: Mapped[float] = mapped_column(Float, default=5.0)  # 1-5 scale
    
    # Notification preferences
    notification_channels: Mapped[List[str]] = mapped_column(
        ARRAY(String), default=lambda: ["email"]
    )  # ['email', 'slack', 'webhook']
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="team_member")
    skills: Mapped[List["Skill"]] = relationship(
        "Skill", secondary=team_member_skills, back_populates="team_members"
    )
    assigned_tasks: Mapped[List["TaskAssignment"]] = relationship(
        "TaskAssignment", back_populates="assigned_to"
    )
    
    def __repr__(self):
        return f"<TeamMember(name='{self.full_name}', role='{self.team_role.value}')>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "supabase_uid": self.supabase_uid,
            "email": self.email,
            "full_name": self.full_name,
            "team_role": self.team_role.value,
            "is_available": self.is_available,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "current_workload": self.current_workload,
            "workload_score": self.workload_score,
            "completed_tasks_count": self.completed_tasks_count,
            "average_completion_time": self.average_completion_time,
            "rating": self.rating,
            "notification_channels": self.notification_channels,
            "skills": [skill.to_dict() for skill in self.skills],
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def has_skill(self, skill_name: str) -> bool:
        """Check if team member has a specific skill"""
        return any(skill.name == skill_name for skill in self.skills)
    
    def get_skill_proficiency(self, skill_name: str) -> int:
        """Get proficiency level for a skill (0-3)"""
        for skill in self.skills:
            if skill.name == skill_name:
                return skill.proficiency_levels.get("expert", 1)
        return 0
    
    def can_take_more_tasks(self) -> bool:
        """Check if team member can take more tasks"""
        return (
            self.is_available
            and self.current_workload < self.max_concurrent_tasks
            and self.is_active
        )


class TaskWorkflow(Base):
    """Workflow for a file/sermon processing pipeline"""
    
    __tablename__ = "task_workflows"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    workflow_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Related entity
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # 'sermon', 'file', 'batch'
    entity_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Workflow status
    status: Mapped[WorkflowStatus] = mapped_column(
        Enum(WorkflowStatus), default=WorkflowStatus.CREATED, nullable=False, index=True
    )
    priority: Mapped[int] = mapped_column(Integer, default=1)  # 1-5, 5 is highest
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Metadata
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    
    # Relationships
    tasks: Mapped[List["TaskAssignment"]] = relationship(
        "TaskAssignment", back_populates="workflow", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("idx_workflow_entity", "entity_type", "entity_id"),
        Index("idx_workflow_status_created", "status", "created_at"),
    )
    
    def __repr__(self):
        return f"<TaskWorkflow(id='{self.workflow_id}', status='{self.status.value}')>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "status": self.status.value,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "metadata": self.metadata,
            "error_message": self.error_message,
            "task_count": len(self.tasks) if self.tasks else 0,
            "completed_task_count": sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED) if self.tasks else 0,
        }
    
    def get_progress(self) -> dict:
        """Get workflow progress"""
        if not self.tasks:
            return {"total": 0, "completed": 0, "percentage": 0}
        
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        percentage = (completed / total * 100) if total > 0 else 0
        
        return {
            "total": total,
            "completed": completed,
            "percentage": round(percentage, 2),
            "failed": sum(1 for t in self.tasks if t.status == TaskStatus.FAILED),
            "in_progress": sum(1 for t in self.tasks if t.status == TaskStatus.IN_PROGRESS),
            "pending": sum(1 for t in self.tasks if t.status == TaskStatus.PENDING),
        }


class TaskAssignment(Base):
    """Individual task assigned to a team member"""
    
    __tablename__ = "task_assignments"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True, default=lambda: str(uuid.uuid4())
    )
    
    # Related workflow
    workflow_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("task_workflows.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    # Task details
    task_type: Mapped[TaskType] = mapped_column(Enum(TaskType), nullable=False, index=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False, index=True
    )
    priority: Mapped[int] = mapped_column(Integer, default=1)  # 1-5
    
    # Assignment
    assigned_to_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("team_members.id"), nullable=True, index=True
    )
    assigned_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Required skills for this task
    required_skills: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    
    # AI assignment score (0-1)
    ai_assignment_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    assignment_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Task data
    input_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    result_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Retry and error handling
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Celery task tracking
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    
    # Relationships
    workflow: Mapped["TaskWorkflow"] = relationship("TaskWorkflow", back_populates="tasks")
    assigned_to: Mapped[Optional["TeamMember"]] = relationship(
        "TeamMember", back_populates="assigned_tasks"
    )
    
    __table_args__ = (
        Index("idx_task_workflow_type", "workflow_id", "task_type"),
        Index("idx_task_status_assigned", "status", "assigned_to_id"),
        Index("idx_task_celery", "celery_task_id"),
    )
    
    def __repr__(self):
        return f"<TaskAssignment(id='{self.task_id}', type='{self.task_type.value}', status='{self.status.value}')>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "workflow_id": self.workflow_id,
            "task_type": self.task_type.value,
            "status": self.status.value,
            "priority": self.priority,
            "assigned_to": self.assigned_to.to_dict() if self.assigned_to else None,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "required_skills": self.required_skills,
            "ai_assignment_score": self.ai_assignment_score,
            "assignment_reason": self.assignment_reason,
            "input_data": self.input_data,
            "result_data": self.result_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "retry_count": self.retry_count,
            "error_message": self.error_message,
            "celery_task_id": self.celery_task_id,
        }


class TaskAuditLog(Base):
    """Audit log for task assignment events"""
    
    __tablename__ = "task_audit_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_id: Mapped[Optional[str]] = mapped_column(
        String(255), ForeignKey("task_assignments.task_id", ondelete="SET NULL"), nullable=True
    )
    workflow_id: Mapped[Optional[str]] = mapped_column(
        String(255), ForeignKey("task_workflows.workflow_id", ondelete="SET NULL"), nullable=True
    )
    
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # created, assigned, started, completed, failed, reassigned, cancelled
    
    performed_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    performed_by_type: Mapped[str] = mapped_column(
        String(20), default="user"
    )  # 'user', 'system', 'celery'
    
    details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
    
    __table_args__ = (
        Index("idx_audit_task_created", "task_id", "created_at"),
        Index("idx_audit_action_created", "action", "created_at"),
    )
    
    def __repr__(self):
        return f"<TaskAuditLog(action='{self.action}', task='{self.task_id}')>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "workflow_id": self.workflow_id,
            "action": self.action,
            "performed_by": self.performed_by,
            "performed_by_type": self.performed_by_type,
            "details": self.details,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ==================== Default Skills Data ====================

DEFAULT_SKILLS = [
    {
        "name": "whisper_transcription",
        "category": "transcription",
        "description": "Audio transcription using OpenAI Whisper",
        "required_tools": ["whisper", "ffmpeg"],
        "proficiency_levels": {"beginner": 1, "intermediate": 2, "expert": 3},
    },
    {
        "name": "fast_transcription",
        "category": "transcription",
        "description": "Fast typing and manual transcription skills",
        "required_tools": ["typing", "transcription_software"],
        "proficiency_levels": {"beginner": 1, "intermediate": 2, "expert": 3},
    },
    {
        "name": "ffmpeg_video_processing",
        "category": "video",
        "description": "Video processing using FFmpeg",
        "required_tools": ["ffmpeg", "ffprobe"],
        "proficiency_levels": {"beginner": 1, "intermediate": 2, "expert": 3},
    },
    {
        "name": "premiere_video_editing",
        "category": "video",
        "description": "Advanced video editing with Adobe Premiere",
        "required_tools": ["premiere_pro", "media_encoder"],
        "proficiency_levels": {"beginner": 1, "intermediate": 2, "expert": 3},
    },
    {
        "name": "exiftool_metadata",
        "category": "metadata",
        "description": "EXIF/GPS metadata extraction using EXIFTool",
        "required_tools": ["exiftool", "geopy"],
        "proficiency_levels": {"beginner": 1, "intermediate": 2, "expert": 3},
    },
    {
        "name": "gps_location_tagging",
        "category": "metadata",
        "description": "GPS coordinate extraction and geocoding",
        "required_tools": ["gps_extractor", "nominatim"],
        "proficiency_levels": {"beginner": 1, "intermediate": 2, "expert": 3},
    },
    {
        "name": "artwork_design",
        "category": "quality",
        "description": "Graphic design and artwork creation",
        "required_tools": ["photoshop", "illustrator", "canva"],
        "proficiency_levels": {"beginner": 1, "intermediate": 2, "expert": 3},
    },
    {
        "name": "quality_assurance",
        "category": "quality",
        "description": "Quality checks and content review",
        "required_tools": ["qa_checklist", "review_tools"],
        "proficiency_levels": {"beginner": 1, "intermediate": 2, "expert": 3},
    },
    {
        "name": "audio_quality_analysis",
        "category": "quality",
        "description": "Audio quality metrics and optimization",
        "required_tools": ["ffmpeg", "audio_analyzer"],
        "proficiency_levels": {"beginner": 1, "intermediate": 2, "expert": 3},
    },
    {
        "name": "thumbnail_generation",
        "category": "video",
        "description": "Video thumbnail creation and optimization",
        "required_tools": ["ffmpeg", "image_editor"],
        "proficiency_levels": {"beginner": 1, "intermediate": 2, "expert": 3},
    },
    {
        "name": "ai_metadata_extraction",
        "category": "metadata",
        "description": "AI-powered metadata and content analysis",
        "required_tools": ["openai", "llm"],
        "proficiency_levels": {"beginner": 1, "intermediate": 2, "expert": 3},
    },
    {
        "name": "social_media_clip_creation",
        "category": "video",
        "description": "Creating short clips for social media",
        "required_tools": ["ffmpeg", "social_media_tools"],
        "proficiency_levels": {"beginner": 1, "intermediate": 2, "expert": 3},
    },
]


# ==================== Task Type to Skills Mapping ====================

TASK_TYPE_REQUIRED_SKILLS = {
    TaskType.TRANSCRIPTION: ["whisper_transcription", "fast_transcription"],
    TaskType.VIDEO_PROCESSING: ["ffmpeg_video_processing", "premiere_video_editing"],
    TaskType.LOCATION_TAGGING: ["exiftool_metadata", "gps_location_tagging"],
    TaskType.ARTWORK_QUALITY: ["artwork_design", "quality_assurance"],
    TaskType.METADATA_AI: ["ai_metadata_extraction"],
    TaskType.THUMBNAIL_GENERATION: ["thumbnail_generation", "artwork_design"],
    TaskType.SOCIAL_CLIP: ["social_media_clip_creation", "ffmpeg_video_processing"],
    TaskType.DISTRIBUTION: ["social_media_clip_creation"],
}
