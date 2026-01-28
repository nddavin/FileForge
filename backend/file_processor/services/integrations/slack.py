"""Slack collaboration platform integration connector"""

from typing import Any, Dict, List, Optional
import httpx
import logging

from .base import (
    IntegrationBase,
    IntegrationConfig,
    IntegrationResult,
    IntegrationType,
    AuthenticationType
)

logger = logging.getLogger(__name__)


class SlackConnector(IntegrationBase):
    """Slack integration using Web API"""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self._bot_token: Optional[str] = None
    
    @property
    def integration_name(self) -> str:
        return "Slack"
    
    @property
    def integration_slug(self) -> str:
        return "slack"
    
    def test_connection(self) -> IntegrationResult:
        """Test Slack connection"""
        try:
            # Use the auth.test API to verify connection
            url = "https://slack.com/api/auth.test"
            headers = self._get_headers()
            headers["Authorization"] = f"Bearer {self._bot_token}"
            
            with httpx.Client(timeout=self.config.timeout) as client:
                response = client.post(url, headers=headers)
            
            data = response.json()
            if data.get("ok"):
                return IntegrationResult(
                    success=True,
                    status_code=200,
                    data={
                        "message": "Successfully connected to Slack",
                        "team": data.get("team"),
                        "user": data.get("user")
                    }
                )
            else:
                return IntegrationResult(
                    success=False,
                    status_code=response.status_code,
                    error=data.get("error", "Unknown error")
                )
        except Exception as e:
            return IntegrationResult(success=False, error=str(e))
    
    def send(
        self,
        endpoint: str,
        data: Dict[str, Any],
        method: str = "POST"
    ) -> IntegrationResult:
        """Send data to Slack API"""
        try:
            url = f"https://slack.com/api{endpoint}"
            headers = self._get_headers()
            headers["Authorization"] = f"Bearer {self._bot_token}"
            
            self._log_request(method, url, data)
            
            with httpx.Client(timeout=self.config.timeout) as client:
                if method == "POST":
                    response = client.post(url, json=data, headers=headers)
                else:
                    return IntegrationResult(
                        success=False,
                        error=f"Unsupported HTTP method: {method}"
                    )
            
            result_data = response.json()
            result = IntegrationResult(
                success=result_data.get("ok", False),
                status_code=response.status_code,
                data=result_data
            )
            
            self._log_result(result)
            return result
            
        except Exception as e:
            logger.error(f"Slack API error: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def send_message(
        self,
        channel: str,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
        thread_ts: Optional[str] = None
    ) -> IntegrationResult:
        """Send a message to a Slack channel"""
        data = {
            "channel": channel,
            "text": text
        }
        
        if blocks:
            data["blocks"] = blocks
        
        if thread_ts:
            data["thread_ts"] = thread_ts
        
        return self.send("/chat.postMessage", data, "POST")
    
    def upload_file(
        self,
        file_content: str,
        filename: str,
        channel: str,
        title: Optional[str] = None,
        filetype: Optional[str] = None
    ) -> IntegrationResult:
        """Upload a file to Slack"""
        try:
            url = "https://slack.com/api/files.upload"
            headers = self._get_headers()
            headers["Authorization"] = f"Bearer {self._bot_token}"
            
            files = {
                "file": (filename, file_content, filetype or "auto")
            }
            
            data = {
                "channels": channel,
                "filename": filename,
                "title": title or filename
            }
            
            with httpx.Client(timeout=self.config.timeout) as client:
                response = client.post(
                    url,
                    files=files,
                    data=data,
                    headers=headers
                )
            
            result_data = response.json()
            return IntegrationResult(
                success=result_data.get("ok", False),
                status_code=response.status_code,
                data=result_data
            )
        except Exception as e:
            return IntegrationResult(success=False, error=str(e))
    
    def create_channel(self, name: str, is_private: bool = False) -> IntegrationResult:
        """Create a new Slack channel"""
        data = {
            "name": name,
            "is_private": is_private
        }
        return self.send("/conversations.create", data, "POST")
    
    def invite_to_channel(
        self,
        channel_id: str,
        user_ids: List[str]
    ) -> IntegrationResult:
        """Invite users to a channel"""
        data = {
            "channel": channel_id,
            "users": ",".join(user_ids)
        }
        return self.send("/conversations.invite", data, "POST")
    
    def get_channel_info(self, channel_id: str) -> IntegrationResult:
        """Get information about a channel"""
        url = f"/conversations.info?channel={channel_id}"
        return self.send(url, {}, "POST")
    
    def list_channels(
        self,
        types: str = "public_channel,private_channel",
        limit: int = 100
    ) -> IntegrationResult:
        """List all channels"""
        url = f"/conversations.list?types={types}&limit={limit}"
        return self.send(url, {}, "POST")
    
    def schedule_message(
        self,
        channel: str,
        text: str,
        post_at: int  # Unix timestamp
    ) -> IntegrationResult:
        """Schedule a message for later delivery"""
        data = {
            "channel": channel,
            "text": text,
            "post_at": post_at
        }
        return self.send("/chat.scheduleMessage", data, "POST")
    
    def _authenticate(self) -> IntegrationResult:
        """Set up authentication with bot token"""
        self._bot_token = self.config.credentials.get("bot_token")
        
        if not self._bot_token:
            return IntegrationResult(
                success=False,
                error="Bot token is required"
            )
        
        return IntegrationResult(success=True, data={"authenticated": True})
    
    @classmethod
    def create_config(
        cls,
        bot_token: str,
        signing_secret: Optional[str] = None
    ) -> IntegrationConfig:
        """Create a Slack configuration"""
        return IntegrationConfig(
            integration_type=IntegrationType.COLLABORATION,
            auth_type=AuthenticationType.BEARER_TOKEN,
            base_url="https://slack.com/api",
            credentials={
                "bot_token": bot_token,
                "signing_secret": signing_secret or ""
            }
        )
