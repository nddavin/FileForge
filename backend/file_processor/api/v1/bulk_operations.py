"""Bulk File Operations API - Smart sorting and package management"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from ...api.deps import get_current_user
from ...core.dependencies import get_db
from ...models.user import User
from ...models.file import File, SortingRule as SortingRuleModel

router = APIRouter()


# Request/Response Models
class SortCondition(BaseModel):
    field: str
    operator: str
    value: str | int | bool


class SortingRuleSchema(BaseModel):
    id: Optional[str] = None
    name: str
    conditions: List[SortCondition]
    target_folder: str
    priority: int = 0
    auto_apply: bool = True


class BulkSortRequest(BaseModel):
    file_ids: List[str]
    rules: Optional[List[SortingRule]] = None
    sort_by: Optional[str] = None
    church_id: str


class BulkPackageRequest(BaseModel):
    file_ids: List[str]
    church_id: str
    name: Optional[str] = None


class BulkMoveRequest(BaseModel):
    file_ids: List[str]
    folder_id: str


class BulkOptimizeRequest(BaseModel):
    file_ids: List[str]
    church_id: str


class TagRequest(BaseModel):
    tags: List[str]


@router.post("/bulk-sort")
async def bulk_smart_sort(
    request: BulkSortRequest, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Apply AI sorting rules to bulk files"""

    sorted_count = 0
    rules_applied = 0

    for file_id in request.file_ids:
        # Get file from database
        file_record = db.query(File).filter(File.id == file_id).first()
        if not file_record:
            continue

        # Apply rules if provided
        if request.rules:
            for rule in request.rules:
                matches = True
                for cond in rule.conditions:
                    file_val = getattr(file_record, cond.field, None)
                    if file_val != cond.value:
                        matches = False
                        break

                if matches:
                    file_record.folder_id = rule.target_folder
                    rules_applied += 1
                    break

        # Apply manual sort
        if request.sort_by:
            predicted_folder = predict_folder_for_file(file_record, request.sort_by)
            if predicted_folder:
                file_record.folder_id = predicted_folder
                sorted_count += 1

    db.commit()
    return {
        "sorted": sorted_count,
        "rules_applied": rules_applied,
        "message": f"Processed {len(request.file_ids)} files",
    }


@router.post("/bulk-package")
async def bulk_create_package(
    request: BulkPackageRequest, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create sermon package from selected files"""

    import uuid
    from datetime import datetime

    package_id = str(uuid.uuid4())
    package_name = request.name or (
        f"Sermon Package {datetime.now().strftime('%Y-%m-%d')}"
    )

    # Update all files with package_id
    for file_id in request.file_ids:
        file_record = db.query(File).filter(File.id == file_id).first()
        if file_record:
            file_record.sermon_package_id = package_id

    db.commit()

    return {
        "package_id": package_id,
        "package_name": package_name,
        "file_count": len(request.file_ids),
        "message": "Sermon package created successfully",
    }


@router.post("/bulk-move")
async def bulk_move_files(
    request: BulkMoveRequest, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Move files to specified folder"""

    moved_count = 0

    for file_id in request.file_ids:
        file_record = db.query(File).filter(File.id == file_id).first()
        if file_record:
            file_record.folder_id = request.folder_id
            moved_count += 1

    db.commit()
    return {"moved": moved_count, "message": f"Moved {moved_count} files to folder"}


@router.post("/bulk-optimize")
async def bulk_optimize(
    request: BulkOptimizeRequest, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Queue files for quality optimization"""

    from ...celery_tasks import optimize_media_task

    optimized_count = 0

    for file_id in request.file_ids:
        file_record = db.query(File).filter(File.id == file_id).first()
        if file_record and file_record.file_type in ["video", "audio"]:
            # Queue optimization task
            optimize_media_task.delay(file_id)
            optimized_count += 1

    return {
        "queued": optimized_count,
        "message": f"Queued {optimized_count} files for optimization",
    }


@router.post("/bulk-tag")
async def bulk_tag_files(
    file_ids: List[str],
    request: TagRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add tags to multiple files"""

    tagged_count = 0

    for file_id in file_ids:
        file_record = db.query(File).filter(File.id == file_id).first()
        if file_record:
            # Get existing tags or initialize empty list
            existing_tags = file_record.tags or []
            # Add new tags that don't exist
            for tag in request.tags:
                if tag not in existing_tags:
                    existing_tags.append(tag)
            file_record.tags = existing_tags
            tagged_count += 1

    db.commit()
    return {
        "tagged": tagged_count,
        "message": f"Added tags to {tagged_count} files",
    }


# ============ Rules Endpoints ============

@router.get("/rules")
async def get_sorting_rules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all sorting rules for current user's church"""
    rules = db.query(SortingRuleModel).all()
    return [rule.to_dict() for rule in rules]


@router.post("/rules")
async def create_sorting_rule(
    rule: SortingRuleSchema, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new sorting rule"""

    rule_data = {
        "church_id": current_user.church_id if hasattr(current_user, 'church_id') else "default",
        "name": rule.name,
        "conditions": [c.model_dump() for c in rule.conditions],
        "target_folder": rule.target_folder,
        "priority": rule.priority,
        "auto_apply": rule.auto_apply,
    }

    new_rule = SortingRuleModel(**rule_data)
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)

    return {"message": "Rule created successfully", "rule_id": str(new_rule.id)}


@router.delete("/rules/{rule_id}")
async def delete_sorting_rule(
    rule_id: str, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a sorting rule"""

    rule = db.query(SortingRuleModel).filter(SortingRuleModel.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    db.delete(rule)
    db.commit()

    return {"message": "Rule deleted successfully"}


# ============ Files CRUD ============

@router.post("/files")
async def create_file(
    file_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new file record"""

    file_record = File(
        user_id=current_user.id,
        name=file_data.get("name"),
        path=file_data.get("path"),
        size=file_data.get("size", 0),
        content_type=file_data.get("content_type", "application/octet-stream"),
        metadata=file_data.get("metadata", {}),
        tags=file_data.get("tags", []),
    )

    db.add(file_record)
    db.commit()
    db.refresh(file_record)

    return {"id": file_record.id, "message": "File created successfully"}


@router.patch("/files/{file_id}")
async def update_file(
    file_id: str,
    file_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a file record"""

    file_record = db.query(File).filter(File.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    # Update fields
    if "name" in file_data:
        file_record.name = file_data["name"]
    if "path" in file_data:
        file_record.path = file_data["path"]
    if "metadata" in file_data:
        file_record.metadata = file_data["metadata"]
    if "tags" in file_data:
        file_record.tags = file_data["tags"]
    if "folder_id" in file_data:
        file_record.folder_id = file_data["folder_id"]

    db.commit()
    db.refresh(file_record)

    return {"message": "File updated successfully", "file": file_record.to_dict()}


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a file record"""

    file_record = db.query(File).filter(File.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    db.delete(file_record)
    db.commit()

    return {"message": "File deleted successfully"}


# Helper function for prediction
def predict_folder_for_file(file: File, sort_by: str) -> Optional[str]:
    """Predict target folder based on sort criteria"""

    folders = {
        "preacher": f"/sermons/{file.preacher_id or 'unknown'}",
        "location": f"/sermons/{file.location_city or 'unknown'}",
        "quality": (
            "/sermons/quality-check"
            if (file.quality_score or 0) < 70
            else "/sermons/approved"
        ),
        "language": f"/sermons/{file.primary_language or 'unknown'}",
        "type": f"/sermons/{file.file_type or 'mixed'}",
    }

    return folders.get(sort_by)
