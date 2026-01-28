"""Microsoft Teams integration connector"""

from typing import Any, Dict, List, Optional
import httpx
import logging

from .base import (
    IntegrationBase,
    IntegrationConfig,
    IntegrationResult,
    IntegrationType,
    AuthenticationType,
)

logger = logging.getLogger(__name__)


class TeamsConnector(IntegrationBase):
    """Microsoft Teams integration using Graph API"""

    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self._access_token: Optional[str] = None

    @property
    def integration_name(self) -> str:
        return "Microsoft Teams"

    @property
    def integration_slug(self) -> str:
        return "teams"

    def test_connection(self) -> IntegrationResult:
        """Test Teams connection"""
        try:
            auth_result = self._authenticate()
            if not auth_result.success:
                return auth_result

            # Get user info to verify connection
            url = "https://graph.microsoft.com/v1.0/me"
            headers = self._get_headers()
            headers["Authorization"] = f"Bearer {self._access_token}"

            with httpx.Client(timeout=self.config.timeout) as client:
                response = client.get(url, headers=headers)

            if response.status_code == 200:
                return IntegrationResult(
                    success=True,
                    status_code=200,
                    data={"message": "Successfully connected to Microsoft Teams"},
                )
            else:
                return IntegrationResult(
                    success=False,
                    status_code=response.status_code,
                    error=f"Teams API error: {response.text}",
                )
        except Exception as e:
            return IntegrationResult(success=False, error=str(e))

    def send(
        self, endpoint: str, data: Dict[str, Any], method: str = "POST"
    ) -> IntegrationResult:
        """Send data to Microsoft Teams Graph API"""
        try:
            if not self._access_token:
                auth_result = self._authenticate()
                if not auth_result.success:
                    return auth_result

            url = f"https://graph.microsoft.com/v1.0{endpoint}"
            headers = self._get_headers()
            headers["Authorization"] = f"Bearer {self._access_token}"

            self._log_request(method, url, data)

            with httpx.Client(timeout=self.config.timeout) as client:
                if method == "POST":
                    response = client.post(url, json=data, headers=headers)
                elif method == "PATCH":
                    response = client.patch(url, json=data, headers=headers)
                elif method == "GET":
                    response = client.get(url, headers=headers)
                else:
                    return IntegrationResult(
                        success=False, error=f"Unsupported HTTP method: {method}"
                    )

            result = IntegrationResult(
                success=200 <= response.status_code < 300,
                status_code=response.status_code,
                data=response.json() if response.text else None,
            )

            self._log_result(result)
            return result

        except Exception as e:
            logger.error(f"Teams API error: {e}")
            return IntegrationResult(success=False, error=str(e))

    def send_channel_message(
        self, team_id: str, channel_id: str, content: str, content_type: str = "html"
    ) -> IntegrationResult:
        """Send a message to a Teams channel"""
        data = {"body": {"contentType": content_type, "content": content}}
        return self.send(
            f"/teams/{team_id}/channels/{channel_id}/messages", data, "POST"
        )

    def send_chat_message(
        self, chat_id: str, content: str, content_type: str = "html"
    ) -> IntegrationResult:
        """Send a message to a Teams chat"""
        data = {"body": {"contentType": content_type, "content": content}}
        return self.send(f"/chats/{chat_id}/messages", data, "POST")

    def create_chat(
        self, topic: Optional[str], members: List[Dict[str, str]]
    ) -> IntegrationResult:
        """Create a new chat with members"""
        data = {
            "chatType": "group" if topic else "oneOnOne",
            "topic": topic,
            "members": [
                {
                    "@odata.type": "#microsoft.graph.aadUserConversationMember",
                    "roles": ["owner"],
                    "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{m['id']}')",
                }
                for m in members
            ],
        }
        return self.send("/chats", data, "POST")

    def upload_file(
        self,
        file_content: bytes,
        filename: str,
        chat_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        team_id: Optional[str] = None,
    ) -> IntegrationResult:
        """Upload a file to a Teams chat or channel"""
        try:
            if not self._access_token:
                auth_result = self._authenticate()
                if not auth_result.success:
                    return auth_result

            # Determine upload URL
            if chat_id:
                upload_url = f"/chats/{chat_id}/messages/{filename}/content"
            elif channel_id and team_id:
                upload_url = (
                    f"/teams/{team_id}/channels/{channel_id}/messages/"
                    f"{filename}/content"
                )
            else:
                return IntegrationResult(
                    success=False,
                    error="Either chat_id or (team_id, channel_id) required",
                )

            url = f"https://graph.microsoft.com/v1.0{upload_url}"
            headers = self._get_headers()
            headers["Authorization"] = f"Bearer {self._access_token}"
            headers["Content-Type"] = "application/octet-stream"

            with httpx.Client(timeout=self.config.timeout) as client:
                response = client.put(url, content=file_content, headers=headers)

            return IntegrationResult(
                success=200 <= response.status_code < 300,
                status_code=response.status_code,
                data=response.json() if response.text else None,
            )
        except Exception as e:
            return IntegrationResult(success=False, error=str(e))

    def list_teams(self) -> IntegrationResult:
        """List all teams the user is part of"""
        return self.send("/me/joinedTeams", {}, "GET")

    def list_channels(self, team_id: str) -> IntegrationResult:
        """List all channels in a team"""
        return self.send(f"/teams/{team_id}/channels", {}, "GET")

    def get_team_members(self, team_id: str) -> IntegrationResult:
        """Get all members of a team"""
        return self.send(f"/teams/{team_id}/members", {}, "GET")

    def create_webhook_channel(
        self, team_id: str, channel_id: str, name: str, webhook_url: str
    ) -> IntegrationResult:
        """Create an incoming webhook for a channel"""
        data = {"name": name, "webhookUrl": webhook_url}
        return self.send(
            f"/teams/{team_id}/channels/{channel_id}/webhooks", data, "POST"
        )

    def _authenticate(self) -> IntegrationResult:
        """Authenticate with Microsoft Graph API"""
        try:
            tenant_id = self.config.credentials.get("tenant_id")
            client_id = self.config.credentials.get("client_id")
            client_secret = self.config.credentials.get("client_secret")

            token_url = (
                f"https://login.microsoftonline.com/{tenant_id}" f"/oauth2/v2.0/token"
            )

            data = {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "https://graph.microsoft.com/.default",
            }

            with httpx.Client(timeout=self.config.timeout) as client:
                response = client.post(token_url, data=data)

            if response.status_code == 200:
                token_data = response.json()
                self._access_token = token_data.get("access_token")

                return IntegrationResult(success=True, status_code=200, data=token_data)
            else:
                return IntegrationResult(
                    success=False,
                    status_code=response.status_code,
                    error=f"Authentication failed: {response.text}",
                )
        except Exception as e:
            return IntegrationResult(success=False, error=str(e))

    @classmethod
    def create_config(
        cls, tenant_id: str, client_id: str, client_secret: str
    ) -> IntegrationConfig:
        """Create a Microsoft Teams configuration"""
        return IntegrationConfig(
            integration_type=IntegrationType.COLLABORATION,
            auth_type=AuthenticationType.OAUTH2,
            base_url="https://graph.microsoft.com/v1.0",
            credentials={
                "tenant_id": tenant_id,
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )
