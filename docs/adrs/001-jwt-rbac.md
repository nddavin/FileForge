# ADR-001: JWT-Based Authentication with RBAC

| ADR ID | Title | Status |
|--------|-------|--------|
| 001 | JWT-Based Authentication with RBAC | Accepted |

## Context

FileForge needs a secure, scalable authentication system for church organizations. We evaluated several approaches:

1. **Session-based auth** (traditional cookies)
2. **OAuth2/OpenID Connect** (external providers)
3. **JWT with custom RBAC** (our solution)

## Decision

We chose **JWT tokens with Role-Based Access Control (RBAC)** as our authentication mechanism.

### Token Structure

```json
{
  "sub": "user_id",
  "email": "user@church.org",
  "role": "manager",
  "permissions": ["files:read", "files:write", "sermons:read"],
  "org_id": "church_123",
  "exp": 1234567890,
  "iat": 1234567890,
  "jti": "unique-token-id"
}
```

### RBAC Model

| Role | Description | Permissions |
|------|-------------|-------------|
| `admin` | Full system access | All permissions |
| `manager` | Team oversight | files:*, sermons:*, tasks:assign |
| `user` | Standard user | files:own, sermons:read, tasks:claim |
| `viewer` | Read-only | sermons:read |

## Consequences

### Positive

- **Stateless**: No session storage needed, scales horizontally
- **Performance**: Token validation is fast, no DB lookup required
- **Flexibility**: Embed user info and permissions in token
- **Security**: Short-lived access tokens (30 min) with refresh tokens

### Negative

- **Token revocation**: No immediate logout (requires token expiry or blocklist)
- **Token size**: Large tokens increase request size
- **Complexity**: More complex token management than sessions

## Implementation

### Token Generation

```python
from datetime import datetime, timedelta
from jose import jwt

def create_access_token(user: User) -> str:
    expiry = datetime.utcnow() + timedelta(minutes=30)
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "permissions": get_permissions(user.role),
        "org_id": user.org_id,
        "exp": expiry,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4())
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
```

### Token Validation

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        user_id = payload["sub"]
        user = await get_user(user_id)
        if not user:
            raise HTTPException(status_code=401)
        return user
    except jwt.JWTError:
        raise HTTPException(status_code=401)
```

### Permission Checker

```python
from functools import wraps

def require_permission(permission: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get("current_user")
            if permission not in user.permissions:
                raise HTTPException(status_code=403)
            return await func(*args, **kwargs)
        return wrapper
    return decorator

@router.get("/files")
@require_permission("files:read")
async def list_files(current_user: User = Depends(get_current_user)):
    return await get_files(user=current_user)
```

## Refresh Token Strategy

| Token Type | Lifetime | Storage | Purpose |
|------------|----------|---------|---------|
| Access Token | 30 min | Memory | API authentication |
| Refresh Token | 7 days | HTTP-only cookie | Session persistence |

```python
@router.post("/refresh")
async def refresh_token(refresh_token: str = Cookie(...)):
    payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY)
    if payload["type"] != "refresh":
        raise HTTPException(status_code=401)
    return {
        "access_token": create_access_token(user),
        "token_type": "bearer"
    }
```

## Date

2024-01-15
