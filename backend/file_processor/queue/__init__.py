"""Celery Task Queue Module

This module initializes the Celery application and imports all tasks.
"""

import logging

from celery import Celery

from file_processor.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Celery app
app = Celery(
    "file_processor",
    broker=settings.redis_url,
    backend=f"{settings.redis_url}/1"
)

# Celery configuration
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour per task
    task_soft_time_limit=3300,  # Soft limit at 55 minutes
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=86400,  # Results expire in 24 hours
)

# Note: Tasks are imported lazily when needed to avoid circular imports
# To use tasks, import them directly from their modules:
# from file_processor.queue.backup_tasks import backup_to_offline_storage
# from file_processor.queue.task_assignment_tasks import orchestrate_task_workflow

__all__ = ["app"]
