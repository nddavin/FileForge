"""DocuSign e-signature integration connector"""

from typing import Any, Dict, List, Optional
import httpx
import base64
import logging

from .base import (
    IntegrationBase,
    IntegrationConfig,
    IntegrationResult,
    IntegrationType,
    AuthenticationType
)

logger = logging.getLogger(__name__)


class DocuSignConnector(IntegrationBase):
    """DocuSign e-signature integration using REST API"""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self._access_token: Optional[str] = None
        self._account_id: Optional[str] = None
    
    @property
    def integration_name(self) -> str:
        return "DocuSign"
    
    @property
    def integration_slug(self) -> str:
        return "docusign"
    
    def test_connection(self) -> IntegrationResult:
        """Test DocuSign connection"""
        try:
            auth_result = self._authenticate()
            if not auth_result.success:
                return auth_result
            
            # Get user info to verify connection
            url = f"{self.config.base_url}/v2.1/accounts/{self._account_id}"
            headers = self._get_headers()
            headers["Authorization"] = f"Bearer {self._access_token}"
            
            with httpx.Client(timeout=self.config.timeout) as client:
                response = client.get(url, headers=headers)
            
            if response.status_code == 200:
                return IntegrationResult(
                    success=True,
                    status_code=200,
                    data={"message": "Successfully connected to DocuSign"}
                )
            else:
                return IntegrationResult(
                    success=False,
                    status_code=response.status_code,
                    error=f"DocuSign API error: {response.text}"
                )
        except Exception as e:
            return IntegrationResult(success=False, error=str(e))
    
    def send(
        self,
        endpoint: str,
        data: Dict[str, Any],
        method: str = "POST"
    ) -> IntegrationResult:
        """Send data to DocuSign"""
        try:
            if not self._access_token:
                auth_result = self._authenticate()
                if not auth_result.success:
                    return auth_result
            
            url = f"{self.config.base_url}/v2.1/accounts/{self._account_id}{endpoint}"
            headers = self._get_headers()
            headers["Authorization"] = f"Bearer {self._access_token}"
            
            self._log_request(method, url, data)
            
            with httpx.Client(timeout=self.config.timeout) as client:
                if method == "POST":
                    response = client.post(url, json=data, headers=headers)
                elif method == "PUT":
                    response = client.put(url, json=data, headers=headers)
                elif method == "GET":
                    response = client.get(url, headers=headers)
                else:
                    return IntegrationResult(
                        success=False,
                        error=f"Unsupported HTTP method: {method}"
                    )
            
            result = IntegrationResult(
                success=200 <= response.status_code < 300,
                status_code=response.status_code,
                data=response.json() if response.text else None
            )
            
            self._log_result(result)
            return result
            
        except Exception as e:
            logger.error(f"DocuSign API error: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def create_envelope(
        self,
        document_base64: str,
        recipients: List[Dict[str, Any]],
        email_subject: str,
        email_blurb: Optional[str] = None
    ) -> IntegrationResult:
        """Create and send an envelope for signature"""
        envelope = {
            "emailSubject": email_subject,
            "emailBlurb": email_blurb or "Please sign this document",
            "documents": [{
                "documentBase64": document_base64,
                "name": "Document",
                "fileExtension": "pdf",
                "documentId": "1"
            }],
            "recipients": {
                "signers": recipients
            },
            "status": "sent"
        }
        
        return self.send("/envelopes", envelope, "POST")
    
    def get_envelope_status(self, envelope_id: str) -> IntegrationResult:
        """Get the status of an envelope"""
        return self.send(f"/envelopes/{envelope_id}", {}, "GET")
    
    def get_signed_document(self, envelope_id: str, document_id: str = "1") -> IntegrationResult:
        """Download a signed document"""
        url = f"/envelopes/{envelope_id}/documents/{document_id}"
        
        try:
            if not self._access_token:
                auth_result = self._authenticate()
                if not auth_result.success:
                    return auth_result
            
            full_url = (
                f"{self.config.base_url}/v2.1/accounts/{self._account_id}{url}"
            )
            headers = self._get_headers()
            headers["Authorization"] = f"Bearer {self._access_token}"
            
            with httpx.Client(timeout=self.config.timeout) as client:
                response = client.get(full_url, headers=headers)
            
            return IntegrationResult(
                success=response.status_code == 200,
                status_code=response.status_code,
                data={"document": base64.b64encode(response.content).decode()}
            )
        except Exception as e:
            return IntegrationResult(success=False, error=str(e))
    
    def void_envelope(
        self,
        envelope_id: str,
        void_reason: str
    ) -> IntegrationResult:
        """Void an envelope"""
        return self.send(
            f"/envelopes/{envelope_id}",
            {"status": "voided", "voidedReason": void_reason},
            "PUT"
        )
    
    def list_envelopes(
        self,
        from_date: Optional[str] = None,
        status: Optional[str] = None
    ) -> IntegrationResult:
        """List envelopes with optional filters"""
        params = []
        if from_date:
            params.append(f"from_date={from_date}")
        if status:
            params.append(f"status={status}")
        
        query = "&".join(params) if params else ""
        return self.send(f"/envelopes?{query}", {}, "GET")
    
    def _authenticate(self) -> IntegrationResult:
        """Authenticate with DocuSign OAuth2"""
        try:
            token_url = f"{self.config.base_url}/oauth/token"
            
            data = {
                "grant_type": "client_credentials",
                "client_id": self.config.credentials.get("integration_key"),
                "client_secret": self.config.credentials.get("secret_key")
            }
            
            with httpx.Client(timeout=self.config.timeout) as client:
                response = client.post(token_url, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self._access_token = token_data.get("access_token")
                
                # Get account ID from credentials or API
                self._account_id = self.config.credentials.get(
                    "account_id",
                    self._get_account_id()
                )
                
                return IntegrationResult(
                    success=True,
                    status_code=200,
                    data=token_data
                )
            else:
                return IntegrationResult(
                    success=False,
                    status_code=response.status_code,
                    error=f"Authentication failed: {response.text}"
                )
        except Exception as e:
            return IntegrationResult(success=False, error=str(e))
    
    def _get_account_id(self) -> Optional[str]:
        """Get the DocuSign account ID"""
        try:
            url = f"{self.config.base_url}/v2.1/userinfo"
            headers = self._get_headers()
            headers["Authorization"] = f"Bearer {self._access_token}"
            
            with httpx.Client(timeout=self.config.timeout) as client:
                response = client.get(url, headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                accounts = user_data.get("accounts", [])
                if accounts:
                    return accounts[0].get("account_id")
            return None
        except Exception:
            return None
    
    @classmethod
    def create_config(
        cls,
        integration_key: str,
        secret_key: str,
        account_id: Optional[str] = None,
        base_url: str = "https://demo.docusign.net/restapi"
    ) -> IntegrationConfig:
        """Create a DocuSign configuration"""
        return IntegrationConfig(
            integration_type=IntegrationType.ESIGNATURE,
            auth_type=AuthenticationType.OAUTH2,
            base_url=base_url,
            credentials={
                "integration_key": integration_key,
                "secret_key": secret_key,
                "account_id": account_id or ""
            }
        )
