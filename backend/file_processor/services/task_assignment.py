"""Task Assignment Service for Skill-Based Task Allocation

This module provides the core logic for:
- Skill-based task assignment to team members
- AI-powered assignment suggestions using OpenAI
- Workflow orchestration and state management
- Task tracking and progress monitoring
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

import openai
from sqlalchemy.orm import Session

from file_processor.core.config import settings
from file_processor.models import (
    TaskType,
    TaskStatus,
    WorkflowStatus,
    TaskWorkflow,
    TaskAssignment,
    TaskAuditLog,
    Skill,
    TeamMember,
    DEFAULT_SKILLS,
    TASK_TYPE_REQUIRED_SKILLS,
)
from file_processor.database import get_db

logger = logging.getLogger(__name__)


class AssignmentAlgorithm(str, Enum):
    """Algorithms available for task assignment"""
    AI_MATCHING = "ai_matching"
    SKILL_MATCH = "skill_match"
    WORKLOAD_BALANCE = "workload_balance"
    RANDOM = "random"
    MANUAL = "manual"


@dataclass
class AssignmentResult:
    """Result of a task assignment process"""
    success: bool
    task_id: Optional[str] = None
    assigned_to_id: Optional[int] = None
    assignment_score: Optional[float] = None
    reason: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        pass


@dataclass
class TeamMemberScore:
    """Score for a team member based on skill match and workload"""
    team_member_id: int
    skill_match_score: float
    workload_score: float
    availability_score: float
    overall_score: float
    required_skills: List[str]
    matching_skills: List[str]
    
    def __repr__(self):
        return (
            f"TeamMemberScore(member={self.team_member_id}, "
            f"skills={self.skill_match_score:.2f}, "
            f"workload={self.workload_score:.2f}, "
            f"availability={self.availability_score:.2f}, "
            f"overall={self.overall_score:.2f})"
        )


class TaskAssignmentService:
    """Service for task assignment and workflow management"""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db or next(get_db())
    
    def get_available_team_members(self, task_type: TaskType) -> List[TeamMember]:
        """Get available team members with required skills for a specific task type"""
        required_skills = TASK_TYPE_REQUIRED_SKILLS.get(task_type, [])
        
        # Query available team members
        query = self.db.query(TeamMember)\
            .filter(TeamMember.is_active == True)\
            .filter(TeamMember.is_available == True)\
            .filter(TeamMember.current_workload < TeamMember.max_concurrent_tasks)
        
        # Filter by required skills
        available_members = []
        for member in query.all():
            if any(skill.name in required_skills for skill in member.skills):
                available_members.append(member)
        
        logger.info(
            f"Found {len(available_members)} available team members "
            f"for task type {task_type.value} with skills {required_skills}"
        )
        
        return available_members
    
    def calculate_member_scores(
        self,
        team_members: List[TeamMember],
        task_type: TaskType
    ) -> List[TeamMemberScore]:
        """Calculate assignment scores for team members based on task requirements"""
        required_skills = TASK_TYPE_REQUIRED_SKILLS.get(task_type, [])
        scores = []
        
        for member in team_members:
            # Skill match score
            matching_skills = [
                skill.name for skill in member.skills 
                if skill.name in required_skills
            ]
            skill_match_score = len(matching_skills) / len(required_skills) if required_skills else 0.0
            
            # Workload score (lower workload = better)
            workload_score = 1 - (member.current_workload / member.max_concurrent_tasks)
            
            # Availability score (adjust for recent activity)
            availability_score = 1.0
            if member.completed_tasks_count > 0 and member.average_completion_time:
                # Adjust for members with very high completion rates
                if member.completed_tasks_count > 100:
                    availability_score *= 0.9
            
            # Overall score with weighted importance
            overall_score = (
                skill_match_score * 0.6 +
                workload_score * 0.25 +
                availability_score * 0.15
            )
            
            scores.append(
                TeamMemberScore(
                    team_member_id=member.id,
                    skill_match_score=skill_match_score,
                    workload_score=workload_score,
                    availability_score=availability_score,
                    overall_score=overall_score,
                    required_skills=required_skills,
                    matching_skills=matching_skills
                )
            )
        
        # Sort by overall score descending
        return sorted(scores, key=lambda x: x.overall_score, reverse=True)
    
    def assign_task(
        self,
        task_id: str,
        task_type: TaskType,
        algorithm: AssignmentAlgorithm = AssignmentAlgorithm.AI_MATCHING,
        assigned_to_id: Optional[int] = None,
        priority: int = 1
    ) -> AssignmentResult:
        """Assign a task to a team member based on selected algorithm"""
        logger.info(
            f"Assigning task {task_id} (type: {task_type.value}) "
            f"using {algorithm.value} algorithm"
        )
        
        try:
            # Find the task
            task = self.db.query(TaskAssignment).filter(
                TaskAssignment.task_id == task_id
            ).first()
            
            if not task:
                return AssignmentResult(
                    success=False,
                    errors=[f"Task {task_id} not found"]
                )
            
            if task.status == TaskStatus.COMPLETED:
                return AssignmentResult(
                    success=False,
                    errors=[f"Task {task_id} is already completed"]
                )
            
            if task.status == TaskStatus.CANCELLED:
                return AssignmentResult(
                    success=False,
                    errors=[f"Task {task_id} has been cancelled"]
                )
            
            # Get available team members
            available_members = self.get_available_team_members(task_type)
            
            if not available_members:
                logger.warning(f"No available team members for task type {task_type.value}")
                return AssignmentResult(
                    success=False,
                    errors=["No available team members with required skills"]
                )
            
            # Manual assignment
            if algorithm == AssignmentAlgorithm.MANUAL and assigned_to_id:
                return self._manual_assignment(task, assigned_to_id)
            
            # AI-based assignment
            if algorithm == AssignmentAlgorithm.AI_MATCHING:
                return self._ai_assignment(task, available_members, task_type)
            
            # Skill-based assignment
            if algorithm == AssignmentAlgorithm.SKILL_MATCH:
                return self._skill_based_assignment(task, available_members, task_type)
            
            # Workload balance assignment
            if algorithm == AssignmentAlgorithm.WORKLOAD_BALANCE:
                return self._workload_balance_assignment(task, available_members)
            
            # Random assignment (fallback)
            return self._random_assignment(task, available_members)
            
        except Exception as e:
            logger.error(f"Task assignment failed: {str(e)}")
            return AssignmentResult(
                success=False,
                errors=[f"Assignment failed: {str(e)}"]
            )
    
    def _ai_assignment(
        self,
        task: TaskAssignment,
        available_members: List[TeamMember],
        task_type: TaskType
    ) -> AssignmentResult:
        """AI-powered task assignment using OpenAI GPT model"""
        required_skills = TASK_TYPE_REQUIRED_SKILLS.get(task_type, [])
        
        try:
            # Prepare team members data
            team_data = []
            for member in available_members:
                skills = [skill.to_dict() for skill in member.skills]
                team_data.append({
                    "id": member.id,
                    "email": member.email,
                    "full_name": member.full_name,
                    "team_role": member.team_role.value,
                    "skills": [skill["name"] for skill in skills],
                    "workload": {
                        "current": member.current_workload,
                        "max": member.max_concurrent_tasks,
                        "score": member.workload_score
                    },
                    "performance": {
                        "completed_tasks": member.completed_tasks_count,
                        "avg_completion_time": member.average_completion_time,
                        "rating": member.rating
                    }
                })
            
            # AI skill matching using GPT
            openai.api_key = settings.openai_api_key
            
            prompt = f"""
            You are an intelligent task assignment assistant for FileForge. Your role is to match tasks to the most suitable team members based on skills, availability, and workload.
            
            Task Details:
            - Task ID: {task.task_id}
            - Task Type: {task_type.value}
            - Required Skills: {', '.join(required_skills)}
            - Priority: {task.priority}
            
            Team Members ({len(team_data)} available):
            {json.dumps(team_data, indent=2, default=str)}
            
            Skills Mapping:
            - transcription: needs 'whisper_transcription', 'fast_transcription'
            - video_processing: needs 'ffmpeg_video_processing', 'premiere_video_editing'
            - location_tagging: needs 'exiftool_metadata', 'gps_location_tagging'
            - artwork_quality: needs 'artwork_design', 'quality_assurance'
            - metadata_ai: needs 'ai_metadata_extraction'
            - thumbnail_generation: needs 'thumbnail_generation', 'artwork_design'
            - social_clip: needs 'social_media_clip_creation', 'ffmpeg_video_processing'
            - distribution: needs 'social_media_clip_creation'
            
            Assignment Criteria (in order of importance):
            1. Skill match score (required skills coverage)
            2. Current workload (lower workload score = better)
            3. Performance history (rating, completion rate)
            4. Role suitability (editor > processor for complex tasks)
            
            Please recommend the best team member for this task and provide a confidence score (0-1).
            Return ONLY valid JSON in this format:
            {{
                "assigned_to_id": <team_member_id>,
                "assignment_score": <confidence_score>,
                "reason": "<detailed_reason_for_assignment>"
            }}
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            assignment = json.loads(response.choices[0].message.content)
            assigned_to_id = assignment["assigned_to_id"]
            assignment_score = assignment["assignment_score"]
            reason = assignment["reason"]
            
            return self._perform_assignment(task, assigned_to_id, assignment_score, reason)
            
        except Exception as e:
            logger.error(f"AI assignment failed, falling back to skill match: {str(e)}")
            return self._skill_based_assignment(task, available_members, task_type)
    
    def _skill_based_assignment(
        self,
        task: TaskAssignment,
        available_members: List[TeamMember],
        task_type: TaskType
    ) -> AssignmentResult:
        """Assign task based on highest skill match score"""
        scores = self.calculate_member_scores(available_members, task_type)
        
        if not scores:
            return AssignmentResult(
                success=False,
                errors=["No available team members with required skills"]
            )
        
        top_score = scores[0]
        reason = (
            f"Best skill match: {len(top_score.matching_skills)} of "
            f"{len(top_score.required_skills)} required skills (score: {top_score.skill_match_score:.2f})"
        )
        
        return self._perform_assignment(
            task, top_score.team_member_id, top_score.overall_score, reason
        )
    
    def _workload_balance_assignment(
        self,
        task: TaskAssignment,
        available_members: List[TeamMember]
    ) -> AssignmentResult:
        """Assign task to team member with lowest current workload"""
        # Sort by current workload ascending
        sorted_members = sorted(
            available_members,
            key=lambda x: x.current_workload
        )
        
        best_member = sorted_members[0]
        reason = (
            f"Lowest workload: {best_member.current_workload}/{best_member.max_concurrent_tasks} "
            f"tasks in progress"
        )
        
        return self._perform_assignment(
            task, best_member.id, 0.8, reason
        )
    
    def _random_assignment(
        self,
        task: TaskAssignment,
        available_members: List[TeamMember]
    ) -> AssignmentResult:
        """Random assignment (fallback)"""
        import random
        
        member = random.choice(available_members)
        reason = "Random assignment (fallback)"
        
        return self._perform_assignment(
            task, member.id, 0.5, reason
        )
    
    def _manual_assignment(
        self,
        task: TaskAssignment,
        assigned_to_id: int
    ) -> AssignmentResult:
        """Manual task assignment"""
        member = self.db.query(TeamMember).filter(
            TeamMember.id == assigned_to_id
        ).first()
        
        if not member:
            return AssignmentResult(
                success=False,
                errors=[f"Team member {assigned_to_id} not found"]
            )
        
        if not member.is_active or not member.is_available:
            return AssignmentResult(
                success=False,
                errors=[f"Team member {assigned_to_id} is not available"]
            )
        
        if member.current_workload >= member.max_concurrent_tasks:
            return AssignmentResult(
                success=False,
                errors=[f"Team member {assigned_to_id} has reached maximum concurrent tasks"]
            )
        
        return self._perform_assignment(
            task, assigned_to_id, 1.0, "Manual assignment"
        )
    
    def _perform_assignment(
        self,
        task: TaskAssignment,
        assigned_to_id: int,
        assignment_score: float,
        reason: str
    ) -> AssignmentResult:
        """Actually perform the assignment in the database"""
        member = self.db.query(TeamMember).filter(
            TeamMember.id == assigned_to_id
        ).first()
        
        if not member:
            return AssignmentResult(
                success=False,
                errors=[f"Team member {assigned_to_id} not found"]
            )
        
        # Update task assignment
        task.assigned_to_id = assigned_to_id
        task.status = TaskStatus.ASSIGNED
        task.assigned_at = datetime.now(timezone.utc)
        task.ai_assignment_score = assignment_score
        task.assignment_reason = reason
        
        # Update team member workload
        member.current_workload += 1
        member.workload_score = member.current_workload / member.max_concurrent_tasks
        
        # Create audit log entry
        audit_log = TaskAuditLog(
            task_id=task.task_id,
            workflow_id=task.workflow.workflow_id if task.workflow else None,
            action="assigned",
            performed_by=None,  # System assignment
            performed_by_type="system",
            details={
                "assigned_to": {
                    "id": member.id,
                    "email": member.email,
                    "full_name": member.full_name
                },
                "assignment_score": assignment_score,
                "reason": reason,
                "algorithm": "ai_matching"
            }
        )
        self.db.add(audit_log)
        
        self.db.commit()
        self.db.refresh(task)
        self.db.refresh(member)
        
        logger.info(
            f"Task {task.task_id} assigned to {member.full_name} "
            f"(score: {assignment_score:.2f}): {reason}"
        )
        
        return AssignmentResult(
            success=True,
            task_id=task.task_id,
            assigned_to_id=assigned_to_id,
            assignment_score=assignment_score,
            reason=reason
        )
    
    def create_workflow(
        self,
        name: str,
        entity_type: str,
        entity_id: str,
        task_types: List[TaskType],
        priority: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
        created_by: Optional[int] = None
    ) -> TaskWorkflow:
        """Create a new task workflow with specified tasks"""
        workflow = TaskWorkflow(
            name=name,
            entity_type=entity_type,
            entity_id=entity_id,
            status=WorkflowStatus.CREATED,
            priority=priority,
            metadata=metadata or {},
            created_by=created_by
        )
        
        # Create task assignments for each task type
        for task_type in task_types:
            task = TaskAssignment(
                task_type=task_type,
                status=TaskStatus.PENDING,
                priority=priority,
                required_skills=TASK_TYPE_REQUIRED_SKILLS.get(task_type, []),
                input_data=metadata or {}
            )
            workflow.tasks.append(task)
        
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)
        
        logger.info(
            f"Created workflow '{name}' (ID: {workflow.workflow_id}) "
            f"with {len(workflow.tasks)} tasks"
        )
        
        return workflow
    
    def start_workflow(self, workflow_id: str) -> bool:
        """Start a workflow and assign tasks to team members"""
        workflow = self.db.query(TaskWorkflow).filter(
            TaskWorkflow.workflow_id == workflow_id
        ).first()
        
        if not workflow:
            logger.error(f"Workflow {workflow_id} not found")
            return False
        
        if workflow.status != WorkflowStatus.CREATED:
            logger.warning(
                f"Workflow {workflow_id} cannot be started - current status: {workflow.status.value}"
            )
            return False
        
        workflow.status = WorkflowStatus.PROCESSING
        workflow.started_at = datetime.now(timezone.utc)
        
        # Assign all pending tasks
        for task in workflow.tasks:
            if task.status == TaskStatus.PENDING:
                result = self.assign_task(
                    task.task_id,
                    task.task_type,
                    AssignmentAlgorithm.AI_MATCHING,
                    priority=workflow.priority
                )
                
                if not result.success:
                    logger.warning(
                        f"Failed to assign task {task.task_id}: {', '.join(result.errors)}"
                    )
        
        self.db.commit()
        self.db.refresh(workflow)
        
        logger.info(f"Workflow {workflow_id} started with {len(workflow.tasks)} tasks")
        return True
    
    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Update task status and optionally result data"""
        task = self.db.query(TaskAssignment).filter(
            TaskAssignment.task_id == task_id
        ).first()
        
        if not task:
            logger.error(f"Task {task_id} not found")
            return False
        
        previous_status = task.status
        task.status = status
        
        if status == TaskStatus.IN_PROGRESS and not task.started_at:
            task.started_at = datetime.now(timezone.utc)
        elif status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now(timezone.utc)
            if result_data:
                task.result_data = result_data
            # Decrement workload if task completes
            if task.assigned_to:
                task.assigned_to.current_workload = max(0, task.assigned_to.current_workload - 1)
                task.assigned_to.workload_score = task.assigned_to.current_workload / task.assigned_to.max_concurrent_tasks
        elif status == TaskStatus.FAILED:
            task.error_message = error_message
            task.retry_count += 1
        elif status == TaskStatus.CANCELLED:
            if task.assigned_to:
                task.assigned_to.current_workload = max(0, task.assigned_to.current_workload - 1)
                task.assigned_to.workload_score = task.assigned_to.current_workload / task.assigned_to.max_concurrent_tasks
        
        # Create audit log entry
        audit_log = TaskAuditLog(
            task_id=task.task_id,
            workflow_id=task.workflow.workflow_id if task.workflow else None,
            action=status.value,
            performed_by=None,
            performed_by_type="system",
            details={
                "previous_status": previous_status.value,
                "new_status": status.value,
                "result_data": result_data,
                "error_message": error_message
            }
        )
        self.db.add(audit_log)
        
        # Update workflow status if all tasks complete
        if task.workflow:
            self._update_workflow_status(task.workflow)
        
        self.db.commit()
        self.db.refresh(task)
        
        logger.info(
            f"Task {task_id} status updated to {status.value}"
        )
        
        return True
    
    def _update_workflow_status(self, workflow: TaskWorkflow):
        """Update workflow status based on task completion"""
        all_completed = all(task.status == TaskStatus.COMPLETED for task in workflow.tasks)
        has_failed = any(task.status == TaskStatus.FAILED for task in workflow.tasks)
        
        if all_completed:
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now(timezone.utc)
        elif has_failed:
            workflow.status = WorkflowStatus.PARTIAL_FAILURE
        elif any(task.status == TaskStatus.IN_PROGRESS for task in workflow.tasks):
            workflow.status = WorkflowStatus.PROCESSING
    
    def get_workflow_progress(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow progress and task statuses"""
        workflow = self.db.query(TaskWorkflow).filter(
            TaskWorkflow.workflow_id == workflow_id
        ).first()
        
        if not workflow:
            return {"error": "Workflow not found"}
        
        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "status": workflow.status.value,
            "created_at": workflow.created_at.isoformat(),
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "priority": workflow.priority,
            "entity": {
                "type": workflow.entity_type,
                "id": workflow.entity_id
            },
            "progress": workflow.get_progress(),
            "tasks": [
                {
                    "task_id": task.task_id,
                    "type": task.task_type.value,
                    "status": task.status.value,
                    "assigned_to": {
                        "id": task.assigned_to.id,
                        "email": task.assigned_to.email,
                        "full_name": task.assigned_to.full_name
                    } if task.assigned_to else None,
                    "assigned_at": task.assigned_at.isoformat() if task.assigned_at else None,
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "result_data": task.result_data
                }
                for task in workflow.tasks
            ]
        }
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """Get task assignment statistics"""
        total_tasks = self.db.query(TaskAssignment).count()
        completed_tasks = self.db.query(TaskAssignment).filter(
            TaskAssignment.status == TaskStatus.COMPLETED
        ).count()
        in_progress = self.db.query(TaskAssignment).filter(
            TaskAssignment.status == TaskStatus.IN_PROGRESS
        ).count()
        pending = self.db.query(TaskAssignment).filter(
            TaskAssignment.status == TaskStatus.PENDING
        ).count()
        failed = self.db.query(TaskAssignment).filter(
            TaskAssignment.status == TaskStatus.FAILED
        ).count()
        
        by_type = {}
        for task_type in TaskType:
            count = self.db.query(TaskAssignment).filter(
                TaskAssignment.task_type == task_type
            ).count()
            by_type[task_type.value] = count
        
        by_assignee = {}
        results = self.db.query(
            TeamMember.id,
            TeamMember.full_name,
            TeamMember.email,
            TeamMember.team_role,
            TeamMember.current_workload,
            TeamMember.max_concurrent_tasks
        ).all()
        
        for member in results:
            assigned_tasks = self.db.query(TaskAssignment).filter(
                TaskAssignment.assigned_to_id == member.id
            ).count()
            
            completed_tasks_by_member = self.db.query(TaskAssignment).filter(
                TaskAssignment.assigned_to_id == member.id,
                TaskAssignment.status == TaskStatus.COMPLETED
            ).count()
            
            by_assignee[member.id] = {
                "full_name": member.full_name,
                "email": member.email,
                "role": member.team_role.value,
                "assigned_tasks": assigned_tasks,
                "completed_tasks": completed_tasks_by_member,
                "current_workload": member.current_workload,
                "max_concurrent_tasks": member.max_concurrent_tasks,
                "completion_rate": (
                    completed_tasks_by_member / assigned_tasks if assigned_tasks > 0 else 0
                )
            }
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress": in_progress,
            "pending": pending,
            "failed": failed,
            "by_type": by_type,
            "by_assignee": by_assignee,
            "completion_rate": (
                completed_tasks / total_tasks if total_tasks > 0 else 0
            )
        }
    
    def initialize_default_skills(self):
        """Initialize default skills if not already present"""
        existing_skills = {s.name for s in self.db.query(Skill).all()}
        
        for skill in DEFAULT_SKILLS:
            if skill["name"] not in existing_skills:
                try:
                    new_skill = Skill(**skill)
                    self.db.add(new_skill)
                    logger.info(f"Created default skill: {skill['name']}")
                except Exception as e:
                    logger.error(f"Failed to create default skill {skill['name']}: {str(e)}")
        
        self.db.commit()
