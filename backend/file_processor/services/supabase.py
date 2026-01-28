"""Supabase Integration Service for Auth, Database, Storage, and Realtime"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from contextlib import asynccontextmanager

import httpx
from supabase import create_client, Client
from supabase.lib.client_options import SyncClientOptions
from supabase import AsyncClient

from backend.file_processor.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SupabaseConfig:
    """Supabase configuration"""

    url: str
    anon_key: str
    service_role_key: Optional[str] = None
    jwt_secret: Optional[str] = None


@dataclass
class UserMetadata:
    """User metadata from Supabase"""

    id: str
    email: str
    role: str
    app_metadata: Dict[str, Any]
    user_metadata: Dict[str, Any]
    created_at: str


@dataclass
class StorageFile:
    """File info from Supabase Storage"""

    name: str
    id: str
    updated_at: str
    created_at: str
    last_accessed_at: str
    metadata: Dict[str, Any]


class SupabaseAuthService:
    """Supabase Authentication Service"""

    def __init__(self, config: SupabaseConfig):
        self.config = config
        self._client: Optional[Client] = None
        self._async_client: Optional[AsyncClient] = None

    def _get_client_options(self) -> SyncClientOptions:
        """Get client options for Supabase"""
        return SyncClientOptions(
            auto_refresh_token=True, persist_session=True, detect_session_in_url=True
        )

    @property
    def client(self) -> Client:
        """Get synchronous client (lazy initialization)"""
        if self._client is None:
            self._client = create_client(
                self.config.url,
                self.config.anon_key,
                options=self._get_client_options(),
            )
        return self._client

    @asynccontextmanager
    async def get_async_client(self):
        """Get async client for async operations"""
        if self._async_client is None:
            self._async_client = create_client(
                self.config.url,
                self.config.anon_key,
                options=SyncClientOptions(auto_refresh_token=False),
            )
        yield self._async_client

    def sign_up(
        self, email: str, password: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Sign up a new user"""
        try:
            result = self.client.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {"data": metadata or {}},
                }
            )
            return {"success": True, "user": result.user, "session": result.session}
        except Exception as e:
            logger.error(f"Supabase sign up failed: {e}")
            return {"success": False, "error": str(e)}

    def sign_in_with_password(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in with email and password"""
        try:
            result = self.client.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            return {"success": True, "user": result.user, "session": result.session}
        except Exception as e:
            logger.error(f"Supabase sign in failed: {e}")
            return {"success": False, "error": str(e)}

    def sign_in_with_oauth(
        self, provider: str, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Sign in with OAuth provider"""
        try:
            result = self.client.auth.sign_in_with_oauth(
                {"provider": provider, "options": options or {}}
            )
            return {"success": True, "url": result.url}
        except Exception as e:
            logger.error(f"Supabase OAuth failed: {e}")
            return {"success": False, "error": str(e)}

    def sign_out(self) -> Dict[str, Any]:
        """Sign out current user"""
        try:
            self.client.auth.sign_out()
            return {"success": True}
        except Exception as e:
            logger.error(f"Supabase sign out failed: {e}")
            return {"success": False, "error": str(e)}

    def get_user(self, token: str) -> Dict[str, Any]:
        """Get user from token"""
        try:
            result = self.client.auth.get_user(token)
            return {"success": True, "user": result.user}
        except Exception as e:
            logger.error(f"Supabase get user failed: {e}")
            return {"success": False, "error": str(e)}

    def get_session(self) -> Dict[str, Any]:
        """Get current session"""
        try:
            session = self.client.auth.get_session()
            return {"success": True, "session": session}
        except Exception as e:
            logger.error(f"Supabase get session failed: {e}")
            return {"success": False, "error": str(e)}

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token"""
        try:
            result = self.client.auth.refresh_session(refresh_token)
            return {
                "success": True,
                "access_token": result.session.access_token,
                "refresh_token": result.session.refresh_token,
            }
        except Exception as e:
            logger.error(f"Supabase token refresh failed: {e}")
            return {"success": False, "error": str(e)}

    def reset_password_email(self, email: str) -> Dict[str, Any]:
        """Send password reset email"""
        try:
            self.client.auth.reset_password_email(email)
            return {"success": True}
        except Exception as e:
            logger.error(f"Supabase password reset failed: {e}")
            return {"success": False, "error": str(e)}

    def update_user(self, token: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Update user metadata"""
        try:
            result = self.client.auth.update_user(
                {"data": metadata}, headers={"Authorization": f"Bearer {token}"}
            )
            return {"success": True, "user": result.user}
        except Exception as e:
            logger.error(f"Supabase update user failed: {e}")
            return {"success": False, "error": str(e)}

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            # Use httpx to verify token directly
            response = httpx.get(
                f"{self.config.url}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": self.config.anon_key,
                },
            )
            if response.status_code == 200:
                return {"success": True, "user": response.json()}
            return {"success": False, "error": "Invalid token"}
        except Exception as e:
            logger.error(f"Supabase token verification failed: {e}")
            return {"success": False, "error": str(e)}


class SupabaseDatabaseService:
    """Supabase Database Service with RLS support"""

    def __init__(self, config: SupabaseConfig):
        self.config = config
        self._client: Optional[Client] = None

    @property
    def client(self) -> Client:
        """Get Supabase client"""
        if self._client is None:
            self._client = create_client(self.config.url, self.config.anon_key)
        return self._client

    def table(self, table_name: str):
        """Get table reference"""
        return self.client.table(table_name)

    def select(
        self,
        table: str,
        query: Dict[str, Any],
        select: str = "*",
        count: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Select from table with filters"""
        try:
            builder = self.table(table).select(select)

            # Apply filters
            if "filters" in query:
                for key, value in query["filters"].items():
                    builder = builder.eq(key, value)

            # Apply ordering
            if "order" in query:
                order = query["order"]
                builder = builder.order(
                    order.get("column", "created_at"), desc=order.get("desc", True)
                )

            # Apply pagination
            if "limit" in query:
                builder = builder.limit(query["limit"])

            if "offset" in query:
                builder = builder.range(
                    query["offset"], query["offset"] + query.get("limit", 10) - 1
                )

            # Execute with count
            if count:
                builder = builder.count(count)

            result = builder.execute()
            return {"success": True, "data": result.data, "count": result.count}
        except Exception as e:
            logger.error(f"Supabase select failed: {e}")
            return {"success": False, "error": str(e)}

    def insert(
        self, table: str, data: Dict[str, Any], returning: str = "minimal"
    ) -> Dict[str, Any]:
        """Insert into table"""
        try:
            result = self.table(table).insert(data, returning=returning).execute()
            return {"success": True, "data": result.data}
        except Exception as e:
            logger.error(f"Supabase insert failed: {e}")
            return {"success": False, "error": str(e)}

    def update(
        self,
        table: str,
        data: Dict[str, Any],
        filters: Dict[str, Any],
        returning: str = "minimal",
    ) -> Dict[str, Any]:
        """Update table"""
        try:
            builder = self.table(table).update(data, returning=returning)

            for key, value in filters.items():
                builder = builder.eq(key, value)

            result = builder.execute()
            return {"success": True, "data": result.data}
        except Exception as e:
            logger.error(f"Supabase update failed: {e}")
            return {"success": False, "error": str(e)}

    def upsert(
        self,
        table: str,
        data: Dict[str, Any],
        on_conflict: Optional[str] = None,
        returning: str = "minimal",
    ) -> Dict[str, Any]:
        """Upsert into table"""
        try:
            builder = self.table(table).upsert(data, returning=returning)

            if on_conflict:
                builder = builder.on_conflict(on_conflict)

            result = builder.execute()
            return {"success": True, "data": result.data}
        except Exception as e:
            logger.error(f"Supabase upsert failed: {e}")
            return {"success": False, "error": str(e)}

    def delete(
        self, table: str, filters: Dict[str, Any], returning: str = "minimal"
    ) -> Dict[str, Any]:
        """Delete from table"""
        try:
            builder = self.table(table).delete(returning=returning)

            for key, value in filters.items():
                builder = builder.eq(key, value)

            result = builder.execute()
            return {"success": True, "data": result.data}
        except Exception as e:
            logger.error(f"Supabase delete failed: {e}")
            return {"success": False, "error": str(e)}

    def rpc(self, function_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call PostgreSQL function"""
        try:
            result = self.client.rpc(function_name, params).execute()
            return {"success": True, "data": result.data}
        except Exception as e:
            logger.error(f"Supabase RPC failed: {e}")
            return {"success": False, "error": str(e)}


class SupabaseStorageService:
    """Supabase Storage Service for file management"""

    def __init__(self, config: SupabaseConfig):
        self.config = config
        self._client: Optional[Client] = None

    @property
    def client(self) -> Client:
        """Get Supabase client"""
        if self._client is None:
            self._client = create_client(self.config.url, self.config.anon_key)
        return self._client

    def bucket(self, bucket_name: str):
        """Get storage bucket"""
        return self.client.storage.from_(bucket_name)

    def upload(
        self,
        bucket: str,
        file_path: str,
        file_content: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Upload file to storage"""
        try:
            result = self.bucket(bucket).upload(
                file_path,
                file_content,
                options=options or {"content_type": "application/octet-stream"},
            )
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"Supabase upload failed: {e}")
            return {"success": False, "error": str(e)}

    def download(self, bucket: str, file_path: str) -> Dict[str, Any]:
        """Download file from storage"""
        try:
            result = self.bucket(bucket).download(file_path)
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"Supabase download failed: {e}")
            return {"success": False, "error": str(e)}

    def list_files(
        self, bucket: str, path: str = "", limit: int = 100, offset: int = 0
    ) -> Dict[str, Any]:
        """List files in storage"""
        try:
            result = self.bucket(bucket).list(path=path, limit=limit, offset=offset)
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"Supabase list files failed: {e}")
            return {"success": False, "error": str(e)}

    def delete(self, bucket: str, file_paths: List[str]) -> Dict[str, Any]:
        """Delete files from storage"""
        try:
            result = self.bucket(bucket).remove(file_paths)
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"Supabase delete failed: {e}")
            return {"success": False, "error": str(e)}

    def get_public_url(self, bucket: str, file_path: str) -> str:
        """Get public URL for file"""
        return self.bucket(bucket).get_public_url(file_path)

    def create_signed_url(
        self, bucket: str, file_path: str, expires_in: int = 3600
    ) -> Dict[str, Any]:
        """Create signed URL for private file"""
        try:
            result = self.bucket(bucket).create_signed_url(
                file_path, expires_in=expires_in
            )
            return {"success": True, "url": result.get("signedUrl")}
        except Exception as e:
            logger.error(f"Supabase signed URL failed: {e}")
            return {"success": False, "error": str(e)}


class SupabaseRealtimeService:
    """Supabase Realtime Service for live updates"""

    def __init__(self, config: SupabaseConfig):
        self.config = config
        self._client: Optional[Client] = None
        self._channels: Dict[str, Any] = {}

    @property
    def client(self) -> Client:
        """Get Supabase client"""
        if self._client is None:
            self._client = create_client(self.config.url, self.config.anon_key)
        return self._client

    def channel(self, name: str):
        """Get or create channel"""
        if name not in self._channels:
            self._channels[name] = self.client.channel(name)
        return self._channels[name]

    def subscribe_to_table(
        self,
        table: str,
        event: str,
        callback: Callable,
        filter_clause: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Subscribe to table changes"""
        try:
            channel = self.channel(f"table:{table}")

            config = {"event": event, "schema": "public", "table": table}

            if filter_clause:
                config["filter"] = filter_clause

            channel.on("postgres_changes", config, callback).subscribe()

            return {"success": True, "channel": channel}
        except Exception as e:
            logger.error(f"Supabase subscribe failed: {e}")
            return {"success": False, "error": str(e)}

    def subscribe_to_channel(
        self, channel_name: str, callback: Callable
    ) -> Dict[str, Any]:
        """Subscribe to broadcast channel"""
        try:
            channel = self.channel(channel_name)

            channel.on("broadcast", {"event": "message"}, callback).subscribe()

            return {"success": True, "channel": channel}
        except Exception as e:
            logger.error(f"Supabase broadcast subscribe failed: {e}")
            return {"success": False, "error": str(e)}

    def broadcast(
        self, channel_name: str, event: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Broadcast message to channel"""
        try:
            channel = self.channel(channel_name)
            channel.send({"type": "broadcast", "event": event, "payload": payload})
            return {"success": True}
        except Exception as e:
            logger.error(f"Supabase broadcast failed: {e}")
            return {"success": False, "error": str(e)}

    def unsubscribe(self, channel_name: str) -> Dict[str, Any]:
        """Unsubscribe from channel"""
        try:
            if channel_name in self._channels:
                self.client.remove_channel(self._channels[channel_name])
                del self._channels[channel_name]
            return {"success": True}
        except Exception as e:
            logger.error(f"Supabase unsubscribe failed: {e}")
            return {"success": False, "error": str(e)}


class SupabaseService:
    """Main Supabase Service coordinating all features"""

    def __init__(self, config: Optional[SupabaseConfig] = None):
        self.config = config or SupabaseConfig(
            url=settings.supabase_url,
            anon_key=settings.supabase_anon_key,
            service_role_key=settings.supabase_service_role_key,
            jwt_secret=settings.supabase_jwt_secret,
        )

        self.auth = SupabaseAuthService(self.config)
        self.db = SupabaseDatabaseService(self.config)
        self.storage = SupabaseStorageService(self.config)
        self.realtime = SupabaseRealtimeService(self.config)

    @classmethod
    def from_env(cls) -> "SupabaseService":
        """Create from environment variables"""
        return cls(
            SupabaseConfig(
                url=os.getenv("SUPABASE_URL", ""),
                anon_key=os.getenv("SUPABASE_ANON_KEY", ""),
                service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
                jwt_secret=os.getenv("SUPABASE_JWT_SECRET", ""),
            )
        )


# RLS Policy SQL generator for documentation
RLS_POLICIES = """
-- Enable RLS on tables
ALTER TABLE files ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;

-- Files table policies
CREATE POLICY "Users see own files" ON files
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users upload files" ON files
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users update own files" ON files
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users delete own files" ON files
    FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Managers see all files" ON files
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_roles
            JOIN roles ON user_roles.role_id = roles.id
            WHERE user_roles.user_id = auth.uid()
            AND roles.name = 'manager'
        )
    );

CREATE POLICY "Admins manage all files" ON files
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_roles
            JOIN roles ON user_roles.role_id = roles.id
            WHERE user_roles.user_id = auth.uid()
            AND roles.name = 'admin'
        )
    );

-- Users table policies (users can only see their own profile)
CREATE POLICY "Users see own profile" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users update own profile" ON users
    FOR UPDATE USING (auth.uid() = id);

-- Workflows table policies
CREATE POLICY "Users see own workflows" ON workflows
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users create workflows" ON workflows
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Managers see all workflows" ON workflows
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_roles
            JOIN roles ON user_roles.role_id = roles.id
            WHERE user_roles.user_id = auth.uid()
            AND roles.name IN ('admin', 'manager')
        )
    );
"""
