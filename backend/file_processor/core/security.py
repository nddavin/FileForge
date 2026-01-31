from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        return None


# RBAC functions
def check_permission(user_roles: list[str], required_role: str) -> bool:
    # Simple role check, can be extended
    return required_role in user_roles


def require_role(allowed_roles: list[str]):
    """
    Dependency factory for role-based access control.
    
    Args:
        allowed_roles: List of roles that are allowed to access the endpoint
        
    Returns:
        A dependency function that checks if the user has one of the allowed roles
        
    Example:
        @router.get("/admin-only")
        async def admin_endpoint(user=Depends(require_role(["admin"]))):
            return {"message": "Hello admin!"}
    """
    from fastapi import HTTPException, status
    
    def role_checker(user=None):
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Handle different user object structures
        user_roles = []
        if hasattr(user, 'roles'):
            user_roles = user.roles
        elif isinstance(user, dict) and 'roles' in user:
            user_roles = user['roles']
        
        # Normalize roles to strings
        normalized_roles = []
        for role in user_roles:
            if isinstance(role, str):
                normalized_roles.append(role)
            elif isinstance(role, dict) and 'name' in role:
                normalized_roles.append(role['name'])
        
        # Check if user has any of the allowed roles
        has_permission = any(role in allowed_roles for role in normalized_roles)
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {allowed_roles}"
            )
        
        return user
    
    return role_checker
