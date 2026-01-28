"""RBAC API Routes for Role and Permission Management"""

from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.file_processor.database import get_db
from backend.file_processor.models.rbac import Role, Permission, AuditLog, DEFAULT_ROLES, DEFAULT_PERMISSIONS
from backend.file_processor.models.user import User
from backend.file_processor.core.rbac_security import (
    get_current_active_user,
    require_admin,
    log_audit_event,
    has_any_role,
    get_user_permissions,
    AuthenticationError,
    AuthorizationError
)

router = APIRouter(prefix="/rbac", tags=["RBAC"])


# ============ Permission Endpoints ============

@router.get("/permissions", response_model=List[dict])
async def list_permissions(
    resource: Optional[str] = Query(None, description="Filter by resource"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List all permissions, optionally filtered by resource"""
    query = db.query(Permission).filter(Permission.is_active == True)
    
    if resource:
        query = query.filter(Permission.resource == resource)
    
    permissions = query.all()
    return [p.to_dict() for p in permissions]


@router.get("/permissions/{permission_id}", response_model=dict)
async def get_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get a specific permission"""
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    return permission.to_dict()


@router.post("/permissions", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_permission(
    name: str,
    resource: str,
    action: str,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new permission"""
    # Check if permission already exists
    existing = db.query(Permission).filter(Permission.name == name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission with this name already exists"
        )
    
    permission = Permission(
        name=name,
        resource=resource,
        action=action,
        description=description
    )
    db.add(permission)
    db.commit()
    db.refresh(permission)
    
    # Audit log
    log_audit_event(
        db=db,
        user_id=current_user.id,
        action="create_permission",
        resource="permission",
        resource_id=str(permission.id),
        details={"name": name, "resource": resource, "action": action}
    )
    
    return permission.to_dict()


@router.delete("/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete a permission (soft delete by deactivating)"""
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    
    permission.is_active = False
    db.commit()
    
    log_audit_event(
        db=db,
        user_id=current_user.id,
        action="delete_permission",
        resource="permission",
        resource_id=str(permission_id)
    )


# ============ Role Endpoints ============

@router.get("/roles", response_model=List[dict])
async def list_roles(
    include_inactive: bool = Query(False, description="Include inactive roles"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List all roles"""
    query = db.query(Role)
    if not include_inactive:
        query = query.filter(Role.is_active == True)
    
    roles = query.all()
    return [r.to_dict() for r in roles]


@router.get("/roles/{role_id}", response_model=dict)
async def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get a specific role with its permissions"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    result = role.to_dict()
    result["permissions"] = [p.to_dict() for p in role.permissions]
    return result


@router.post("/roles", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_role(
    name: str,
    description: Optional[str] = None,
    permission_ids: Optional[List[int]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new role with optional permissions"""
    # Check if role already exists
    existing = db.query(Role).filter(Role.name == name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role with this name already exists"
        )
    
    role = Role(
        name=name,
        description=description
    )
    
    if permission_ids:
        permissions = db.query(Permission).filter(
            Permission.id.in_(permission_ids),
            Permission.is_active == True
        ).all()
        role.permissions = permissions
    
    db.add(role)
    db.commit()
    db.refresh(role)
    
    log_audit_event(
        db=db,
        user_id=current_user.id,
        action="create_role",
        resource="role",
        resource_id=str(role.id),
        details={"name": name, "permission_count": len(permission_ids or [])}
    )
    
    return role.to_dict()


@router.put("/roles/{role_id}", response_model=dict)
async def update_role(
    role_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    permission_ids: Optional[List[int]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update a role"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    updates = {}
    if name is not None:
        # Check for duplicate name
        existing = db.query(Role).filter(
            and_(Role.name == name, Role.id != role_id)
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role with this name already exists"
            )
        role.name = name
        updates["name"] = name
    
    if description is not None:
        role.description = description
        updates["description"] = description
    
    if permission_ids is not None:
        permissions = db.query(Permission).filter(
            Permission.id.in_(permission_ids),
            Permission.is_active == True
        ).all()
        role.permissions = permissions
        updates["permission_ids"] = permission_ids
    
    role.updated_at = datetime.now(timezone.utc).isoformat()
    db.commit()
    db.refresh(role)
    
    log_audit_event(
        db=db,
        user_id=current_user.id,
        action="update_role",
        resource="role",
        resource_id=str(role_id),
        details=updates
    )
    
    return role.to_dict()


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete a role (soft delete by deactivating)"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Prevent deleting admin role
    if role.name == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete admin role"
        )
    
    role.is_active = False
    db.commit()
    
    log_audit_event(
        db=db,
        user_id=current_user.id,
        action="delete_role",
        resource="role",
        resource_id=str(role_id)
    )


@router.post("/roles/{role_id}/permissions", response_model=dict)
async def assign_permissions_to_role(
    role_id: int,
    permission_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Assign permissions to a role"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    permissions = db.query(Permission).filter(
        Permission.id.in_(permission_ids),
        Permission.is_active == True
    ).all()
    
    # Add permissions without duplicates
    current_perm_ids = {p.id for p in role.permissions}
    for perm in permissions:
        if perm.id not in current_perm_ids:
            role.permissions.append(perm)
    
    db.commit()
    db.refresh(role)
    
    log_audit_event(
        db=db,
        user_id=current_user.id,
        action="assign_permissions",
        resource="role",
        resource_id=str(role_id),
        details={"permission_ids": permission_ids}
    )
    
    return role.to_dict()


@router.delete("/roles/{role_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_permission_from_role(
    role_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Remove a permission from a role"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    
    if permission in role.permissions:
        role.permissions.remove(permission)
        db.commit()
    
    log_audit_event(
        db=db,
        user_id=current_user.id,
        action="remove_permission",
        resource="role",
        resource_id=str(role_id),
        details={"permission_id": permission_id}
    )


# ============ User Role Management ============

@router.get("/users/{user_id}/roles", response_model=List[dict])
async def get_user_roles(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get roles assigned to a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return [role.to_dict() for role in user.roles]


@router.post("/users/{user_id}/roles", response_model=List[dict])
async def assign_roles_to_user(
    user_id: int,
    role_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Assign roles to a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    roles = db.query(Role).filter(
        Role.id.in_(role_ids),
        Role.is_active == True
    ).all()
    
    # Add roles without duplicates
    current_role_ids = {r.id for r in user.roles}
    for role in roles:
        if role.id not in current_role_ids:
            user.roles.append(role)
    
    db.commit()
    db.refresh(user)
    
    log_audit_event(
        db=db,
        user_id=current_user.id,
        action="assign_roles",
        resource="user",
        resource_id=str(user_id),
        details={"role_ids": role_ids}
    )
    
    return [role.to_dict() for role in user.roles]


@router.delete("/users/{user_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_role_from_user(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Remove a role from a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    if role in user.roles:
        user.roles.remove(role)
        db.commit()
    
    log_audit_event(
        db=db,
        user_id=current_user.id,
        action="remove_role",
        resource="user",
        resource_id=str(user_id),
        details={"role_id": role_id}
    )


# ============ Seed Default Roles ============

@router.post("/seed", status_code=status.HTTP_201_CREATED)
async def seed_default_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Seed default roles and permissions"""
    results = {"roles_created": 0, "permissions_created": 0, "errors": []}
    
    # Create permissions
    for perm_data in DEFAULT_PERMISSIONS:
        existing = db.query(Permission).filter(
            Permission.name == perm_data["name"]
        ).first()
        if not existing:
            permission = Permission(**perm_data)
            db.add(permission)
            results["permissions_created"] += 1
    
    db.commit()
    
    # Create roles with permissions
    for role_data in DEFAULT_ROLES:
        existing = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing:
            perm_names = role_data.pop("permissions", [])
            role = Role(**role_data)
            
            # Get permission objects by name
            permissions = db.query(Permission).filter(
                Permission.name.in_(perm_names),
                Permission.is_active == True
            ).all()
            role.permissions = permissions
            
            db.add(role)
            results["roles_created"] += 1
    
    db.commit()
    
    log_audit_event(
        db=db,
        user_id=current_user.id,
        action="seed_rbac",
        resource="rbac",
        details=results
    )
    
    return results


# ============ Current User Info ============

@router.get("/me/permissions", response_model=List[str])
async def get_my_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's permissions"""
    permissions = get_user_permissions(db, current_user)
    return sorted(list(permissions))


@router.get("/me/roles", response_model=List[str])
async def get_my_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's roles"""
    return [role.name for role in current_user.roles]


# ============ Audit Logs ============

@router.get("/audit", response_model=List[dict])
async def list_audit_logs(
    user_id: Optional[int] = Query(None, description="Filter by user"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource: Optional[str] = Query(None, description="Filter by resource"),
    limit: int = Query(100, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List audit logs"""
    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource:
        query = query.filter(AuditLog.resource == resource)
    
    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    return [log.to_dict() for log in logs]
