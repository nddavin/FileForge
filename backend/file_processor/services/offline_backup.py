"""Offline Storage Backup Service for FileForge

This module provides Backblaze B2 integration with rclone for offline storage backup.
It implements a cold storage tier with unlimited retention and versioning.
"""

import logging
import subprocess
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

# rclone remote configuration for Backblaze B2
RCLONE_B2_CONFIG = {
    "remote_name": "b2-backup",
    "bucket": "fileforge-archive",
    "trashed_bucket": "fileforge-trashed",
}

# rclone command templates
RCLONE_SYNC_CMD = [
    "rclone",
    "sync",
    "{local_path}",
    "{remote_path}",
    "--backup-dir", "{backup_dir}",
    "--progress",
    "--log-level", "INFO",
]

RCLONE_COPY_CMD = [
    "rclone",
    "copy",
    "{local_path}",
    "{remote_path}",
    "--progress",
    "--log-level", "INFO",
]

RCLONE_LIST_CMD = [
    "rclone",
    "ls",
    "{remote_path}",
    "--log-level", "ERROR",
]


class OfflineBackupService:
    """Service for managing offline storage backup operations"""

    def __init__(self):
        self.config = RCLONE_B2_CONFIG
        self.ensure_rclone_configured()

    def ensure_rclone_configured(self) -> bool:
        """Check if rclone is configured with B2 remote"""
        try:
            # List remote buckets to test configuration
            result = subprocess.run(
                ["rclone", "listremotes"],
                capture_output=True,
                text=True,
                check=True,
            )
            remote_names = [line.strip() for line in result.stdout.splitlines()]
            if f"{self.config['remote_name']}:" not in remote_names:
                logger.error(f"rclone remote '{self.config['remote_name']}' not configured")
                return False
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"rclone configuration check failed: {e.stderr}")
            return False
        except FileNotFoundError:
            logger.error("rclone command not found")
            return False

    def get_remote_path(self, supabase_path: str) -> str:
        """Get remote B2 path from Supabase storage path"""
        # Strip any leading slashes
        supabase_path = supabase_path.lstrip("/")
        return f"{self.config['remote_name']}:{self.config['bucket']}/{supabase_path}"

    def get_backup_dir(self) -> str:
        """Get backup directory for soft delete operations"""
        return f"{self.config['remote_name']}:{self.config['trashed_bucket']}"

    def sync_to_b2(self, local_path: str, supabase_path: str) -> Dict[str, Any]:
        """Sync local file to Backblaze B2 with versioning and soft delete"""
        try:
            # Check if rclone is configured
            if not self.ensure_rclone_configured():
                return {"success": False, "error": "rclone not configured"}

            # Verify local file exists
            if not os.path.exists(local_path):
                return {"success": False, "error": f"Local file not found: {local_path}"}

            # Build and execute rclone command
            remote_path = self.get_remote_path(supabase_path)
            backup_dir = self.get_backup_dir()

            cmd = [
                "rclone",
                "sync",
                local_path,
                remote_path,
                "--backup-dir", backup_dir,
                "--progress",
                "--log-level", "INFO",
            ]

            logger.info(f"Syncing {local_path} to {remote_path}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                logger.info(f"Successfully synced to B2: {remote_path}")
                return {"success": True, "remote_path": remote_path}
            else:
                logger.error(f"rclone sync failed: {result.stderr}")
                return {"success": False, "error": result.stderr}

        except Exception as e:
            logger.error(f"Backup to B2 failed: {e}")
            return {"success": False, "error": str(e)}

    def copy_to_b2(self, local_path: str, supabase_path: str) -> Dict[str, Any]:
        """Copy file to B2 without syncing (preserves existing files)"""
        try:
            if not self.ensure_rclone_configured():
                return {"success": False, "error": "rclone not configured"}

            if not os.path.exists(local_path):
                return {"success": False, "error": f"Local file not found: {local_path}"}

            remote_path = self.get_remote_path(supabase_path)

            cmd = [
                "rclone",
                "copy",
                local_path,
                remote_path,
                "--progress",
                "--log-level", "INFO",
            ]

            logger.info(f"Copying {local_path} to {remote_path}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                logger.info(f"Successfully copied to B2: {remote_path}")
                return {"success": True, "remote_path": remote_path}
            else:
                logger.error(f"rclone copy failed: {result.stderr}")
                return {"success": False, "error": result.stderr}

        except Exception as e:
            logger.error(f"Copy to B2 failed: {e}")
            return {"success": False, "error": str(e)}

    def list_b2_files(self, supabase_path: str = "") -> Dict[str, Any]:
        """List files in B2 bucket"""
        try:
            if not self.ensure_rclone_configured():
                return {"success": False, "error": "rclone not configured"}

            remote_path = self.get_remote_path(supabase_path)

            cmd = [
                "rclone",
                "ls",
                remote_path,
                "--log-level", "ERROR",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                files = []
                for line in result.stdout.splitlines():
                    if line.strip():
                        size, filename = line.strip().split(maxsplit=1)
                        files.append({
                            "name": filename,
                            "size": int(size),
                        })
                return {"success": True, "files": files}
            else:
                logger.error(f"rclone list failed: {result.stderr}")
                return {"success": False, "error": result.stderr}

        except Exception as e:
            logger.error(f"List B2 files failed: {e}")
            return {"success": False, "error": str(e)}

    def restore_from_b2(self, supabase_path: str, local_path: str) -> Dict[str, Any]:
        """Restore file from B2 to local storage"""
        try:
            if not self.ensure_rclone_configured():
                return {"success": False, "error": "rclone not configured"}

            remote_path = self.get_remote_path(supabase_path)
            local_dir = os.path.dirname(local_path)
            os.makedirs(local_dir, exist_ok=True)

            cmd = [
                "rclone",
                "copy",
                remote_path,
                local_path,
                "--progress",
                "--log-level", "INFO",
            ]

            logger.info(f"Restoring {remote_path} to {local_path}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                logger.info(f"Successfully restored from B2: {local_path}")
                return {"success": True, "local_path": local_path}
            else:
                logger.error(f"rclone restore failed: {result.stderr}")
                return {"success": False, "error": result.stderr}

        except Exception as e:
            logger.error(f"Restore from B2 failed: {e}")
            return {"success": False, "error": str(e)}

    def cleanup_old_versions(self, supabase_path: str, keep_versions: int = 3) -> Dict[str, Any]:
        """Cleanup old versions (soft delete to trash bucket)"""
        try:
            if not self.ensure_rclone_configured():
                return {"success": False, "error": "rclone not configured"}

            remote_path = self.get_remote_path(supabase_path)
            backup_dir = self.get_backup_dir()

            cmd = [
                "rclone",
                "sync",
                remote_path,
                remote_path,
                "--backup-dir", f"{backup_dir}/{supabase_path}",
                "--max-backlog", str(keep_versions),
                "--progress",
                "--log-level", "INFO",
            ]

            logger.info(f"Cleaning up old versions for {supabase_path}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                logger.info(f"Successfully cleaned up old versions")
                return {"success": True}
            else:
                logger.error(f"rclone cleanup failed: {result.stderr}")
                return {"success": False, "error": result.stderr}

        except Exception as e:
            logger.error(f"Cleanup old versions failed: {e}")
            return {"success": False, "error": str(e)}
