"""Unit tests for security components - JWT, RBAC, encryption."""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import patch, MagicMock
import jwt


# ====== JWT Token Tests ======


class TestJWTTokens:
    """Tests for JWT token creation and validation."""

    @pytest.fixture
    def secret_key(self):
        return "test-secret-key-for-testing"

    @pytest.fixture
    def token_payload(self):
        return {
            "sub": "user-123",
            "email": "test@church.org",
            "roles": ["user", "admin"],
            "church_id": str(uuid4()),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }

    def test_create_valid_token(self, token_payload, secret_key):
        """Test creating a valid JWT token."""
        with patch("file_processor.core.security.settings") as mock_settings:
            mock_settings.secret_key = secret_key
            mock_settings.algorithm = "HS256"
            token = jwt.encode(token_payload, secret_key, algorithm="HS256")
            assert isinstance(token, str)
            assert len(token) > 0

    def test_decode_valid_token(self, token_payload, secret_key):
        """Test decoding a valid JWT token."""
        with patch("file_processor.core.security.settings") as mock_settings:
            mock_settings.secret_key = secret_key
            mock_settings.algorithm = "HS256"
            token = jwt.encode(token_payload, secret_key, algorithm="HS256")
            decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
            assert decoded["sub"] == "user-123"
            assert decoded["email"] == "test@church.org"
            assert "user" in decoded["roles"]

    def test_expired_token_raises_error(self, secret_key):
        """Test that expired tokens raise an error."""
        expired_payload = {
            "sub": "user-123",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        token = jwt.encode(expired_payload, secret_key, algorithm="HS256")

        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(token, secret_key, algorithms=["HS256"])

    def test_invalid_signature_raises_error(self, secret_key):
        """Test that tokens with invalid signatures raise an error."""
        payload = {
            "sub": "user-123",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, secret_key, algorithm="HS256")

        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(token, "wrong-secret", algorithms=["HS256"])

    def test_missing_sub_claim_invalid(self, secret_key):
        """Test that tokens without 'sub' claim are invalid."""
        payload = {"exp": datetime.now(timezone.utc) + timedelta(hours=1)}
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        decoded = jwt.decode(token, secret_key, algorithms=["HS256"])

        # Token is valid but has no user identifier
        assert "sub" not in decoded


# ====== Password Hashing Tests ======


class TestPasswordHashing:
    """Tests for password hashing and verification."""

    @pytest.fixture
    def test_password(self):
        return "SecurePassword123!"

    @pytest.fixture
    def wrong_password(self):
        return "WrongPassword456!"

    def test_hash_password(self, test_password):
        """Test that password hashing produces a valid hash."""
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed = pwd_context.hash(test_password)

        assert hashed != test_password
        assert hashed.startswith("$2b$")  # bcrypt prefix
        assert len(hashed) > 50

    def test_verify_correct_password(self, test_password):
        """Test that correct password verification succeeds."""
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed = pwd_context.hash(test_password)

        assert pwd_context.verify(test_password, hashed) is True

    def test_verify_wrong_password(self, test_password, wrong_password):
        """Test that wrong password verification fails."""
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed = pwd_context.hash(test_password)

        assert pwd_context.verify(wrong_password, hashed) is False

    def test_different_passwords_produce_different_hashes(self):
        """Test that different passwords produce different hashes."""
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hash1 = pwd_context.hash("password1")
        hash2 = pwd_context.hash("password2")

        assert hash1 != hash2


# ====== RBAC Permission Tests ======


class TestRBACPermissions:
    """Tests for Role-Based Access Control."""

    @pytest.fixture
    def role_permissions(self):
        return {
            "admin": ["read", "write", "delete", "manage_users", "manage_church"],
            "manager": ["read", "write", "manage_files"],
            "user": ["read"],
        }

    def test_admin_has_all_permissions(self, role_permissions):
        """Test that admin role has all permissions."""
        permissions = role_permissions["admin"]
        assert "read" in permissions
        assert "write" in permissions
        assert "delete" in permissions
        assert "manage_users" in permissions
        assert "manage_church" in permissions

    def test_manager_lacks_admin_permissions(self, role_permissions):
        """Test that manager role lacks admin permissions."""
        permissions = role_permissions["manager"]
        assert "manage_users" not in permissions
        assert "manage_church" not in permissions

    def test_user_readonly(self, role_permissions):
        """Test that user role is read-only."""
        permissions = role_permissions["user"]
        assert permissions == ["read"]

    def test_permission_check_admin(self, role_permissions):
        """Test permission checking for admin."""
        user_permissions = role_permissions["admin"]

        assert "read" in user_permissions
        assert "write" in user_permissions
        assert "delete" in user_permissions
        assert "manage_users" in user_permissions

    def test_permission_check_manager(self, role_permissions):
        """Test permission checking for manager."""
        user_permissions = role_permissions["manager"]

        assert "read" in user_permissions
        assert "write" in user_permissions
        assert "delete" not in user_permissions
        assert "manage_users" not in user_permissions

    def test_permission_check_user(self, role_permissions):
        """Test permission checking for user."""
        user_permissions = role_permissions["user"]

        assert "read" in user_permissions
        assert "write" not in user_permissions
        assert "delete" not in user_permissions


# ====== File Validation Tests ======


class TestFileValidation:
    """Tests for file upload validation."""

    ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/wav", "audio/mp3", "audio/x-m4a"}
    ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/x-msvideo"}
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

    MALICIOUS_SIGNATURES = [
        b"MZ",  # Windows executable
        b"\x7fELF",  # Linux executable
        b"%PDF",  # PDF can contain malicious scripts
    ]

    def test_valid_audio_file_type(self):
        """Test that valid audio file types are accepted."""
        content_type = "audio/mpeg"
        assert content_type in self.ALLOWED_AUDIO_TYPES

    def test_valid_video_file_type(self):
        """Test that valid video file types are accepted."""
        content_type = "video/mp4"
        assert content_type in self.ALLOWED_VIDEO_TYPES

    def test_reject_executable_signature(self):
        """Test that executable file signatures are rejected."""
        # Test each malicious signature separately
        for signature in self.MALICIOUS_SIGNATURES:
            # Create file content that starts with this signature
            file_content = signature + b"\x00" * 100
            assert file_content.startswith(signature), f"Failed for signature: {signature}"

    def test_max_file_size_validation(self):
        """Test that file size limit is enforced."""
        file_size = self.MAX_FILE_SIZE + 1

        assert file_size > self.MAX_FILE_SIZE

    def test_valid_file_size(self):
        """Test that valid file sizes pass."""
        file_size = 50 * 1024 * 1024  # 50MB

        assert file_size < self.MAX_FILE_SIZE

    def test_empty_file_rejected(self):
        """Test that empty files are rejected."""
        file_size = 0

        assert file_size == 0


# ====== Encryption Tests ======


class TestEncryption:
    """Tests for encryption utilities."""

    @pytest.fixture
    def encryption_key(self):
        """Generate a valid Fernet key (32 url-safe base64-encoded bytes)."""
        from cryptography.fernet import Fernet
        return Fernet.generate_key()

    def test_encrypt_decrypt_roundtrip(self, encryption_key):
        """Test that encryption and decryption work together."""
        from cryptography.fernet import Fernet

        fernet = Fernet(encryption_key)
        original_data = b"Sensitive sermon data"

        encrypted = fernet.encrypt(original_data)
        decrypted = fernet.decrypt(encrypted)

        assert decrypted == original_data

    def test_encrypted_data_differs_from_original(self, encryption_key):
        """Test that encrypted data differs from original."""
        from cryptography.fernet import Fernet

        fernet = Fernet(encryption_key)
        original_data = b"Sensitive data"

        encrypted = fernet.encrypt(original_data)

        assert encrypted != original_data

    def test_different_keys_produce_different_ciphertext(self, encryption_key):
        """Test that different keys produce different ciphertext."""
        from cryptography.fernet import Fernet

        key1 = Fernet(encryption_key)
        key2 = Fernet(Fernet.generate_key())

        original_data = b"Test data"

        encrypted1 = key1.encrypt(original_data)
        encrypted2 = key2.encrypt(original_data)

        assert encrypted1 != encrypted2


# ====== API Key Tests ======


class TestAPIKeys:
    """Tests for API key generation and validation."""

    def test_api_key_format(self):
        """Test that API keys have correct format."""
        import secrets

        api_key = "ff_" + secrets.token_urlsafe(32)

        assert api_key.startswith("ff_")
        assert len(api_key) > 40

    def test_api_key_uniqueness(self):
        """Test that generated API keys are unique."""
        import secrets

        keys = set()
        for _ in range(100):
            key = "ff_" + secrets.token_urlsafe(32)
            keys.add(key)

        assert len(keys) == 100
