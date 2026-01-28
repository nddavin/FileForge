"""Base integration classes for enterprise connectors"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
from enum import Enum
import hashlib
import hmac
import json
import time
import logging

logger = logging.getLogger(__name__)


class IntegrationType(Enum):
    """Types of enterprise integrations"""
    CRM = "crm"
    ERP = "erp"
    ESIGNATURE = "e_signature"
    COLLABORATION = "collaboration"
    CUSTOM = "custom"


class AuthenticationType(Enum):
    """Authentication methods for integrations"""
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    BASIC = "basic"
    BEARER_TOKEN = "bearer_token"
    HMAC = "hmac"


@dataclass
class IntegrationConfig:
    """Configuration for an integration"""
    integration_type: IntegrationType
    auth_type: AuthenticationType
    base_url: str
    credentials: Dict[str, str] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    retry_attempts: int = 3
    enabled: bool = True
    
    def __post_init__(self):
        """Validate configuration"""
        if not self.base_url:
            raise ValueError("Base URL is required for integration")
        if self.auth_type == AuthenticationType.API_KEY and 'api_key' not in self.credentials:
            raise ValueError("API key is required for API_KEY authentication")


@dataclass
class IntegrationResult:
    """Result from an integration call"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    headers: Dict[str, str] = field(default_factory=dict)


class IntegrationBase(ABC):
    """Abstract base class for all enterprise integrations"""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self._session = None
        self._token_cache: Dict[str, Any] = {}
    
    @property
    @abstractmethod
    def integration_name(self) -> str:
        """Human-readable name of the integration"""
        pass
    
    @property
    @abstractmethod
    def integration_slug(self) -> str:
        """Machine-readable identifier for the integration"""
        pass
    
    @abstractmethod
    def test_connection(self) -> IntegrationResult:
        """Test if the integration is properly configured"""
        pass
    
    @abstractmethod
    def send(self, endpoint: str, data: Dict[str, Any], method: str = "POST") -> IntegrationResult:
        """Send data to the integration"""
        pass
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"FileForge-Integration/{self.integration_slug}",
        }
        headers.update(self.config.headers)
        
        # Add authentication headers based on auth type
        if self.config.auth_type == AuthenticationType.API_KEY:
            headers["Authorization"] = f"ApiKey {self.config.credentials.get('api_key', '')}"
        elif self.config.auth_type == AuthenticationType.BEARER_TOKEN:
            headers["Authorization"] = f"Bearer {self.config.credentials.get('token', '')}"
        elif self.config.auth_type == AuthenticationType.BASIC:
            import base64
            credentials = f"{self.config.credentials.get('username', '')}:{self.config.credentials.get('password', '')}"
            encoded = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"
        
        return headers
    
    def _sign_payload(self, payload: str, secret: str) -> str:
        """Create HMAC signature for payload verification"""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _validate_webhook_signature(self, payload: str, signature: str, secret: str) -> bool:
        """Validate webhook signature"""
        expected = self._sign_payload(payload, secret)
        return hmac.compare_digest(expected, signature)
    
    def _get_token(self) -> Optional[str]:
        """Get cached OAuth token if applicable"""
        if self.config.auth_type != AuthenticationType.OAUTH2:
            return None
        
        token_info = self._token_cache.get("access_token")
        if token_info:
            if token_info.get("expires_at", 0) > time.time():
                return token_info.get("access_token")
        return None
    
    def _cache_token(self, token: str, expires_in: int):
        """Cache OAuth token with expiration"""
        self._token_cache["access_token"] = {
            "access_token": token,
            "expires_at": time.time() + expires_in - 60  # Expire 1 minute early
        }
    
    def _log_request(self, method: str, url: str, data: Dict[str, Any]):
        """Log API request (without sensitive data)"""
        safe_data = {k: v for k, v in data.items() 
                    if k not in ['api_key', 'password', 'secret', 'token']}
        logger.info(f"[{self.integration_name}] {method} {url} - Data: {json.dumps(safe_data)}")
    
    def _log_result(self, result: IntegrationResult):
        """Log integration result"""
        if result.success:
            logger.info(f"[{self.integration_name}] Success - Status: {result.status_code}")
        else:
            logger.error(f"[{self.integration_name}] Failed - {result.error}")
