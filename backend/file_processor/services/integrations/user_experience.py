"""User Experience Services - Sharing, Versioning, and Collaboration Backend"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
import hashlib
import hmac
import secrets
import threading
import uuid
import logging

logger = logging.getLogger(__name__)


class SharePermission(Enum):
    """Share permission levels"""
    VIEW = "view"
    DOWNLOAD = "download"
    EDIT = "edit"
    ADMIN = "admin"


class ShareLinkStatus(Enum):
    """Status of a share link"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    MAX_VIEWS_REACHED = "max_views_reached"


@dataclass
class ShareLinkConfig:
    """Configuration for a share link"""
    file_id: str
    permission: SharePermission = SharePermission.VIEW
    expires_at: Optional[str] = None
    password_protected: bool = False
    password_hash: Optional[str] = None
    max_views: Optional[int] = None
    current_views: int = 0
    allow_download: bool = True
    allow_print: bool = False
    watermark_enabled: bool = False
    notify_on_access: bool = False
    access_notifications: List[str] = field(default_factory=list)
    created_by: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_accessed_at: Optional[str] = None
    status: ShareLinkStatus = ShareLinkStatus.ACTIVE
    
    def is_expired(self) -> bool:
        """Check if link is expired"""
        if not self.expires_at:
            return False
        return datetime.fromisoformat(self.expires_at) < datetime.now(timezone.utc)
    
    def can_access(self) -> tuple[bool, str]:
        """Check if link can be accessed"""
        if self.status != ShareLinkStatus.ACTIVE:
            return False, f"Link is {self.status.value}"
        
        if self.is_expired():
            self.status = ShareLinkStatus.EXPIRED
            return False, "Link has expired"
        
        if self.max_views and self.current_views >= self.max_views:
            self.status = ShareLinkStatus.MAX_VIEWS_REACHED
            return False, "Maximum views reached"
        
        return True, "OK"
    
    def record_access(self, ip_address: Optional[str] = None):
        """Record an access to the link"""
        self.current_views += 1
        self.last_accessed_at = datetime.now(timezone.utc).isoformat()
        
        if self.max_views and self.current_views >= self.max_views:
            self.status = ShareLinkStatus.MAX_VIEWS_REACHED


@dataclass
class FileVersion:
    """File version information"""
    version_id: str
    file_id: str
    version_number: int
    content_hash: str
    size_bytes: int
    created_by: str
    created_at: str
    change_description: str = ""
    parent_version_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "version_id": self.version_id,
            "file_id": self.file_id,
            "version_number": self.version_number,
            "content_hash": self.content_hash,
            "size_bytes": self.size_bytes,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "change_description": self.change_description,
            "parent_version_id": self.parent_version_id,
            "metadata": self.metadata
        }


@dataclass
class Comment:
    """File comment"""
    comment_id: str
    file_id: str
    user_id: str
    content: str
    created_at: str
    updated_at: Optional[str] = None
    parent_comment_id: Optional[str] = None
    anchor_position: Optional[Dict[str, Any]] = None  # For inline comments
    mentions: List[str] = field(default_factory=list)
    reactions: Dict[str, List[str]] = field(default_factory=dict)  # emoji -> user_ids
    is_resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "comment_id": self.comment_id,
            "file_id": self.file_id,
            "user_id": self.user_id,
            "content": self.content,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "parent_comment_id": self.parent_comment_id,
            "anchor_position": self.anchor_position,
            "mentions": self.mentions,
            "reactions": self.reactions,
            "is_resolved": self.is_resolved,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at
        }


@dataclass
class CollaborationSession:
    """Real-time collaboration session"""
    session_id: str
    file_id: str
    created_by: str
    created_at: str
    participants: List[str] = field(default_factory=list)
    cursors: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    selections: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    is_active: bool = True
    
    def add_participant(self, user_id: str):
        """Add participant to session"""
        if user_id not in self.participants:
            self.participants.append(user_id)
    
    def remove_participant(self, user_id: str):
        """Remove participant from session"""
        if user_id in self.participants:
            self.participants.remove(user_id)
        if user_id in self.cursors:
            del self.cursors[user_id]
        if user_id in self.selections:
            del self.selections[user_id]
    
    def update_cursor(self, user_id: str, position: Dict[str, Any]):
        """Update user cursor position"""
        self.cursors[user_id] = position
    
    def update_selection(self, user_id: str, selection: Dict[str, Any]):
        """Update user selection"""
        self.selections[user_id] = selection


class SharingService:
    """Service for managing share links"""
    
    def __init__(self, secret_key: str = None):
        self._secret_key = secret_key or secrets.token_hex(32)
        self._share_links: Dict[str, ShareLinkConfig] = {}
        self._access_history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
    
    def create_share_link(
        self,
        file_id: str,
        created_by: str,
        permission: SharePermission = SharePermission.VIEW,
        expires_at: Optional[str] = None,
        password: Optional[str] = None,
        max_views: Optional[int] = None,
        **kwargs
    ) -> tuple[str, str]:
        """Create a new share link"""
        link_id = secrets.token_urlsafe(16)
        access_token = secrets.token_urlsafe(24)
        
        config = ShareLinkConfig(
            file_id=file_id,
            permission=permission,
            expires_at=expires_at,
            password_protected=bool(password),
            password_hash=self._hash_password(password) if password else None,
            max_views=max_views,
            created_by=created_by,
            **kwargs
        )
        
        with self._lock:
            self._share_links[link_id] = config
        
        logger.info(f"Created share link {link_id} for file {file_id}")
        return link_id, access_token
    
    def validate_share_link(
        self,
        link_id: str,
        password: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate and access a share link"""
        with self._lock:
            if link_id not in self._share_links:
                return {"valid": False, "error": "Link not found"}
            
            config = self._share_links[link_id]
            can_access, reason = config.can_access()
            
            if not can_access:
                return {"valid": False, "error": reason}
            
            if config.password_protected:
                if not password:
                    return {"valid": False, "error": "Password required", "password_required": True}
                if not self._verify_password(password, config.password_hash):
                    return {"valid": False, "error": "Invalid password"}
            
            # Record access
            config.record_access(ip_address)
            
            # Log access
            self._access_history.append({
                "link_id": link_id,
                "file_id": config.file_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "ip_address": ip_address
            })
            
            # Notify if configured
            if config.notify_on_access:
                for email in config.access_notifications:
                    self._send_notification(email, "access", link_id)
            
            return {
                "valid": True,
                "file_id": config.file_id,
                "permission": config.permission.value,
                "allow_download": config.allow_download,
                "allow_print": config.allow_print,
                "watermark_enabled": config.watermark_enabled,
                "expires_at": config.expires_at,
                "remaining_views": (
                    config.max_views - config.current_views
                    if config.max_views else None
                )
            }
    
    def revoke_share_link(self, link_id: str, reason: str = "Revoked by owner") -> bool:
        """Revoke a share link"""
        with self._lock:
            if link_id not in self._share_links:
                return False
            
            config = self._share_links[link_id]
            config.status = ShareLinkStatus.REVOKED
            
            self._access_history.append({
                "link_id": link_id,
                "action": "revoke",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "reason": reason
            })
            
            return True
    
    def get_share_link_stats(self, link_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a share link"""
        with self._lock:
            if link_id not in self._share_links:
                return None
            
            config = self._share_links[link_id]
            return {
                "file_id": config.file_id,
                "status": config.status.value,
                "created_by": config.created_by,
                "created_at": config.created_at,
                "last_accessed": config.last_accessed_at,
                "total_views": config.current_views,
                "max_views": config.max_views,
                "expires_at": config.expires_at,
                "password_protected": config.password_protected
            }
    
    def list_share_links(self, file_id: str) -> List[Dict[str, Any]]:
        """List all share links for a file"""
        with self._lock:
            return [
                {
                    "link_id": link_id,
                    "status": config.status.value,
                    "permission": config.permission.value,
                    "created_at": config.created_at,
                    "views": config.current_views
                }
                for link_id, config in self._share_links.items()
                if config.file_id == file_id
            ]
    
    def _hash_password(self, password: str) -> str:
        """Hash a password"""
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            self._secret_key.encode(),
            100000
        ).hex()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against hash"""
        return hmac.compare_digest(
            self._hash_password(password),
            password_hash
        )
    
    def _send_notification(self, email: str, event: str, link_id: str):
        """Send notification (placeholder)"""
        logger.info(f"Notification: {event} on link {link_id} to {email}")


class VersioningService:
    """Service for file version control"""
    
    def __init__(self, storage_path: str = "/tmp/versions"):
        self._versions: Dict[str, List[FileVersion]] = {}
        self._lock = threading.Lock()
    
    def create_version(
        self,
        file_id: str,
        content_hash: str,
        size_bytes: int,
        created_by: str,
        change_description: str = "",
        parent_version_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FileVersion:
        """Create a new version of a file"""
        version_id = str(uuid.uuid4())
        
        with self._lock:
            # Get next version number
            versions = self._versions.get(file_id, [])
            version_number = len(versions) + 1
            
            version = FileVersion(
                version_id=version_id,
                file_id=file_id,
                version_number=version_number,
                content_hash=content_hash,
                size_bytes=size_bytes,
                created_by=created_by,
                created_at=datetime.now(timezone.utc).isoformat(),
                change_description=change_description,
                parent_version_id=parent_version_id,
                metadata=metadata or {}
            )
            
            if file_id not in self._versions:
                self._versions[file_id] = []
            self._versions[file_id].append(version)
        
        logger.info(f"Created version {version_number} for file {file_id}")
        return version
    
    def get_versions(self, file_id: str) -> List[FileVersion]:
        """Get all versions of a file"""
        with self._lock:
            return list(self._versions.get(file_id, []))
    
    def get_version(self, file_id: str, version_number: int) -> Optional[FileVersion]:
        """Get a specific version"""
        with self._lock:
            versions = self._versions.get(file_id, [])
            for v in versions:
                if v.version_number == version_number:
                    return v
            return None
    
    def get_latest_version(self, file_id: str) -> Optional[FileVersion]:
        """Get the latest version of a file"""
        with self._lock:
            versions = self._versions.get(file_id, [])
            return versions[-1] if versions else None
    
    def rollback(
        self,
        file_id: str,
        version_number: int,
        user_id: str
    ) -> Dict[str, Any]:
        """Rollback to a specific version"""
        version = self.get_version(file_id, version_number)
        
        if not version:
            return {"success": False, "error": "Version not found"}
        
        # Create a new version that copies the old content
        new_version = self.create_version(
            file_id=file_id,
            content_hash=version.content_hash,
            size_bytes=version.size_bytes,
            created_by=user_id,
            change_description=f"Rollback to version {version_number}",
            parent_version_id=version.version_id
        )
        
        return {
            "success": True,
            "new_version": new_version.version_number,
            "rolled_back_from": version_number
        }
    
    def compare_versions(
        self,
        file_id: str,
        version_a: int,
        version_b: int
    ) -> Dict[str, Any]:
        """Compare two versions"""
        v_a = self.get_version(file_id, version_a)
        v_b = self.get_version(file_id, version_b)
        
        if not v_a or not v_b:
            return {"success": False, "error": "Version not found"}
        
        return {
            "success": True,
            "version_a": v_a.to_dict(),
            "version_b": v_b.to_dict(),
            "content_changed": v_a.content_hash != v_b.content_hash,
            "size_diff": v_b.size_bytes - v_a.size_bytes
        }
    
    def delete_old_versions(self, file_id: str, keep_count: int = 10) -> int:
        """Delete old versions, keeping the most recent"""
        with self._lock:
            versions = self._versions.get(file_id, [])
            if len(versions) <= keep_count:
                return 0
            
            to_delete = versions[:-keep_count]
            self._versions[file_id] = versions[-keep_count:]
            
            logger.info(f"Deleted {len(to_delete)} old versions for file {file_id}")
            return len(to_delete)


class CollaborationService:
    """Service for real-time collaboration"""
    
    def __init__(self):
        self._sessions: Dict[str, CollaborationSession] = {}
        self._comments: Dict[str, List[Comment]] = {}
        self._lock = threading.Lock()
        self._callbacks: Dict[str, List[Callable]] = {}
    
    def create_session(
        self,
        file_id: str,
        created_by: str
    ) -> CollaborationSession:
        """Create a new collaboration session"""
        session = CollaborationSession(
            session_id=str(uuid.uuid4()),
            file_id=file_id,
            created_by=created_by,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        with self._lock:
            self._sessions[session.session_id] = session
        
        logger.info(f"Created collaboration session {session.session_id}")
        return session
    
    def join_session(self, session_id: str, user_id: str) -> Optional[CollaborationSession]:
        """Join an existing session"""
        with self._lock:
            if session_id not in self._sessions:
                return None
            
            session = self._sessions[session_id]
            session.add_participant(user_id)
            
            # Notify other participants
            self._notify_participants(session_id, "user_joined", {"user_id": user_id})
            
            return session
    
    def leave_session(self, session_id: str, user_id: str):
        """Leave a session"""
        with self._lock:
            if session_id not in self._sessions:
                return
            
            session = self._sessions[session_id]
            session.remove_participant(user_id)
            
            # Notify other participants
            self._notify_participants(session_id, "user_left", {"user_id": user_id})
            
            # Clean up empty sessions
            if not session.participants:
                del self._sessions[session_id]
    
    def update_cursor(self, session_id: str, user_id: str, position: Dict[str, Any]):
        """Update cursor position for a user"""
        with self._lock:
            if session_id not in self._sessions:
                return
            
            session = self._sessions[session_id]
            session.update_cursor(user_id, position)
            
            self._notify_participants(
                session_id,
                "cursor_update",
                {"user_id": user_id, "position": position}
            )
    
    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the current state of a session"""
        with self._lock:
            if session_id not in self._sessions:
                return None
            
            session = self._sessions[session_id]
            return {
                "session_id": session.session_id,
                "file_id": session.file_id,
                "participants": session.participants,
                "cursors": session.cursors,
                "selections": session.selections,
                "is_active": session.is_active
            }
    
    # ========== Comments ==========
    
    def add_comment(
        self,
        file_id: str,
        user_id: str,
        content: str,
        parent_comment_id: Optional[str] = None,
        anchor_position: Optional[Dict[str, Any]] = None,
        mentions: Optional[List[str]] = None
    ) -> Comment:
        """Add a comment to a file"""
        comment = Comment(
            comment_id=str(uuid.uuid4()),
            file_id=file_id,
            user_id=user_id,
            content=content,
            created_at=datetime.now(timezone.utc).isoformat(),
            parent_comment_id=parent_comment_id,
            anchor_position=anchor_position,
            mentions=mentions or []
        )
        
        with self._lock:
            if file_id not in self._comments:
                self._comments[file_id] = []
            self._comments[file_id].append(comment)
        
        # Notify mentioned users
        for mentioned_user in comment.mentions:
            self._notify_participants(
                file_id,
                "mention",
                {"user_id": mentioned_user, "comment_id": comment.comment_id}
            )
        
        return comment
    
    def get_comments(
        self,
        file_id: str,
        include_resolved: bool = False
    ) -> List[Comment]:
        """Get all comments for a file"""
        with self._lock:
            comments = self._comments.get(file_id, [])
            
            if not include_resolved:
                comments = [c for c in comments if not c.is_resolved]
            
            return sorted(comments, key=lambda c: c.created_at)
    
    def resolve_comment(self, comment_id: str, user_id: str) -> bool:
        """Resolve a comment"""
        with self._lock:
            for comments in self._comments.values():
                for comment in comments:
                    if comment.comment_id == comment_id:
                        comment.is_resolved = True
                        comment.resolved_by = user_id
                        comment.resolved_at = datetime.now(timezone.utc).isoformat()
                        return True
            return False
    
    def add_reaction(
        self,
        comment_id: str,
        user_id: str,
        emoji: str
    ) -> bool:
        """Add a reaction to a comment"""
        with self._lock:
            for comments in self._comments.values():
                for comment in comments:
                    if comment.comment_id == comment_id:
                        if emoji not in comment.reactions:
                            comment.reactions[emoji] = []
                        if user_id not in comment.reactions[emoji]:
                            comment.reactions[emoji].append(user_id)
                        return True
            return False
    
    def remove_reaction(
        self,
        comment_id: str,
        user_id: str,
        emoji: str
    ) -> bool:
        """Remove a reaction from a comment"""
        with self._lock:
            for comments in self._comments.values():
                for comment in comments:
                    if comment.comment_id == comment_id:
                        if emoji in comment.reactions and user_id in comment.reactions[emoji]:
                            comment.reactions[emoji].remove(user_id)
                            if not comment.reactions[emoji]:
                                del comment.reactions[emoji]
                            return True
            return False
    
    # ========== Callbacks ==========
    
    def register_callback(self, event: str, callback: Callable):
        """Register callback for collaboration events"""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)
    
    def _notify_participants(self, session_id: str, event: str, data: Dict[str, Any]):
        """Notify callbacks of an event"""
        for callback in self._callbacks.get(event, []):
            try:
                callback(session_id, data)
            except Exception as e:
                logger.error(f"Collaboration callback failed: {e}")
    
    def get_collaboration_stats(self, file_id: str) -> Dict[str, Any]:
        """Get collaboration statistics for a file"""
        with self._lock:
            comments = self._comments.get(file_id, [])
            active_sessions = [
                s for s in self._sessions.values()
                if s.file_id == file_id and s.is_active
            ]
            
            return {
                "total_comments": len(comments),
                "resolved_comments": sum(1 for c in comments if c.is_resolved),
                "active_sessions": len(active_sessions),
                "total_participants": len(set(c.user_id for c in comments)),
                "recent_activities": [
                    {"type": "comment", "user_id": c.user_id, "time": c.created_at}
                    for c in sorted(comments, key=lambda x: x.created_at, reverse=True)[:5]
                ]
            }
