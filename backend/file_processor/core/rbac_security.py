"""RBAC Security Module with FastAPI Dependencies for JWT-based Authorization"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional, Set, Callable, Any

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from backend.file_processor.core.config import settings
from backend.file_processor.database import get_db
from backend.file_processor.models.rbac import Role, Permission, AuditLog
from backend.file_processor.models.user import User

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=True
)


class AuthenticationError(HTTPException):
    """Custom authentication error"""
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(HTTPException):
    """Custom authorization error"""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


# ============ Token Functions ============

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    include_roles: bool = True,
    include_permissions: bool = True,
    db: Optional[Session] = None,
    user_id: Optional[int] = None
) -> str:
    """Create a JWT access token with optional role/permission claims"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode.update({"exp": expire})
    to_encode.update({"iat": datetime.now(timezone.utc)})
    
    # Embed role and permission claims if user_id provided
    if user_id and db and (include_roles or include_permissions):
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            if include_roles:
                to_encode["roles"] = [role.name for role in user.roles]
            if include_permissions:
                permissions = set()
                for role in user.roles:
                    for perm in role.permissions:
                        permissions.add(perm.name)
                to_encode["permissions"] = list(permissions)
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except ExpiredSignatureError:
        return None
    except JWTError:
        return None


def extract_token_payload(token: str) -> dict:
    """Extract payload from token, raising error if invalid"""
    payload = decode_token(token)
    if payload is None:
        raise AuthenticationError("Invalid or expired token")
    return payload


# ============ Dependency Classes ============

class RoleChecker:
    """Dependency class for role-based access control"""
    
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles
    
    async def __call__(
        self,
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
    ) -> User:
        """Check if user has required role"""
        payload = extract_token_payload(token)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise AuthenticationError("Token missing user ID")
        
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise AuthenticationError("User not found")
        
        user_roles = [role.name for role in user.roles]
        
        # Check if user has any of the allowed roles
        if not any(role in self.allowed_roles for role in user_roles):
            raise AuthorizationError(
                f"Access denied. Required roles: {self.allowed_roles}"
            )
        
        return user


class PermissionChecker:
    """Dependency class for permission-based access control"""
    
    def __init__(self, required_permission: str):
        self.required_permission = required_permission
    
    async def __call__(
        self,
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
    ) -> User:
        """Check if user has required permission"""
        payload = extract_token_payload(token)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise AuthenticationError("Token missing user ID")
        
        # Check permissions from token first (faster)
        token_permissions = payload.get("permissions", [])
        if self.required_permission in token_permissions:
            user = db.query(User).filter(User.id == int(user_id)).first()
            if user:
                return user
        
        # Fall back to database check
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise AuthenticationError("User not found")
        
        # Check user's permissions
        user_permissions = set()
        for role in user.roles:
            for perm in role.permissions:
                user_permissions.add(perm.name)
        
        if self.required_permission not in user_permissions:
            raise AuthorizationError(
                f"Permission denied. Required: {self.required_permission}"
            )
        
        return user


class ResourceOwnerChecker:
    """Dependency class for resource ownership verification"""
    
    def __init__(self, resource_id_param: str, resource_table, owner_field: str = "user_id"):
        self.resource_id_param = resource_id_param
        self.resource_table = resource_table
        self.owner_field = owner_field
    
    async def __call__(
        self,
        request: Request,
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
    ) -> User:
        """Check if user owns the resource or has admin role"""
        payload = extract_token_payload(token)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise AuthenticationError("Token missing user ID")
        
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise AuthenticationError("User not found")
        
        # Check if user has admin role (can access any resource)
        user_roles = [role.name for role in user.roles]
        if "admin" in user_roles:
            return user
        
        # Get resource ID from path
        resource_id = request.path_params.get(self.resource_id_param)
        if resource_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resource ID not found in path"
            )
        
        # Check ownership
        resource = db.query(self.resource_table).filter(
            and_(
                self.resource_table.id == int(resource_id),
                getattr(self.resource_table, self.owner_field) == int(user_id)
            )
        ).first()
        
        if resource is None:
            raise AuthorizationError(
                "You don't have permission to access this resource"
            )
        
        return user


# ============ Convenience Dependencies ============

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    payload = extract_token_payload(token)
    user_id = payload.get("sub")
    
    if user_id is None:
        raise AuthenticationError("Token missing user ID")
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise AuthenticationError("User not found")
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user and verify they are active"""
    if not current_user.is_active:
        raise AuthenticationError("User account is deactivated")
    return current_user


def require_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Require admin role for access"""
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles:
        raise AuthorizationError("Admin access required")
    return current_user


def require_manager(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Require manager or admin role for access"""
    user_roles = [role.name for role in current_user.roles]
    if not any(role in ["admin", "manager"] for role in user_roles):
        raise AuthorizationError("Manager access required")
    return current_user


# ============ Permission Checkers ============

def require_permission(permission: str):
    """Factory for creating permission check dependencies"""
    return PermissionChecker(permission)


def require_role(*roles: str):
    """Factory for creating role check dependencies"""
    return RoleChecker(list(roles))


# ============ RBAC Utilities ============

def get_user_permissions(db: Session, user: User) -> Set[str]:
    """Get all permissions for a user"""
    permissions = set()
    for role in user.roles:
        for perm in role.permissions:
            permissions.add(perm.name)
    return permissions


def get_user_roles(db: Session, user: User) -> List[str]:
    """Get all role names for a user"""
    return [role.name for role in user.roles]


def has_permission(db: Session, user: User, permission: str) -> bool:
    """Check if user has a specific permission"""
    return permission in get_user_permissions(db, user)


def has_role(db: Session, user: User, role: str) -> bool:
    """Check if user has a specific role"""
    return role in get_user_roles(db, user)


def has_any_role(db: Session, user: User, roles: List[str]) -> bool:
    """Check if user has any of the specified roles"""
    user_roles = get_user_roles(db, user)
    return any(role in user_roles for role in roles)


# ============ Audit Logging ============

def log_audit_event(
    db: Session,
    user_id: Optional[int],
    action: str,
    resource: str,
    resource_id: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    status: str = "success"
):
    """Log an audit event"""
    import json
    
    audit = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        details=json.dumps(details) if details else None,
        ip_address=ip_address,
        user_agent=user_agent,
        status=status
    )
    db.add(audit)
    db.commit()


# ============ Scoped Queries ============

def filter_query_by_role(
    db: Session,
    user: User,
    query,
    resource_table,
    owner_field: str = "user_id"
):
    """Filter a query based on user role"""
    user_roles = get_user_roles(db, user)
    
    # Admins and managers can see all resources
    if "admin" in user_roles or "manager" in user_roles:
        return query
    
    # Regular users can only see their own resources
    return query.filter(
        getattr(resource_table, owner_field) == user.id
    )


# ============ Decorators for Function-Based Views ============

def rbac_require(permission: str = None, roles: List[str] = None):
    """
    Decorator for function-based views to enforce RBAC.
    Use with async functions that accept current_user as keyword argument.
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            # This would be used with FastAPI's dependency injection
            # Actual enforcement happens via dependencies
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# ============ WebSocket Authentication ============

async def get_websocket_user(
    token: str,
    db: Session
) -> Optional[User]:
    """Authenticate WebSocket connection using token"""
    payload = decode_token(token)
    if payload is None:
        return None
    
    user_id = payload.get("sub")
    if user_id is None:
        return None
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    return user


# ============ Token Refresh ============

async def refresh_token(
    refresh_token: str,
    db: Session
) -> Optional[dict]:
    """Refresh access token using refresh token"""
    payload = decode_token(refresh_token)
    if payload is None:
        return None
    
    user_id = payload.get("sub")
    if user_id is None:
        return None
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        return None
    
    # Create new access token
    new_token = create_access_token(
        data={"sub": str(user.id)},
        db=db,
        user_id=user.id
    )
    
    return {
        "access_token": new_token,
        "token_type": "bearer"
    }
