"""Storage Sync Service for FileForge Post-Processing Pipeline

This module implements Supabase Storage integration for:
- Sermon metadata sync
- Task assignment storage
- RBAC for media files
- Optimized media delivery
- Storage policies and access control
"""

import logging
from typing import Any, Dict, List, Optional
from pathlib import Path
import json

from file_processor.services.supabase import SupabaseService

logger = logging.getLogger(__name__)

# Storage bucket configuration
STORAGE_BUCKETS = {
    "sermon-audio": {
        "description": "Optimized audio files",
        "public": False,
        "allowed_mime_types": ["audio/mpeg", "audio/mp4", "audio/aac"],
    },
    "sermon-video": {
        "description": "Optimized video files (H.264/AV1)",
        "public": False,
        "allowed_mime_types": ["video/mp4", "video/webm"],
    },
    "sermon-transcripts": {
        "description": "Transcripts and metadata",
        "public": False,
        "allowed_mime_types": ["text/plain", "application/json", "text/vtt", "text/srt"],
    },
    "sermon-thumbnails": {
        "description": "Video thumbnails",
        "public": True,
        "allowed_mime_types": ["image/jpeg", "image/png", "image/webp"],
    },
    "sermon-artwork": {
        "description": "Sermon artwork and cover images",
        "public": False,
        "allowed_mime_types": ["image/jpeg", "image/png", "image/webp"],
    },
}

# Storage folder structure
STORAGE_FOLDERS = {
    "audio": "audio",
    "video": "video",
    "transcripts": "transcripts",
    "thumbnails": "thumbnails",
    "artwork": "artwork",
    "original": "original",
}


class StorageSyncService:
    """Service for managing storage synchronization"""

    def __init__(self, supabase_service: Optional[SupabaseService] = None):
        self.supabase = supabase_service or SupabaseService()
        self._bucket_config = STORAGE_BUCKETS

    def get_bucket_config(self, bucket_name: str) -> Optional[Dict[str, Any]]:
        """Get bucket configuration"""
        return self._bucket_config.get(bucket_name)

    def validate_mime_type(self, bucket_name: str, mime_type: str) -> bool:
        """Validate file type against bucket constraints"""
        bucket_config = self.get_bucket_config(bucket_name)
        if not bucket_config:
            return False
        return mime_type in bucket_config.get("allowed_mime_types", [])

    def get_file_path(self, sermon_id: str, file_type: str, filename: str) -> str:
        """Generate storage file path based on sermon ID and type"""
        folder = STORAGE_FOLDERS.get(file_type, "other")
        return f"{sermon_id}/{folder}/{filename}"

    def upload_sermon_media(
        self,
        sermon_id: str,
        file_path: str,
        media_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Upload sermon media file to Supabase Storage"""
        try:
            # Determine bucket based on media type
            if media_type == "audio":
                bucket = "sermon-audio"
            elif media_type == "video":
                bucket = "sermon-video"
            elif media_type == "transcript":
                bucket = "sermon-transcripts"
            elif media_type == "thumbnail":
                bucket = "sermon-thumbnails"
            elif media_type == "artwork":
                bucket = "sermon-artwork"
            else:
                bucket = "sermon-audio"

            # Validate file type
            filename = Path(file_path).name
            mime_type = self._detect_mime_type(filename)

            if not self.validate_mime_type(bucket, mime_type):
                return {"success": False, "error": f"Invalid file type: {mime_type}"}

            # Read file content
            with open(file_path, "rb") as f:
                file_content = f.read()

            # Generate storage path
            storage_path = self.get_file_path(sermon_id, media_type, filename)

            # Upload to Supabase Storage
            result = self.supabase.storage.upload(
                bucket=bucket,
                file_path=storage_path,
                file_content=file_content,
                options={"content_type": mime_type, "cache-control": "public, max-age=31536000"},
            )

            if not result.get("success"):
                return {"success": False, "error": result.get("error")}

            # Get public URL if bucket is public
            bucket_config = self.get_bucket_config(bucket)
            if bucket_config and bucket_config.get("public"):
                public_url = self.supabase.storage.get_public_url(bucket, storage_path)
            else:
                public_url = None

            # Create signed URL for private files
            signed_url = self.supabase.storage.create_signed_url(bucket, storage_path, 3600 * 24 * 7)

            # Trigger offline backup task
            try:
                from file_processor.queue.backup_tasks import backup_to_offline_storage
                backup_to_offline_storage.delay(file_path, storage_path)
                logger.info(f"Backup task triggered for: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to trigger backup task: {e}")
            
            return {
                "success": True,
                "bucket": bucket,
                "path": storage_path,
                "filename": filename,
                "size": len(file_content),
                "mime_type": mime_type,
                "public_url": public_url,
                "signed_url": signed_url.get("url"),
                "metadata": metadata,
            }

        except Exception as e:
            logger.error(f"Failed to upload media: {e}")
            return {"success": False, "error": str(e)}

    def get_sermon_media_urls(
        self,
        sermon_id: str,
        media_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get all media URLs for a sermon"""
        try:
            media_types = media_types or ["audio", "video", "transcript", "thumbnail", "artwork"]

            urls = {}
            for media_type in media_types:
                # Determine bucket
                if media_type == "audio":
                    bucket = "sermon-audio"
                elif media_type == "video":
                    bucket = "sermon-video"
                elif media_type == "transcript":
                    bucket = "sermon-transcripts"
                elif media_type == "thumbnail":
                    bucket = "sermon-thumbnails"
                elif media_type == "artwork":
                    bucket = "sermon-artwork"
                else:
                    continue

                # List files in folder
                folder_path = f"{sermon_id}/{STORAGE_FOLDERS.get(media_type, media_type)}"
                result = self.supabase.storage.list_files(bucket, folder_path)

                if result.get("success"):
                    files = result.get("data", [])
                    for file_info in files:
                        filename = file_info.get("name")
                        file_path = f"{folder_path}/{filename}"

                        bucket_config = self.get_bucket_config(bucket)
                        if bucket_config and bucket_config.get("public"):
                            urls[f"{media_type}_{filename}"] = {
                                "url": self.supabase.storage.get_public_url(bucket, file_path),
                                "signed": False,
                            }
                        else:
                            signed_result = self.supabase.storage.create_signed_url(bucket, file_path, 3600)
                            if signed_result.get("success"):
                                urls[f"{media_type}_{filename}"] = {
                                    "url": signed_result.get("url"),
                                    "signed": True,
                                }

            return {"success": True, "urls": urls}

        except Exception as e:
            logger.error(f"Failed to get media URLs: {e}")
            return {"success": False, "error": str(e)}

    def sync_sermon_metadata(self, sermon_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Sync sermon metadata with Supabase Storage"""
        try:
            # Upload metadata file
            metadata_json = json.dumps(metadata, indent=2)
            metadata_path = self.get_file_path(sermon_id, "transcripts", "metadata.json")

            result = self.supabase.storage.upload(
                bucket="sermon-transcripts",
                file_path=metadata_path,
                file_content=metadata_json.encode("utf-8"),
                options={"content_type": "application/json"},
            )

            if not result.get("success"):
                return {"success": False, "error": result.get("error")}

            return {"success": True, "metadata_path": metadata_path}

        except Exception as e:
            logger.error(f"Failed to sync metadata: {e}")
            return {"success": False, "error": str(e)}

    def sync_task_assignment(self, task_id: str, assignment: Dict[str, Any]) -> Dict[str, Any]:
        """Sync task assignment with Supabase Storage"""
        try:
            # Store task assignment in storage
            assignment_json = json.dumps(assignment, indent=2)
            assignment_path = f"tasks/{task_id}.json"

            result = self.supabase.storage.upload(
                bucket="sermon-transcripts",
                file_path=assignment_path,
                file_content=assignment_json.encode("utf-8"),
                options={"content_type": "application/json"},
            )

            if not result.get("success"):
                return {"success": False, "error": result.get("error")}

            return {"success": True, "assignment_path": assignment_path}

        except Exception as e:
            logger.error(f"Failed to sync task assignment: {e}")
            return {"success": False, "error": str(e)}

    def cleanup_sermon_files(self, sermon_id: str) -> Dict[str, Any]:
        """Cleanup all files associated with a sermon"""
        try:
            files_to_delete = []

            for bucket, config in self._bucket_config.items():
                for media_type in STORAGE_FOLDERS:
                    folder_path = f"{sermon_id}/{media_type}"
                    result = self.supabase.storage.list_files(bucket, folder_path)

                    if result.get("success"):
                        for file_info in result.get("data", []):
                            file_path = f"{folder_path}/{file_info.get('name')}"
                            files_to_delete.append((bucket, file_path))

            for bucket, file_path in files_to_delete:
                self.supabase.storage.delete(bucket, [file_path])

            return {"success": True, "deleted_files": len(files_to_delete)}

        except Exception as e:
            logger.error(f"Failed to cleanup files: {e}")
            return {"success": False, "error": str(e)}

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get storage usage statistics"""
        try:
            stats = {}

            for bucket, config in self._bucket_config.items():
                try:
                    # Get bucket metadata
                    result = self.supabase.db.rpc("storage_bucket_stats", {"bucket_name": bucket})

                    if result.get("success"):
                        stats[bucket] = {
                            "file_count": result.get("data", {}).get("file_count", 0),
                            "total_size": result.get("data", {}).get("total_size", 0),
                            "public": config.get("public", False),
                        }

                except Exception as e:
                    logger.error(f"Failed to get bucket stats: {e}")
                    stats[bucket] = {
                        "file_count": 0,
                        "total_size": 0,
                        "public": config.get("public", False),
                    }

            return {"success": True, "stats": stats}

        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {"success": False, "error": str(e)}

    def _detect_mime_type(self, filename: str) -> str:
        """Detect MIME type from filename"""
        filename = filename.lower()

        if filename.endswith(".mp3"):
            return "audio/mpeg"
        elif filename.endswith(".m4a") or filename.endswith(".aac"):
            return "audio/mp4"
        elif filename.endswith(".mp4"):
            return "video/mp4"
        elif filename.endswith(".webm"):
            return "video/webm"
        elif filename.endswith(".wav"):
            return "audio/wav"
        elif filename.endswith(".txt"):
            return "text/plain"
        elif filename.endswith(".json"):
            return "application/json"
        elif filename.endswith(".vtt"):
            return "text/vtt"
        elif filename.endswith(".srt"):
            return "text/srt"
        elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
            return "image/jpeg"
        elif filename.endswith(".png"):
            return "image/png"
        elif filename.endswith(".webp"):
            return "image/webp"

        return "application/octet-stream"


class StorageRBACService:
    """RBAC service for storage operations"""

    def __init__(self, supabase_service: Optional[SupabaseService] = None):
        self.supabase = supabase_service or SupabaseService()

    def create_storage_rls_policies(self) -> Dict[str, Any]:
        """Create RLS policies for storage buckets"""
        try:
            policies = """
-- Storage Bucket RLS Policies
-- Sermon Audio Bucket
CREATE POLICY "Users can upload their own audio" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'sermon-audio'
        AND (auth.uid()::text = (storage.foldername(name))[1])
    );

CREATE POLICY "Users can read their own audio" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'sermon-audio'
        AND (auth.uid()::text = (storage.foldername(name))[1])
    );

CREATE POLICY "Admins can manage all audio" ON storage.objects
    FOR ALL USING (
        bucket_id = 'sermon-audio'
        AND EXISTS (
            SELECT 1 FROM user_roles
            JOIN roles ON user_roles.role_id = roles.id
            WHERE user_roles.user_id = auth.uid()
            AND roles.name IN ('admin', 'manager')
        )
    );

-- Sermon Video Bucket
CREATE POLICY "Users can upload their own video" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'sermon-video'
        AND (auth.uid()::text = (storage.foldername(name))[1])
    );

CREATE POLICY "Users can read their own video" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'sermon-video'
        AND (auth.uid()::text = (storage.foldername(name))[1])
    );

CREATE POLICY "Admins can manage all video" ON storage.objects
    FOR ALL USING (
        bucket_id = 'sermon-video'
        AND EXISTS (
            SELECT 1 FROM user_roles
            JOIN roles ON user_roles.role_id = roles.id
            WHERE user_roles.user_id = auth.uid()
            AND roles.name IN ('admin', 'manager')
        )
    );

-- Sermon Transcripts Bucket
CREATE POLICY "Users can upload their own transcripts" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'sermon-transcripts'
        AND (auth.uid()::text = (storage.foldername(name))[1])
    );

CREATE POLICY "Users can read their own transcripts" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'sermon-transcripts'
        AND (auth.uid()::text = (storage.foldername(name))[1])
    );

CREATE POLICY "Admins can manage all transcripts" ON storage.objects
    FOR ALL USING (
        bucket_id = 'sermon-transcripts'
        AND EXISTS (
            SELECT 1 FROM user_roles
            JOIN roles ON user_roles.role_id = roles.id
            WHERE user_roles.user_id = auth.uid()
            AND roles.name IN ('admin', 'manager')
        )
    );

-- Sermon Thumbnails Bucket (Public)
CREATE POLICY "Thumbnails are publicly readable" ON storage.objects
    FOR SELECT USING (bucket_id = 'sermon-thumbnails');

CREATE POLICY "Users can upload their own thumbnails" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'sermon-thumbnails'
        AND (auth.uid()::text = (storage.foldername(name))[1])
    );

CREATE POLICY "Admins can manage all thumbnails" ON storage.objects
    FOR ALL USING (
        bucket_id = 'sermon-thumbnails'
        AND EXISTS (
            SELECT 1 FROM user_roles
            JOIN roles ON user_roles.role_id = roles.id
            WHERE user_roles.user_id = auth.uid()
            AND roles.name IN ('admin', 'manager')
        )
    );

-- Sermon Artwork Bucket
CREATE POLICY "Users can upload their own artwork" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'sermon-artwork'
        AND (auth.uid()::text = (storage.foldername(name))[1])
    );

CREATE POLICY "Users can read their own artwork" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'sermon-artwork'
        AND (auth.uid()::text = (storage.foldername(name))[1])
    );

CREATE POLICY "Admins can manage all artwork" ON storage.objects
    FOR ALL USING (
        bucket_id = 'sermon-artwork'
        AND EXISTS (
            SELECT 1 FROM user_roles
            JOIN roles ON user_roles.role_id = roles.id
            WHERE user_roles.user_id = auth.uid()
            AND roles.name IN ('admin', 'manager')
        )
    );
            """.strip()

            return {"success": True, "policies": policies}

        except Exception as e:
            logger.error(f"Failed to create storage policies: {e}")
            return {"success": False, "error": str(e)}
