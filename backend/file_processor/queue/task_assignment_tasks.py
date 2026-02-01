"""Celery Tasks for Task Assignment Workflow Orchestration

This module implements the Celery task queue operations for:
- Automatic task assignment
- Workflow execution
- Task processing
- Results collection and workflow completion
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path

from celery import chord, group
from file_processor.models import (
    TaskType,
    TaskStatus,
    WorkflowStatus,
    TaskWorkflow,
    TaskAssignment,
    TASK_TYPE_REQUIRED_SKILLS,
)
from file_processor.services.task_assignment import (
    TaskAssignmentService,
    AssignmentAlgorithm,
)
from file_processor.database import get_db

logger = logging.getLogger(__name__)

# Use the shared Celery app instance
from file_processor.queue import app


# ==================== Workflow Orchestration ====================

@app.task(bind=True, max_retries=3, default_retry_delay=60)
def orchestrate_task_workflow(self, workflow_id: str, uploaded_files: List[str], church_id: Optional[str] = None):
    """Master orchestrator for task assignment and processing pipeline"""
    logger.info(f"Starting task assignment workflow: {workflow_id}")
    
    try:
        db = next(get_db())
        assignment_service = TaskAssignmentService(db)
        
        # Get workflow
        workflow = db.query(TaskWorkflow).filter(TaskWorkflow.workflow_id == workflow_id).first()
        if not workflow:
            raise Exception(f"Workflow {workflow_id} not found")
        
        # Update workflow status
        workflow.status = WorkflowStatus.INTAKE
        db.commit()
        db.refresh(workflow)
        
        # Determine required task types based on uploaded files
        task_types = [TaskType.TRANSCRIPTION, TaskType.LOCATION_TAGGING]
        
        has_video = any(Path(f).suffix.lower() in [".mp4", ".mov", ".mkv"] for f in uploaded_files)
        has_audio = any(Path(f).suffix.lower() in [".mp3", ".wav", ".flac"] for f in uploaded_files)
        has_images = any(Path(f).suffix.lower() in [".jpg", ".jpeg", ".png"] for f in uploaded_files)
        
        if has_video or has_audio:
            task_types.append(TaskType.VIDEO_PROCESSING)
        
        if has_images:
            task_types.append(TaskType.ARTWORK_QUALITY)
        
        # Create task assignments
        for task_type in task_types:
            task = TaskAssignment(
                task_type=task_type,
                status=TaskStatus.PENDING,
                priority=workflow.priority,
                required_skills=TASK_TYPE_REQUIRED_SKILLS.get(task_type, []),
                input_data={
                    "uploaded_files": uploaded_files,
                    "church_id": church_id,
                    "workflow_id": workflow_id
                }
            )
            workflow.tasks.append(task)
        
        db.commit()
        db.refresh(workflow)
        
        # Assign tasks to team members
        task_ids = []
        for task in workflow.tasks:
            assignment_result = assignment_service.assign_task(
                task.task_id,
                task.task_type,
                AssignmentAlgorithm.AI_MATCHING,
                priority=workflow.priority
            )
            
            if assignment_result.success:
                task_ids.append(task.task_id)
                logger.info(f"Task {task.task_id} assigned to {assignment_result.assigned_to_id}")
            else:
                logger.warning(
                    f"Failed to assign task {task.task_id}: {', '.join(assignment_result.errors)}"
                )
        
        # Dispatch parallel processing tasks
        workflow_tasks = []
        
        for task in workflow.tasks:
            if task.status == TaskStatus.ASSIGNED:
                # Map task type to Celery task
                task_map = {
                    TaskType.TRANSCRIPTION: transcribe_task,
                    TaskType.VIDEO_PROCESSING: process_video_task,
                    TaskType.LOCATION_TAGGING: extract_location_task,
                    TaskType.ARTWORK_QUALITY: quality_check_task,
                    TaskType.METADATA_AI: analyze_metadata_task,
                    TaskType.THUMBNAIL_GENERATION: generate_thumbnails_task,
                    TaskType.SOCIAL_CLIP: create_social_clips_task,
                }
                
                if task.task_type in task_map:
                    celery_task = task_map[task.task_type].delay(
                        task.task_id,
                        task.assigned_to_id,
                        task.input_data
                    )
                    task.celery_task_id = celery_task.id
                    workflow_tasks.append(celery_task.id)
        
        db.commit()
        
        # Update workflow status
        workflow.status = WorkflowStatus.PROCESSING
        db.commit()
        
        # Finalize when all tasks complete
        finalize_task = chord(group(workflow_tasks))(
            finalize_workflow.s(workflow_id)
        )
        
        return {
            "workflow_id": workflow_id,
            "tasks_created": len(workflow.tasks),
            "tasks_assigned": len(task_ids),
            "workflow_tasks": workflow_tasks,
            "status": "workflow_started"
        }
        
    except Exception as e:
        logger.error(f"Workflow orchestration failed: {e}")
        
        # Update workflow status
        try:
            db = next(get_db())
            workflow = db.query(TaskWorkflow).filter(TaskWorkflow.workflow_id == workflow_id).first()
            if workflow:
                workflow.status = WorkflowStatus.FAILED
                workflow.error_message = str(e)
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update workflow status: {db_error}")
        
        raise self.retry(exc=e)


# ==================== Task Processing Workers ====================

@app.task(bind=True, max_retries=3)
def transcribe_task(self, task_id: str, assigned_to_id: int, input_data: Dict[str, Any]):
    """Whisper AI transcription task"""
    logger.info(f"Starting transcription task: {task_id}")
    
    try:
        db = next(get_db())
        assignment_service = TaskAssignmentService(db)
        
        # Update task status
        assignment_service.update_task_status(
            task_id, TaskStatus.IN_PROGRESS
        )
        
        # Get task details
        task = db.query(TaskAssignment).filter(TaskAssignment.task_id == task_id).first()
        
        # Perform transcription (using existing implementation)
        from backend.celery_tasks.sermon_workflow import transcribe_sermon
        
        result = transcribe_sermon(
            task.workflow.entity_id if task.workflow else task_id,
            None
        )
        
        # Update task status
        assignment_service.update_task_status(
            task_id,
            TaskStatus.COMPLETED,
            result_data=result
        )
        
        return {
            "status": "completed",
            "task_id": task_id,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Transcription task failed: {e}")
        _handle_task_failure(task_id, "transcription", e, self.request.retries)
        raise self.retry(exc=e)


@app.task(bind=True, max_retries=3)
def process_video_task(self, task_id: str, assigned_to_id: int, input_data: Dict[str, Any]):
    """FFmpeg video processing task"""
    logger.info(f"Starting video processing task: {task_id}")
    
    try:
        db = next(get_db())
        assignment_service = TaskAssignmentService(db)
        
        # Update task status
        assignment_service.update_task_status(
            task_id, TaskStatus.IN_PROGRESS
        )
        
        # Get task details
        task = db.query(TaskAssignment).filter(TaskAssignment.task_id == task_id).first()
        
        # Perform video processing (using existing implementation)
        from backend.celery_tasks.sermon_workflow import process_video
        
        result = process_video(
            task.workflow.entity_id if task.workflow else task_id,
            None
        )
        
        # Update task status
        assignment_service.update_task_status(
            task_id,
            TaskStatus.COMPLETED,
            result_data=result
        )
        
        return {
            "status": "completed",
            "task_id": task_id,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Video processing task failed: {e}")
        _handle_task_failure(task_id, "video_processing", e, self.request.retries)
        raise self.retry(exc=e)


@app.task(bind=True, max_retries=3)
def extract_location_task(self, task_id: str, assigned_to_id: int, input_data: Dict[str, Any]):
    """EXIFTool location tagging task"""
    logger.info(f"Starting location tagging task: {task_id}")
    
    try:
        db = next(get_db())
        assignment_service = TaskAssignmentService(db)
        
        # Update task status
        assignment_service.update_task_status(
            task_id, TaskStatus.IN_PROGRESS
        )
        
        # Get task details
        task = db.query(TaskAssignment).filter(TaskAssignment.task_id == task_id).first()
        
        # Perform location extraction (using existing implementation)
        from backend.celery_tasks.sermon_workflow import extract_gps_location
        
        result = extract_gps_location(
            task.workflow.entity_id if task.workflow else task_id,
            None
        )
        
        # Update task status
        assignment_service.update_task_status(
            task_id,
            TaskStatus.COMPLETED,
            result_data=result
        )
        
        return {
            "status": "completed",
            "task_id": task_id,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Location tagging task failed: {e}")
        _handle_task_failure(task_id, "location_tagging", e, self.request.retries)
        raise self.retry(exc=e)


@app.task(bind=True, max_retries=2)
def quality_check_task(self, task_id: str, assigned_to_id: int, input_data: Dict[str, Any]):
    """Artwork and quality check task"""
    logger.info(f"Starting quality check task: {task_id}")
    
    try:
        db = next(get_db())
        assignment_service = TaskAssignmentService(db)
        
        # Update task status
        assignment_service.update_task_status(
            task_id, TaskStatus.IN_PROGRESS
        )
        
        # Perform quality checks (placeholder implementation)
        uploaded_files = input_data.get("uploaded_files", [])
        quality_results = []
        
        for file_path in uploaded_files:
            file_result = {
                "file_path": file_path,
                "file_type": Path(file_path).suffix.lower().strip("."),
                "checks": [],
                "warnings": [],
                "errors": []
            }
            
            # Basic file size check
            if Path(file_path).stat().st_size > 100 * 1024 * 1024:  # > 100MB
                file_result["warnings"].append("File size exceeds recommended limit")
            
            # Image quality check
            if file_result["file_type"] in ["jpg", "jpeg", "png"]:
                try:
                    from PIL import Image
                    with Image.open(file_path) as img:
                        width, height = img.size
                        if width < 1000 or height < 1000:
                            file_result["warnings"].append("Image resolution may be too low")
                except Exception as e:
                    file_result["errors"].append(f"Failed to check image quality: {e}")
            
            quality_results.append(file_result)
        
        # Update task status
        assignment_service.update_task_status(
            task_id,
            TaskStatus.COMPLETED,
            result_data={
                "quality_checks": quality_results,
                "summary": {
                    "total_files": len(uploaded_files),
                    "pass": sum(1 for res in quality_results if not res["errors"]),
                    "fail": sum(1 for res in quality_results if res["errors"]),
                    "warnings": sum(len(res["warnings"]) for res in quality_results)
                }
            }
        )
        
        return {
            "status": "completed",
            "task_id": task_id,
            "result": quality_results
        }
        
    except Exception as e:
        logger.error(f"Quality check task failed: {e}")
        _handle_task_failure(task_id, "artwork_quality", e, self.request.retries)
        raise self.retry(exc=e)


@app.task(bind=True, max_retries=3)
def analyze_metadata_task(self, task_id: str, assigned_to_id: int, input_data: Dict[str, Any]):
    """AI metadata extraction task"""
    logger.info(f"Starting metadata analysis task: {task_id}")
    
    try:
        db = next(get_db())
        assignment_service = TaskAssignmentService(db)
        
        # Update task status
        assignment_service.update_task_status(
            task_id, TaskStatus.IN_PROGRESS
        )
        
        # Get task details
        task = db.query(TaskAssignment).filter(TaskAssignment.task_id == task_id).first()
        
        # Perform metadata analysis (using existing implementation)
        from backend.celery_tasks.sermon_workflow import analyze_sermon_metadata
        
        result = analyze_sermon_metadata(
            task.workflow.entity_id if task.workflow else task_id,
            None
        )
        
        # Update task status
        assignment_service.update_task_status(
            task_id,
            TaskStatus.COMPLETED,
            result_data=result
        )
        
        return {
            "status": "completed",
            "task_id": task_id,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Metadata analysis task failed: {e}")
        _handle_task_failure(task_id, "metadata_ai", e, self.request.retries)
        raise self.retry(exc=e)


@app.task(bind=True, max_retries=3)
def generate_thumbnails_task(self, task_id: str, assigned_to_id: int, input_data: Dict[str, Any]):
    """Thumbnail generation task"""
    logger.info(f"Starting thumbnail generation task: {task_id}")
    
    try:
        db = next(get_db())
        assignment_service = TaskAssignmentService(db)
        
        # Update task status
        assignment_service.update_task_status(
            task_id, TaskStatus.IN_PROGRESS
        )
        
        # Get task details
        task = db.query(TaskAssignment).filter(TaskAssignment.task_id == task_id).first()
        
        # Perform thumbnail generation (using existing implementation)
        from backend.celery_tasks.sermon_workflow import generate_thumbnails
        
        result = generate_thumbnails(
            task.workflow.entity_id if task.workflow else task_id,
            None
        )
        
        # Update task status
        assignment_service.update_task_status(
            task_id,
            TaskStatus.COMPLETED,
            result_data=result
        )
        
        return {
            "status": "completed",
            "task_id": task_id,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Thumbnail generation task failed: {e}")
        _handle_task_failure(task_id, "thumbnail_generation", e, self.request.retries)
        raise self.retry(exc=e)


@app.task(bind=True, max_retries=3)
def create_social_clips_task(self, task_id: str, assigned_to_id: int, input_data: Dict[str, Any]):
    """Social media clip creation task"""
    logger.info(f"Starting social clip creation task: {task_id}")
    
    try:
        db = next(get_db())
        assignment_service = TaskAssignmentService(db)
        
        # Update task status
        assignment_service.update_task_status(
            task_id, TaskStatus.IN_PROGRESS
        )
        
        # Get task details
        task = db.query(TaskAssignment).filter(TaskAssignment.task_id == task_id).first()
        
        # Perform social clip creation (using existing implementation)
        from backend.celery_tasks.sermon_workflow import create_social_clips
        
        result = create_social_clips(
            task.workflow.entity_id if task.workflow else task_id,
            None
        )
        
        # Update task status
        assignment_service.update_task_status(
            task_id,
            TaskStatus.COMPLETED,
            result_data=result
        )
        
        return {
            "status": "completed",
            "task_id": task_id,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Social clip creation task failed: {e}")
        _handle_task_failure(task_id, "social_clip", e, self.request.retries)
        raise self.retry(exc=e)


# ==================== Finalization ====================

@app.task(bind=True)
def finalize_workflow(self, results: List[Dict], workflow_id: str):
    """Finalize workflow when all tasks complete"""
    logger.info(f"Finalizing workflow: {workflow_id}")
    
    try:
        db = next(get_db())
        assignment_service = TaskAssignmentService(db)
        
        workflow = db.query(TaskWorkflow).filter(TaskWorkflow.workflow_id == workflow_id).first()
        if not workflow:
            raise Exception(f"Workflow {workflow_id} not found")
        
        # Check all task statuses
        tasks = workflow.tasks
        statuses = [task.status for task in tasks]
        
        if all(status == TaskStatus.COMPLETED for status in statuses):
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now(timezone.utc)
            logger.info(f"Workflow {workflow_id} completed successfully")
        elif any(status == TaskStatus.FAILED for status in statuses):
            workflow.status = WorkflowStatus.PARTIAL_FAILURE
            logger.warning(f"Workflow {workflow_id} completed with partial failure")
        else:
            workflow.status = WorkflowStatus.PROCESSING
            logger.warning(f"Workflow {workflow_id} still processing")
        
        db.commit()
        db.refresh(workflow)
        
        return {
            "workflow_id": workflow_id,
            "status": workflow.status.value,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "tasks_completed": sum(1 for task in tasks if task.status == TaskStatus.COMPLETED),
            "tasks_failed": sum(1 for task in tasks if task.status == TaskStatus.FAILED)
        }
        
    except Exception as e:
        logger.error(f"Workflow finalization failed: {e}")
        
        try:
            db = next(get_db())
            workflow = db.query(TaskWorkflow).filter(TaskWorkflow.workflow_id == workflow_id).first()
            if workflow:
                workflow.status = WorkflowStatus.FAILED
                workflow.error_message = str(e)
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update workflow status: {db_error}")
        
        raise


# ==================== Helper Functions ====================

def _handle_task_failure(task_id: str, task_type: str, error: Exception, retry_count: int):
    """Handle task failure with retry logic"""
    try:
        db = next(get_db())
        assignment_service = TaskAssignmentService(db)
        
        task = db.query(TaskAssignment).filter(TaskAssignment.task_id == task_id).first()
        
        if task:
            max_retries = 3
            new_status = TaskStatus.PENDING if retry_count < max_retries else TaskStatus.FAILED
            
            assignment_service.update_task_status(
                task_id,
                new_status,
                error_message=str(error)
            )
            
            logger.warning(
                f"Task {task_id} failed (retry {retry_count}/{max_retries}): {str(error)}"
            )
            
    except Exception as e:
        logger.error(f"Failed to handle task failure: {e}")


@app.task
def cleanup_stale_tasks():
    """Mark tasks stuck in 'in_progress' for too long as pending"""
    logger.info("Cleaning up stale tasks")
    
    try:
        db = next(get_db())
        
        # Tasks in progress for more than 2 hours
        cutoff = datetime.now(timezone.utc) - timezone.timedelta(hours=2)
        
        stale_tasks = db.query(TaskAssignment).filter(
            TaskAssignment.status == TaskStatus.IN_PROGRESS,
            TaskAssignment.started_at < cutoff
        ).all()
        
        assignment_service = TaskAssignmentService(db)
        
        for task in stale_tasks:
            assignment_service.update_task_status(
                task.task_id,
                TaskStatus.PENDING
            )
            logger.info(f"Marked task {task.task_id} as pending (stale)")
        
    except Exception as e:
        logger.error(f"Failed to clean up stale tasks: {e}")


@app.task
def retry_failed_tasks():
    """Retry tasks that failed with retryable errors"""
    logger.info("Retrying failed tasks")
    
    try:
        db = next(get_db())
        
        failed_tasks = db.query(TaskAssignment).filter(
            TaskAssignment.status == TaskStatus.FAILED,
            TaskAssignment.retry_count <= 2
        ).all()
        
        task_map = {
            TaskType.TRANSCRIPTION: transcribe_task,
            TaskType.VIDEO_PROCESSING: process_video_task,
            TaskType.LOCATION_TAGGING: extract_location_task,
            TaskType.ARTWORK_QUALITY: quality_check_task,
            TaskType.METADATA_AI: analyze_metadata_task,
            TaskType.THUMBNAIL_GENERATION: generate_thumbnails_task,
            TaskType.SOCIAL_CLIP: create_social_clips_task,
        }
        
        assignment_service = TaskAssignmentService(db)
        
        for task in failed_tasks:
            if task.task_type in task_map:
                # Re-queue task
                celery_task = task_map[task.task_type].delay(
                    task.task_id,
                    task.assigned_to_id,
                    task.input_data
                )
                
                task.celery_task_id = celery_task.id
                assignment_service.update_task_status(
                    task.task_id,
                    TaskStatus.PENDING,
                    result_data={"retry_count": task.retry_count + 1}
                )
                
                logger.info(f"Retried task {task.task_id} (retry {task.retry_count + 1})")
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Failed to retry failed tasks: {e}")


@app.task
def monitor_workflow_progress():
    """Monitor workflow progress and update statuses"""
    logger.info("Monitoring workflow progress")
    
    try:
        db = next(get_db())
        
        # Check workflows in progress
        active_workflows = db.query(TaskWorkflow).filter(
            TaskWorkflow.status == WorkflowStatus.PROCESSING
        ).all()
        
        assignment_service = TaskAssignmentService(db)
        
        for workflow in active_workflows:
            all_completed = all(task.status == TaskStatus.COMPLETED for task in workflow.tasks)
            has_failed = any(task.status == TaskStatus.FAILED for task in workflow.tasks)
            
            if all_completed:
                workflow.status = WorkflowStatus.COMPLETED
                workflow.completed_at = datetime.now(timezone.utc)
                logger.info(f"Workflow {workflow.workflow_id} completed successfully")
            elif has_failed:
                workflow.status = WorkflowStatus.PARTIAL_FAILURE
                logger.warning(f"Workflow {workflow.workflow_id} has failed tasks")
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Failed to monitor workflow progress: {e}")


# ==================== Beat Schedule ====================

app.conf.beat_schedule = {
    "cleanup-stale-tasks": {
        "task": "backend.file_processor.queue.task_assignment_tasks.cleanup_stale_tasks",
        "schedule": 300.0,  # Every 5 minutes
    },
    "retry-failed-tasks": {
        "task": "backend.file_processor.queue.task_assignment_tasks.retry_failed_tasks",
        "schedule": 600.0,  # Every 10 minutes
    },
    "monitor-workflow-progress": {
        "task": "backend.file_processor.queue.task_assignment_tasks.monitor_workflow_progress",
        "schedule": 1800.0,  # Every 30 minutes
    },
}
