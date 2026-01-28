"""Microsoft Dynamics 365 CRM integration connector"""

from typing import Any, Dict, Optional
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


class Dynamics365Connector(IntegrationBase):
    """Microsoft Dynamics 365 CRM integration using Web API"""

    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self._access_token: Optional[str] = None
        self._tenant_id: str = config.credentials.get("tenant_id", "")

    @property
    def integration_name(self) -> str:
        return "Microsoft Dynamics 365"

    @property
    def integration_slug(self) -> str:
        return "dynamics365"

    def test_connection(self) -> IntegrationResult:
        """Test Dynamics 365 connection"""
        try:
            auth_result = self._authenticate()
            if not auth_result.success:
                return auth_result

            # Get organization info to verify connection
            url = f"{self.config.base_url}/api/data/v9.2/WhoAmI()"
            headers = self._get_headers()
            headers["Authorization"] = f"Bearer {self._access_token}"

            with httpx.Client(timeout=self.config.timeout) as client:
                response = client.get(url, headers=headers)

            if response.status_code == 200:
                return IntegrationResult(
                    success=True,
                    status_code=200,
                    data={"message": "Successfully connected to Dynamics 365"},
                )
            else:
                return IntegrationResult(
                    success=False,
                    status_code=response.status_code,
                    error=f"Dynamics 365 API error: {response.text}",
                )
        except Exception as e:
            return IntegrationResult(success=False, error=str(e))

    def send(
        self, endpoint: str, data: Dict[str, Any], method: str = "POST"
    ) -> IntegrationResult:
        """Send data to Dynamics 365"""
        try:
            if not self._access_token:
                auth_result = self._authenticate()
                if not auth_result.success:
                    return auth_result

            url = f"{self.config.base_url}/api/data/v9.2{endpoint}"
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
            logger.error(f"Dynamics 365 API error: {e}")
            return IntegrationResult(success=False, error=str(e))

    def create_contact(self, contact_data: Dict[str, Any]) -> IntegrationResult:
        """Create a new contact"""
        return self.send("/contacts", contact_data, "POST")

    def update_contact(
        self, contact_id: str, data: Dict[str, Any]
    ) -> IntegrationResult:
        """Update an existing contact"""
        return self.send(f"/contacts({contact_id})", data, "PATCH")

    def create_account(self, account_data: Dict[str, Any]) -> IntegrationResult:
        """Create a new account"""
        return self.send("/accounts", account_data, "POST")

    def create_opportunity(self, opp_data: Dict[str, Any]) -> IntegrationResult:
        """Create a new opportunity"""
        return self.send("/opportunities", opp_data, "POST")

    def create_lead(self, lead_data: Dict[str, Any]) -> IntegrationResult:
        """Create a new lead"""
        return self.send("/leads", lead_data, "POST")

    def upload_file(
        self, entity: str, entity_id: str, file_data: Dict[str, Any]
    ) -> IntegrationResult:
        """Upload a file to an entity"""
        return self.send(f"/{entity}({entity_id})/annotation", file_data, "POST")

    def query(self, fetchxml: str) -> IntegrationResult:
        """Execute a FetchXML query"""
        return self.send(f"?fetchxml={httpx.utils.quote(fetchxml)}", {}, "GET")

    def _authenticate(self) -> IntegrationResult:
        """Authenticate with Microsoft Identity Platform"""
        try:
            token_url = (
                f"https://login.microsoftonline.com/{self._tenant_id}"
                f"/oauth2/v2.0/token"
            )

            data = {
                "grant_type": "client_credentials",
                "client_id": self.config.credentials.get("client_id"),
                "client_secret": self.config.credentials.get("client_secret"),
                "scope": self.config.credentials.get(
                    "scope", f"{self.config.base_url}/.default"
                ),
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
        cls, tenant_id: str, client_id: str, client_secret: str, base_url: str
    ) -> IntegrationConfig:
        """Create a Dynamics 365 configuration"""
        return IntegrationConfig(
            integration_type=IntegrationType.CRM,
            auth_type=AuthenticationType.OAUTH2,
            base_url=base_url,
            credentials={
                "tenant_id": tenant_id,
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )
