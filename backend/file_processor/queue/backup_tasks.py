"""Celery Tasks for Offline Storage Backup

This module contains Celery tasks for managing Backblaze B2 offline storage backup
operations, including post-processing sync and disaster recovery.
"""

import logging
import os
from typing import Dict, Any

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

from file_processor.services.offline_backup import OfflineBackupService

logger = logging.getLogger(__name__)

# Initialize backup service
backup_service = OfflineBackupService()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def backup_to_offline_storage(self, local_path: str, supabase_path: str) -> Dict[str, Any]:
    """Sync optimized files to Backblaze B2 with unlimited retention and versioning.

    This task creates a cold storage backup of processed files, ensuring
    unlimited retention through B2 versioning with soft delete support.

    Args:
        local_path: Path to the local optimized file
        supabase_path: Corresponding Supabase storage path

    Returns:
        Dictionary with backup result
    """
    try:
        logger.info(f"Starting backup to B2: {local_path} -> {supabase_path}")

        # Validate input paths
        if not local_path or not supabase_path:
            logger.error("Invalid backup paths")
            return {"success": False, "error": "Invalid paths"}

        # Perform backup
        result = backup_service.sync_to_b2(local_path, supabase_path)

        if result.get("success"):
            logger.info(f"Backup completed successfully: {result.get('remote_path')}")
        else:
            logger.error(f"Backup failed: {result.get('error')}")

        return result

    except Exception as e:
        logger.error(f"Backup task failed: {e}")

        # Retry task if it fails
        try:
            self.retry(exc=e, countdown=60)
        except MaxRetriesExceededError:
            logger.error("Max backup retries exceeded")
            return {
                "success": False,
                "error": "Max backup retries exceeded",
                "original_error": str(e),
            }


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def restore_from_offline_storage(self, supabase_path: str, local_path: str) -> Dict[str, Any]:
    """Restore file from Backblaze B2 to local storage.

    This task handles disaster recovery scenarios, restoring files from
    cold storage backup to active storage.

    Args:
        supabase_path: Path in Supabase storage to restore
        local_path: Local path to restore the file

    Returns:
        Dictionary with restore result
    """
    try:
        logger.info(f"Starting restore from B2: {supabase_path} -> {local_path}")

        result = backup_service.restore_from_b2(supabase_path, local_path)

        if result.get("success"):
            logger.info(f"Restore completed successfully: {result.get('local_path')}")
        else:
            logger.error(f"Restore failed: {result.get('error')}")

        return result

    except Exception as e:
        logger.error(f"Restore task failed: {e}")

        try:
            self.retry(exc=e, countdown=120)
        except MaxRetriesExceededError:
            logger.error("Max restore retries exceeded")
            return {
                "success": False,
                "error": "Max restore retries exceeded",
                "original_error": str(e),
            }


@shared_task
def cleanup_old_versions(supabase_path: str, keep_versions: int = 3) -> Dict[str, Any]:
    """Clean up old file versions in B2 storage.

    This task manages versioning by soft deleting old versions while
    maintaining a specified number of recent versions.

    Args:
        supabase_path: Path in Supabase storage to clean up
        keep_versions: Number of recent versions to keep (default: 3)

    Returns:
        Dictionary with cleanup result
    """
    try:
        logger.info(f"Cleaning up old versions for: {supabase_path}")

        result = backup_service.cleanup_old_versions(supabase_path, keep_versions)

        if result.get("success"):
            logger.info("Old versions cleanup completed successfully")
        else:
            logger.error(f"Cleanup failed: {result.get('error')}")

        return result

    except Exception as e:
        logger.error(f"Version cleanup failed: {e}")
        return {"success": False, "error": str(e)}


@shared_task
def verify_b2_configuration() -> Dict[str, Any]:
    """Verify that rclone and B2 configuration are working correctly.

    This task checks if rclone is properly configured and can communicate
    with Backblaze B2.

    Returns:
        Dictionary with configuration check result
    """
    try:
        logger.info("Verifying rclone and B2 configuration")

        # Check if rclone command exists
        import subprocess
        subprocess.run(["rclone", "version"], capture_output=True, text=True, check=True)

        # Check remote configuration
        from backend.file_processor.services.offline_backup import RCLONE_B2_CONFIG

        backup_service = OfflineBackupService()
        result = backup_service.list_b2_files()

        if result.get("success"):
            logger.info(f"B2 configuration verified. Found {len(result.get('files', []))} files.")
            return {
                "success": True,
                "status": "configured",
                "bucket_name": RCLONE_B2_CONFIG["bucket"],
                "file_count": len(result.get("files", [])),
            }
        else:
            logger.error(f"B2 configuration check failed: {result.get('error')}")
            return {
                "success": False,
                "status": "error",
                "error": result.get("error"),
            }

    except FileNotFoundError:
        logger.error("rclone command not found")
        return {
            "success": False,
            "status": "not_installed",
            "error": "rclone command not found",
        }
    except subprocess.CalledProcessError as e:
        logger.error(f"rclone command failed: {e.stderr}")
        return {
            "success": False,
            "status": "error",
            "error": e.stderr.strip(),
        }
    except Exception as e:
        logger.error(f"Configuration verification failed: {e}")
        return {
            "success": False,
            "status": "error",
            "error": str(e),
        }


@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def batch_backup_sermon_files(self, sermon_id: str, file_paths: Dict[str, str]) -> Dict[str, Any]:
    """Backup all media files for a specific sermon.

    This task coordinates the backup of all optimized files for a sermon,
    including audio, video, transcripts, thumbnails, and metadata.

    Args:
        sermon_id: Unique identifier for the sermon
        file_paths: Dictionary mapping media types to file paths

    Returns:
        Dictionary with backup results for each media type
    """
    try:
        logger.info(f"Batch backup for sermon {sermon_id}")

        results = {}

        for media_type, local_path in file_paths.items():
            # Convert local path to Supabase path
            filename = os.path.basename(local_path)
            supabase_path = f"{sermon_id}/{media_type}/{filename}"

            # Perform backup
            result = backup_service.sync_to_b2(local_path, supabase_path)
            results[media_type] = result

            if not result.get("success"):
                logger.error(f"Failed to backup {media_type}: {result.get('error')}")

        # Check overall success
        all_successful = all(result.get("success") for result in results.values())
        if all_successful:
            logger.info(f"All sermon files backed up successfully: {sermon_id}")

        return {
            "success": all_successful,
            "sermon_id": sermon_id,
            "results": results,
            "total_files": len(results),
            "successful_files": sum(1 for r in results.values() if r.get("success")),
        }

    except Exception as e:
        logger.error(f"Batch backup failed: {e}")
        try:
            self.retry(exc=e, countdown=300)
        except MaxRetriesExceededError:
            logger.error("Max batch backup retries exceeded")
            return {
                "success": False,
                "error": "Max batch backup retries exceeded",
                "original_error": str(e),
            }
