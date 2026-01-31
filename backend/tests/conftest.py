"""Pytest configuration and fixtures for FileForge test suite."""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from uuid import uuid4


# ====== Test Configuration ======


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ====== Mock Data Fixtures ======


@pytest.fixture
def test_user():
    """Create a test user."""
    return {
        "id": str(uuid4()),
        "email": "test@church.org",
        "full_name": "Test User",
        "church_id": str(uuid4()),
        "roles": ["user"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def test_admin():
    """Create a test admin user."""
    return {
        "id": str(uuid4()),
        "email": "admin@church.org",
        "full_name": "Admin User",
        "church_id": str(uuid4()),
        "roles": ["admin", "user"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def test_church():
    """Create a test church."""
    return {
        "id": str(uuid4()),
        "name": "Test Church",
        "subscription_tier": "enterprise",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def test_sermon():
    """Create a test sermon."""
    return {
        "id": str(uuid4()),
        "title": "Sunday Sermon",
        "description": "A test sermon",
        "church_id": str(uuid4()),
        "primary_preacher_id": str(uuid4()),
        "primary_language": "english",
        "speaker_confidence_avg": 0.92,
        "duration_seconds": 1800,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def test_preacher():
    """Create a test preacher profile."""
    return {
        "id": str(uuid4()),
        "full_name": "Pastor John",
        "avatar_url": None,
        "voice_embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
        "confidence_score": 0.94,
        "language": "english",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def test_file():
    """Create a test file record."""
    return {
        "id": str(uuid4()),
        "filename": "sermon_test.mp3",
        "file_type": "audio",
        "file_size": 15728640,  # 15MB
        "church_id": str(uuid4()),
        "folder_id": None,
        "preacher_id": str(uuid4()),
        "primary_language": "english",
        "location_city": "Kampala",
        "quality_score": 85,
        "sermon_package_id": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def test_audio_file(tmp_path):
    """Create a temporary audio file for testing."""
    audio_path = tmp_path / "test_sermon.mp3"
    # Write minimal MP3 header
    audio_path.write_bytes(b"ID3" + b"\x04" * 100)
    return audio_path


@pytest.fixture
def test_video_file(tmp_path):
    """Create a temporary video file for testing."""
    video_path = tmp_path / "test_sermon.mp4"
    # Write minimal MP4 header
    video_path.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 100)
    return video_path


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client."""
    mock_client = MagicMock()

    # Mock auth
    mock_client.auth = MagicMock()
    mock_client.auth.get_user = AsyncMock(
        return_value=MagicMock(user=MagicMock(id="test-user-id"))
    )

    # Mock table operations
    mock_table = MagicMock()
    mock_table.select = MagicMock(return_value=mock_table)
    mock_table.insert = MagicMock(return_value=mock_table)
    mock_table.update = MagicMock(return_value=mock_table)
    mock_table.delete = MagicMock(return_value=mock_table)
    mock_table.eq = MagicMock(return_value=mock_table)
    mock_table.execute = AsyncMock(return_value=MagicMock(data=[], count=0, error=None))

    mock_client.table = MagicMock(return_value=mock_table)

    return mock_client


@pytest.fixture
def mock_celery_app():
    """Create a mock Celery app."""
    mock_app = MagicMock()
    mock_app.send_task = MagicMock(
        return_value=MagicMock(id="task-123", state="PENDING")
    )
    return mock_app


# ====== Authentication Fixtures ======


@pytest.fixture
def valid_jwt_token(test_user):
    """Create a valid JWT token for testing."""
    with patch("file_processor.core.security.create_access_token") as mock_create:
        mock_create.return_value = "valid_test_token"
        return "valid_test_token"


@pytest.fixture
def expired_jwt_token(test_user):
    """Create an expired JWT token for testing."""
    with patch("file_processor.core.security.create_access_token") as mock_create:
        mock_create.return_value = "expired_test_token"
    return "expired_test_token"


# ====== API Client Fixtures ======


@pytest.fixture
def auth_headers(valid_jwt_token):
    """Create authorization headers."""
    return {"Authorization": f"Bearer {valid_jwt_token}"}


@pytest.fixture
def admin_auth_headers(test_admin):
    """Create admin authorization headers."""
    with patch("file_processor.core.security.create_access_token") as mock_create:
        mock_create.return_value = "admin_test_token"
        return {"Authorization": "Bearer admin_test_token"}


# ====== Mock External Services ======


@pytest.fixture
def mock_gps_extractor():
    """Mock GPS extractor service."""
    mock = MagicMock()
    mock.extract_gps_from_audio = MagicMock(
        return_value={
            "lat": 0.3476,
            "lon": 32.5825,
            "readable_location": "Kampala Central Church",
            "accuracy": "high",
        }
    )
    return mock


@pytest.fixture
def mock_speaker_identifier():
    """Mock speaker identifier service."""
    mock = MagicMock()
    mock.identify_speakers = AsyncMock(
        return_value={
            "preacher": {
                "name": "Pastor John",
                "confidence": 0.94,
                "segments": [
                    {"start": 0, "end": 300, "confidence": 0.95},
                    {"start": 300, "end": 600, "confidence": 0.93},
                ],
            }
        }
    )
    return mock


@pytest.fixture
def mock_rss_feed():
    """Mock RSS feed data."""
    return {
        "entries": [
            {
                "title": "Sunday Service - Jan 28",
                "id": "https://youtube.com/watch?v=abc123",
                "links": [
                    {"type": "video/mp4", "href": "https://example.com/video.mp4"}
                ],
                "published": "2026-01-28T10:00:00Z",
            }
        ],
        "feed": {
            "title": "Church Podcast",
            "link": "https://podcast.church.org/feed.xml",
        },
    }


# ====== Test Helper Functions ======


def create_mock_upload_file(
    filename: str, content: bytes, content_type: str = "audio/mpeg"
):
    """Create a mock upload file."""
    mock_file = MagicMock()
    mock_file.filename = filename
    mock_file.content_type = content_type
    mock_file.read = AsyncMock(return_value=content)
    mock_file.seek = MagicMock()
    mock_file.size = len(content)
    return mock_file


@pytest.fixture
def sample_audio_content():
    """Sample audio file content."""
    return b"ID3" + b"\x00" * 1000


@pytest.fixture
def sample_video_content():
    """Sample video file content."""
    return b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 1000


# ====== Database Fixtures ======


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = MagicMock()
    session.execute = AsyncMock(
        return_value=MagicMock(scalars=MagicMock(all=MagicMock(return_value=[])))
    )
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


# ====== RBAC Test Data ======


@pytest.fixture
def rbac_test_cases():
    """Test cases for RBAC validation."""
    return [
        {"role": "admin", "resource": "files", "action": "read", "allowed": True},
        {"role": "admin", "resource": "files", "action": "write", "allowed": True},
        {"role": "admin", "resource": "users", "action": "manage", "allowed": True},
        {"role": "manager", "resource": "files", "action": "read", "allowed": True},
        {"role": "manager", "resource": "files", "action": "write", "allowed": True},
        {"role": "manager", "resource": "users", "action": "read", "allowed": True},
        {"role": "manager", "resource": "users", "action": "write", "allowed": False},
        {"role": "user", "resource": "files", "action": "read", "allowed": True},
        {"role": "user", "resource": "files", "action": "write", "allowed": False},
        {"role": "user", "resource": "users", "action": "write", "allowed": False},
    ]
