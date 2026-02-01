"""Task Assignment API Endpoints

This module provides API endpoints for managing task assignments, workflows, and team members.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.file_processor.core.dependencies import get_db
from backend.file_processor.core.rbac_security import require_permission
from backend.file_processor.models import (
    TaskType,
    TaskStatus,
    WorkflowStatus,
    AssignmentAlgorithm,
    TeamMember,
    TaskWorkflow,
    TaskAssignment,
)
from backend.file_processor.services.task_assignment import TaskAssignmentService, AssignmentAlgorithm
from backend.file_processor.schemas.user import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


# ==================== Workflow Management ====================

@router.post("/workflows", dependencies=[Depends(require_permission("workflows:create"))])
def create_workflow(
    name: str,
    entity_type: str = "file",
    entity_id: Optional[str] = None,
    task_types: List[TaskType] = Query(...),
    priority: int = 1,
    metadata: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Create a new task workflow with specified tasks"""
    try:
        service = TaskAssignmentService(db)
        
        workflow = service.create_workflow(
            name=name,
            entity_type=entity_type,
            entity_id=entity_id or str(uuid4()),
            task_types=task_types,
            priority=priority,
            metadata=metadata,
            created_by=current_user.id,
        )
        
        return {
            "success": True,
            "data": workflow.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")


@router.post("/workflows/{workflow_id}/start", dependencies=[Depends(require_permission("workflows:execute"))])
def start_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Start a task workflow and assign tasks to team members"""
    try:
        service = TaskAssignmentService(db)
        
        success = service.start_workflow(workflow_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Workflow not found or cannot be started")
        
        # Get updated workflow
        workflow = db.query(TaskWorkflow).filter(TaskWorkflow.workflow_id == workflow_id).first()
        
        return {
            "success": True,
            "data": workflow.to_dict()
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to start workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")


@router.get("/workflows/{workflow_id}", dependencies=[Depends(require_permission("workflows:view"))])
def get_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get workflow details with progress information"""
    try:
        service = TaskAssignmentService(db)
        progress = service.get_workflow_progress(workflow_id)
        
        if "error" in progress:
            raise HTTPException(status_code=404, detail=progress["error"])
        
        return {
            "success": True,
            "data": progress
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to get workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow: {str(e)}")


@router.get("/workflows", dependencies=[Depends(require_permission("workflows:view"))])
def list_workflows(
    status: Optional[WorkflowStatus] = None,
    entity_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """List all task workflows (with optional filters)"""
    try:
        query = db.query(TaskWorkflow)
        
        if status:
            query = query.filter(TaskWorkflow.status == status)
            
        if entity_type:
            query = query.filter(TaskWorkflow.entity_type == entity_type)
            
        workflows = query.offset(offset).limit(limit).all()
        
        return {
            "success": True,
            "data": [workflow.to_dict() for workflow in workflows],
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": query.count(),
            },
        }
        
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list workflows: {str(e)}")


# ==================== Task Assignment ====================

@router.post("/{task_id}/assign", dependencies=[Depends(require_permission("tasks:assign"))])
def assign_task(
    task_id: str,
    assigned_to_id: Optional[int] = None,
    algorithm: AssignmentAlgorithm = AssignmentAlgorithm.AI_MATCHING,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Assign a task to a team member using specified algorithm"""
    try:
        service = TaskAssignmentService(db)
        
        result = service.assign_task(
            task_id=task_id,
            task_type=None,  # Will be retrieved from task
            algorithm=algorithm,
            assigned_to_id=assigned_to_id,
        )
        
        if not result.success:
            raise HTTPException(status_code=400, detail="; ".join(result.errors))
        
        return {
            "success": True,
            "data": {
                "task_id": result.task_id,
                "assigned_to_id": result.assigned_to_id,
                "assignment_score": result.assignment_score,
                "reason": result.reason,
            },
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to assign task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to assign task: {str(e)}")


@router.put("/{task_id}/status", dependencies=[Depends(require_permission("tasks:update"))])
def update_task_status(
    task_id: str,
    status: TaskStatus,
    result_data: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Update task status with optional result data or error message"""
    try:
        service = TaskAssignmentService(db)
        
        success = service.update_task_status(
            task_id=task_id,
            status=status,
            result_data=result_data,
            error_message=error_message,
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {"success": True}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to update task status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update task status: {str(e)}")


@router.get("/{task_id}", dependencies=[Depends(require_permission("tasks:view"))])
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get task details including assignment information"""
    try:
        task = db.query(TaskAssignment).filter(TaskAssignment.task_id == task_id).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "success": True,
            "data": task.to_dict(),
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to get task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task: {str(e)}")


@router.get("/", dependencies=[Depends(require_permission("tasks:view"))])
def list_tasks(
    status: Optional[TaskStatus] = None,
    task_type: Optional[TaskType] = None,
    assigned_to_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """List all tasks with optional filters for status, type, or assignee"""
    try:
        query = db.query(TaskAssignment)
        
        if status:
            query = query.filter(TaskAssignment.status == status)
            
        if task_type:
            query = query.filter(TaskAssignment.task_type == task_type)
            
        if assigned_to_id:
            query = query.filter(TaskAssignment.assigned_to_id == assigned_to_id)
            
        tasks = query.offset(offset).limit(limit).all()
        
        return {
            "success": True,
            "data": [task.to_dict() for task in tasks],
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": query.count(),
            },
        }
        
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")


# ==================== Team Members ====================

@router.get("/team/members", dependencies=[Depends(require_permission("team:view"))])
def list_team_members(
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """List all team members with optional filters for role and active status"""
    try:
        query = db.query(TeamMember)
        
        if role:
            query = query.filter(TeamMember.team_role == role)
            
        if is_active is not None:
            query = query.filter(TeamMember.is_active == is_active)
            
        members = query.offset(offset).limit(limit).all()
        
        return {
            "success": True,
            "data": [member.to_dict() for member in members],
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": query.count(),
            },
        }
        
    except Exception as e:
        logger.error(f"Failed to list team members: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list team members: {str(e)}")


@router.get("/team/members/{member_id}", dependencies=[Depends(require_permission("team:view"))])
def get_team_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get team member details including skills and assigned tasks"""
    try:
        member = db.query(TeamMember).filter(TeamMember.id == member_id).first()
        
        if not member:
            raise HTTPException(status_code=404, detail="Team member not found")
        
        return {
            "success": True,
            "data": member.to_dict(),
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to get team member: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get team member: {str(e)}")


# ==================== Statistics ====================

@router.get("/statistics", dependencies=[Depends(require_permission("tasks:view_all"))])
def get_task_statistics(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get task assignment statistics including completion rates and workload distribution"""
    try:
        service = TaskAssignmentService(db)
        stats = service.get_task_statistics()
        
        return {
            "success": True,
            "data": stats,
        }
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


# ==================== Celery Orchestration ====================

@router.post("/orchestrate", dependencies=[Depends(require_permission("workflows:execute"))])
def orchestrate_workflow(
    uploaded_files: List[str],
    church_id: Optional[str] = None,
    name: str = "File Processing Workflow",
    entity_type: str = "file",
    entity_id: Optional[str] = None,
    priority: int = 1,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Orchestrate a complete task workflow for uploaded files"""
    try:
        # Import here to avoid circular imports
        from backend.file_processor.queue.task_assignment_tasks import orchestrate_task_workflow
        
        # Create workflow first
        service = TaskAssignmentService(db)
        workflow = service.create_workflow(
            name=name,
            entity_type=entity_type,
            entity_id=entity_id or str(uuid4()),
            task_types=[],  # Task types will be determined by uploaded files in Celery task
            priority=priority,
            metadata={"uploaded_files": uploaded_files, "church_id": church_id},
            created_by=current_user.id,
        )
        
        # Start Celery orchestration
        result = orchestrate_task_workflow.delay(
            workflow_id=workflow.workflow_id,
            uploaded_files=uploaded_files,
            church_id=church_id,
        )
        
        return {
            "success": True,
            "data": {
                "workflow_id": workflow.workflow_id,
                "celery_task_id": result.id,
            },
        }
        
    except Exception as e:
        logger.error(f"Failed to orchestrate workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to orchestrate workflow: {str(e)}")
