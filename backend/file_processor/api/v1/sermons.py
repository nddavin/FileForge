"""Sermon Processing API Routes"""

import os
import tempfile
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.file_processor.database import get_db
from backend.file_processor.models.file import File as FileModel
from backend.file_processor.models.user import User
from backend.file_processor.core.rbac_security import (
    get_current_active_user,
    require_permission,
)
from backend.file_processor.services.sermon_processor import (
    SermonProcessor,
    SermonMetadata,
    create_sermon_processor,
)
from backend.file_processor.services.supabase import SupabaseService

router = APIRouter(prefix="/sermons", tags=["Sermons"])

# Global processor instance
_processor: Optional[SermonProcessor] = None


def get_processor() -> SermonProcessor:
    """Get or create sermon processor"""
    global _processor
    if _processor is None:
        _processor = create_sermon_processor()
    return _processor


# Request/Response models
class SermonMetadataUpdate(BaseModel):
    """Update sermon metadata"""

    series_title: Optional[str] = None
    sermon_title: Optional[str] = None
    theme_scripture: Optional[str] = None
    recording_location: Optional[str] = None


class TeamAssignment(BaseModel):
    """Team assignment for sermon"""

    video_editor: Optional[str] = None
    audio_engineer: Optional[str] = None
    transcriber: Optional[str] = None


class OptimizationRequest(BaseModel):
    """Optimization request"""

    profile: str = "sermon_web"


class ProcessingResponse(BaseModel):
    """Processing response"""

    success: bool
    file_id: int
    metadata: dict
    quality_metrics: dict
    optimized_files: List[dict] = []


# ============ Processing Endpoints ============


@router.post("/process", response_model=ProcessingResponse)
async def process_sermon(
    files: List[UploadFile] = File(...),
    series_title: Optional[str] = Form(None),
    church_id: Optional[str] = Form(None),
    current_user: User = Depends(require_permission("files:upload")),
    db=Depends(get_db),
):
    """
    Process a sermon through the full pipeline:
    1. Detect media components (video, audio, transcript)
    2. Extract location from audio metadata
    3. Analyze transcript with AI
    4. Analyze quality metrics
    5. Assign processing team
    """
    processor = get_processor()

    # Save uploaded files temporarily
    temp_paths = []
    try:
        for upload_file in files:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                content = await upload_file.read()
                tmp.write(content)
                tmp.flush()
                temp_paths.append(tmp.name)

        # Process sermon
        results = await processor.process_sermon(
            file_paths=temp_paths, church_id=church_id, series_title=series_title
        )

        # Create file record with sermon metadata
        file_record = FileModel(
            user_id=current_user.id,
            name=files[0].filename or "sermon_upload",
            path=temp_paths[0] if temp_paths else "",
            size=os.path.getsize(temp_paths[0]) if temp_paths else 0,
            content_type=files[0].content_type or "application/octet-stream",
            status="processed",
            metadata=results["metadata"].to_dict(),
        )

        db.add(file_record)
        db.commit()
        db.refresh(file_record)

        return ProcessingResponse(
            success=True,
            file_id=file_record.id,
            metadata=results["metadata"].to_dict(),
            quality_metrics=results["quality"],
            optimized_files=results.get("optimized_files", []),
        )

    except Exception as e:
        logger.error(f"Sermon processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

    finally:
        # Cleanup temp files
        for path in temp_paths:
            try:
                os.unlink(path)
            except:
                pass


@router.post("/{file_id}/optimize")
async def optimize_sermon(
    file_id: int,
    profile: str = Query("sermon_web", description="Optimization profile"),
    current_user: User = Depends(require_permission("files:upload")),
    db=Depends(get_db),
):
    """Optimize a sermon file using specified profile"""
    processor = get_processor()

    # Get file record
    file_record = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    # Check access
    if file_record.user_id != current_user.id:
        if "files:view_all" not in [
            p.name for r in current_user.roles for p in r.permissions
        ]:
            raise HTTPException(status_code=403, detail="Access denied")

    # Run optimization
    result = processor.optimize(input_path=file_record.path, profile_name=profile)

    if result:
        return {
            "success": True,
            "original_path": result["input_path"],
            "optimized_path": result["output_path"],
            "profile": profile,
            "file_size": result["file_size"],
        }

    raise HTTPException(status_code=500, detail="Optimization failed")


@router.post("/{file_id}/analyze")
async def analyze_sermon_transcript(
    file_id: int,
    current_user: User = Depends(require_permission("files:view")),
    db=Depends(get_db),
):
    """Run AI analysis on sermon transcript"""
    processor = get_processor()

    file_record = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    metadata = file_record.metadata or {}
    transcript_path = metadata.get("transcript_path")

    if not transcript_path or not os.path.exists(transcript_path):
        raise HTTPException(status_code=400, detail="No transcript available")

    # Run AI analysis
    analysis = await processor.ai_analyzer.analyze_transcript(transcript_path)

    # Update metadata
    if analysis:
        metadata.update(
            {
                "series_title": analysis.get("series_title"),
                "sermon_title": analysis.get("sermon_title"),
                "theme_scripture": analysis.get("theme_scripture"),
                "analysis_complete": True,
            }
        )
        file_record.metadata = metadata
        db.commit()

    return {"success": True, "analysis": analysis}


# ============ Metadata Endpoints ============


@router.get("/{file_id}/metadata")
async def get_sermon_metadata(
    file_id: int,
    current_user: User = Depends(require_permission("files:view")),
    db=Depends(get_db),
):
    """Get sermon metadata"""
    file_record = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    return {
        "id": file_record.id,
        "name": file_record.name,
        "metadata": file_record.metadata or {},
        "created_at": file_record.created_at,
    }


@router.patch("/{file_id}/metadata")
async def update_sermon_metadata(
    file_id: int,
    updates: SermonMetadataUpdate,
    current_user: User = Depends(require_permission("files:update")),
    db=Depends(get_db),
):
    """Update sermon metadata"""
    file_record = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    metadata = file_record.metadata or {}
    metadata.update(updates.model_dump(exclude_none=True))
    file_record.metadata = metadata
    file_record.updated_at = datetime.now(timezone.utc).isoformat()

    db.commit()

    return {"success": True, "metadata": metadata}


# ============ Team Management ============


@router.get("/{file_id}/team")
async def get_sermon_team(
    file_id: int,
    current_user: User = Depends(require_permission("users:view")),
    db=Depends(get_db),
):
    """Get assigned team for sermon"""
    file_record = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    metadata = file_record.metadata or {}
    return {"file_id": file_id, "team": metadata.get("assigned_team", {})}


@router.put("/{file_id}/team")
async def update_sermon_team(
    file_id: int,
    team: TeamAssignment,
    current_user: User = Depends(require_permission("users:manage")),
    db=Depends(get_db),
):
    """Update team assignment for sermon"""
    file_record = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    metadata = file_record.metadata or {}
    metadata["assigned_team"] = {
        "video_editor": team.video_editor,
        "audio_engineer": team.audio_engineer,
        "transcriber": team.transcriber,
    }
    file_record.metadata = metadata

    db.commit()

    return {"success": True, "team": metadata["assigned_team"]}


# ============ Quality Reports ============


@router.get("/{file_id}/quality")
async def get_quality_report(
    file_id: int,
    current_user: User = Depends(require_permission("files:view")),
    db=Depends(get_db),
):
    """Get quality analysis report"""
    file_record = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    processor = get_processor()
    quality = processor.quality_analyzer.analyze(file_record.path)

    return {"file_id": file_id, "quality": quality.to_dict()}


# ============ Batch Processing ============


@router.post("/batch/optimize")
async def batch_optimize(
    file_ids: List[int],
    profile: str = Query("sermon_web"),
    current_user: User = Depends(require_permission("files:upload")),
    db=Depends(get_db),
):
    """Optimize multiple sermon files"""
    processor = get_processor()

    results = []
    for file_id in file_ids:
        file_record = db.query(FileModel).filter(FileModel.id == file_id).first()
        if not file_record:
            results.append({"file_id": file_id, "success": False, "error": "Not found"})
            continue

        if file_record.user_id != current_user.id:
            results.append(
                {"file_id": file_id, "success": False, "error": "Access denied"}
            )
            continue

        result = processor.optimize(file_record.path, profile)
        if result:
            results.append(
                {
                    "file_id": file_id,
                    "success": True,
                    "optimized_path": result["output_path"],
                }
            )
        else:
            results.append(
                {"file_id": file_id, "success": False, "error": "Optimization failed"}
            )

    return {
        "total": len(file_ids),
        "successful": sum(1 for r in results if r.get("success")),
        "results": results,
    }


# ============ Statistics ============


@router.get("/stats")
async def get_sermon_stats(
    current_user: User = Depends(require_permission("files:view")), db=Depends(get_db)
):
    """Get sermon processing statistics"""
    files = db.query(FileModel).filter(FileModel.metadata.isnot(None)).all()

    stats = {
        "total_sermons": len(files),
        "with_video": 0,
        "with_audio": 0,
        "with_transcript": 0,
        "with_ai_analysis": 0,
        "average_duration": 0,
    }

    total_duration = 0
    for f in files:
        metadata = f.metadata or {}
        if metadata.get("has_video"):
            stats["with_video"] += 1
        if metadata.get("has_audio"):
            stats["with_audio"] += 1
        if metadata.get("has_transcript"):
            stats["with_transcript"] += 1
        if metadata.get("analysis_complete"):
            stats["with_ai_analysis"] += 1

        duration = metadata.get("duration_seconds", 0)
        total_duration += duration

    if files:
        stats["average_duration"] = total_duration // len(files)

    return stats
