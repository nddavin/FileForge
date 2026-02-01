"""Storage Sync API Endpoints

This module provides API endpoints for managing Supabase Storage integration:
- Uploading and downloading media files
- Synchronizing sermon metadata
- Getting media URLs
- Storage statistics
- File management operations
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
from backend.file_processor.services.storage_sync import StorageSyncService
from backend.file_processor.models.user import User
from backend.file_processor.core.rbac_security import (
    require_permission,
)
import os
import tempfile

router = APIRouter(prefix="/storage", tags=["Storage"])

logger = logging.getLogger(__name__)

@router.post("/upload-sermon-media")
async def upload_sermon_media(
    sermon_id: str,
    media_type: str = Query(..., regex="^(audio|video|transcript|thumbnail|artwork)$"),
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission("sermons:create")),
):
    """Upload sermon media file to Supabase Storage with proper organization and permissions.
    
    Args:
        sermon_id: Unique identifier for the sermon
        media_type: Type of media file (audio, video, transcript, thumbnail, artwork)
        file: File to upload
        current_user: Current authenticated user
        
    Returns:
        Dictionary containing upload information
    """
    try:
        storage_sync = StorageSyncService()
        
        # Read file content
        file_content = await file.read()
        
        # Create temporary file to process
        suffix = os.path.splitext(file.filename)[1] if file.filename else ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(file_content)
            temp_filename = temp_file.name
            
        # Upload to storage
        result = storage_sync.upload_sermon_media(
            sermon_id=sermon_id,
            file_path=temp_filename,
            media_type=media_type,
            metadata={
                "uploaded_by": current_user.id,
                "filename": file.filename,
                "content_type": file.content_type,
            },
        )
        
        # Remove temporary file
        os.remove(temp_filename)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
            
        return result
        
    except Exception as e:
        logger.error(f"Failed to upload sermon media: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload media file")

@router.get("/sermon-media-urls/{sermon_id}")
async def get_sermon_media_urls(
    sermon_id: str,
    media_types: Optional[List[str]] = Query(None, regex="^(audio|video|transcript|thumbnail|artwork)$"),
    current_user: User = Depends(require_permission("sermons:view")),
):
    """Get all media URLs for a specific sermon with appropriate permissions.
    
    Args:
        sermon_id: Unique identifier for the sermon
        media_types: Optional list of media types to filter (audio, video, transcript, thumbnail, artwork)
        current_user: Current authenticated user
        
    Returns:
        Dictionary containing media URLs
    """
    try:
        storage_sync = StorageSyncService()
        
        result = storage_sync.get_sermon_media_urls(
            sermon_id=sermon_id,
            media_types=media_types,
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
            
        return result
        
    except Exception as e:
        logger.error(f"Failed to get sermon media URLs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get media URLs")

@router.post("/sync-sermon-metadata/{sermon_id}")
async def sync_sermon_metadata(
    sermon_id: str,
    metadata: dict,
    current_user: User = Depends(require_permission("sermons:update")),
):
    """Sync sermon metadata with Supabase Storage.
    
    Args:
        sermon_id: Unique identifier for the sermon
        metadata: Sermon metadata to sync
        current_user: Current authenticated user
        
    Returns:
        Dictionary containing sync information
    """
    try:
        storage_sync = StorageSyncService()
        
        result = storage_sync.sync_sermon_metadata(
            sermon_id=sermon_id,
            metadata={**metadata, "updated_by": current_user.id},
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
            
        return result
        
    except Exception as e:
        logger.error(f"Failed to sync sermon metadata: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync metadata")

@router.post("/sync-task-assignment/{task_id}")
async def sync_task_assignment(
    task_id: str,
    assignment: dict,
    current_user: User = Depends(require_permission("tasks:assign")),
):
    """Sync task assignment with Supabase Storage.
    
    Args:
        task_id: Unique identifier for the task
        assignment: Task assignment data to sync
        current_user: Current authenticated user
        
    Returns:
        Dictionary containing sync information
    """
    try:
        storage_sync = StorageSyncService()
        
        result = storage_sync.sync_task_assignment(
            task_id=task_id,
            assignment={**assignment, "assigned_by": current_user.id},
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
            
        return result
        
    except Exception as e:
        logger.error(f"Failed to sync task assignment: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync task assignment")

@router.delete("/cleanup-sermon-files/{sermon_id}")
async def cleanup_sermon_files(
    sermon_id: str,
    current_user: User = Depends(require_permission("sermons:delete")),
):
    """Clean up all files associated with a sermon.
    
    Args:
        sermon_id: Unique identifier for the sermon
        current_user: Current authenticated user
        
    Returns:
        Dictionary containing cleanup information
    """
    try:
        storage_sync = StorageSyncService()
        
        result = storage_sync.cleanup_sermon_files(sermon_id=sermon_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
            
        return result
        
    except Exception as e:
        logger.error(f"Failed to cleanup sermon files: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup sermon files")

@router.get("/storage-stats")
async def get_storage_stats(
    current_user: User = Depends(require_permission("admin:view")),
):
    """Get storage usage statistics.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Dictionary containing storage statistics
    """
    try:
        storage_sync = StorageSyncService()
        
        result = storage_sync.get_usage_stats()
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
            
        return result
        
    except Exception as e:
        logger.error(f"Failed to get storage stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get storage statistics")

@router.get("/create-storage-rls-policies")
async def create_storage_rls_policies(
    current_user: User = Depends(require_permission("admin:manage")),
):
    """Create RLS policies for storage buckets.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Dictionary containing policy creation information
    """
    try:
        from backend.file_processor.services.storage_sync import StorageRBACService
        storage_rbac = StorageRBACService()
        
        result = storage_rbac.create_storage_rls_policies()
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
            
        return result
        
    except Exception as e:
        logger.error(f"Failed to create storage RLS policies: {e}")
        raise HTTPException(status_code=500, detail="Failed to create storage policies")
