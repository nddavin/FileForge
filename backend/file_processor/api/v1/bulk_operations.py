"""Bulk File Operations API - Smart sorting and package management"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from ...api.deps import get_current_user
from ...core.dependencies import get_db
from ...models.user import User
from ...models.file import File

router = APIRouter()


# Request/Response Models
class SortCondition(BaseModel):
    field: str
    operator: str
    value: str | int | bool


class SortingRule(BaseModel):
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


@router.post("/bulk-sort")
async def bulk_smart_sort(
    request: BulkSortRequest, current_user: User = Depends(get_current_user)
):
    """Apply AI sorting rules to bulk files"""

    sorted_count = 0
    rules_applied = 0

    for file_id in request.file_ids:
        # Get file
        file = await File.get(file_id)
        if not file:
            continue

        # Apply rules if provided
        if request.rules:
            for rule in request.rules:
                matches = True
                for cond in rule.conditions:
                    file_val = getattr(file, cond.field, None)
                    if file_val != cond.value:
                        matches = False
                        break

                if matches:
                    file.folder_id = rule.target_folder
                    await file.save()
                    rules_applied += 1
                    break

        # Apply manual sort
        if request.sort_by:
            predicted_folder = predict_folder_for_file(file, request.sort_by)
            if predicted_folder:
                file.folder_id = predicted_folder
                await file.save()
                sorted_count += 1

    return {
        "sorted": sorted_count,
        "rules_applied": rules_applied,
        "message": f"Processed {len(request.file_ids)} files",
    }


@router.post("/bulk-package")
async def bulk_create_package(
    request: BulkPackageRequest, current_user: User = Depends(get_current_user)
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
        file = await File.get(file_id)
        if file:
            file.sermon_package_id = package_id
            await file.save()

    return {
        "package_id": package_id,
        "package_name": package_name,
        "file_count": len(request.file_ids),
        "message": "Sermon package created successfully",
    }


@router.post("/bulk-move")
async def bulk_move_files(
    request: BulkMoveRequest, current_user: User = Depends(get_current_user)
):
    """Move files to specified folder"""

    moved_count = 0

    for file_id in request.file_ids:
        file = await File.get(file_id)
        if file:
            file.folder_id = request.folder_id
            await file.save()
            moved_count += 1

    return {"moved": moved_count, "message": f"Moved {moved_count} files to folder"}


@router.post("/bulk-optimize")
async def bulk_optimize(
    request: BulkOptimizeRequest, current_user: User = Depends(get_current_user)
):
    """Queue files for quality optimization"""

    from app.celery_tasks import optimize_media_task

    optimized_count = 0

    for file_id in request.file_ids:
        file = await File.get(file_id)
        if file and file.file_type in ["video", "audio"]:
            # Queue optimization task
            optimize_media_task.delay(file_id)
            optimized_count += 1

    return {
        "queued": optimized_count,
        "message": f"Queued {optimized_count} files for optimization",
    }


@router.post("/rules/save")
async def save_sorting_rule(
    rule: SortingRule, current_user: User = Depends(get_current_user)
):
    """Save a sorting rule to database"""

    from app.models.file import SortingRule as SortingRuleModel

    # Convert to dict
    rule_data = {
        "church_id": current_user.church_id,
        "name": rule.name,
        "conditions": [c.model_dump() for c in rule.conditions],
        "target_folder": rule.target_folder,
        "priority": rule.priority,
        "auto_apply": rule.auto_apply,
    }

    if rule.id:
        # Update existing
        await SortingRuleModel.update(rule.id, **rule_data)
    else:
        # Create new
        await SortingRuleModel.create(**rule_data)

    return {"message": "Rule saved successfully", "rule_id": rule.id}


@router.delete("/rules/{rule_id}")
async def delete_sorting_rule(
    rule_id: str, current_user: User = Depends(get_current_user)
):
    """Delete a sorting rule"""

    from app.models.file import SortingRule as SortingRuleModel

    await SortingRuleModel.delete(rule_id)

    return {"message": "Rule deleted successfully"}


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
