"""Salesforce CRM integration connector"""

from typing import Any, Dict, List, Optional
import httpx
import json
import logging

from .base import (
    IntegrationBase,
    IntegrationConfig,
    IntegrationResult,
    IntegrationType,
    AuthenticationType
)

logger = logging.getLogger(__name__)


class SalesforceConnector(IntegrationBase):
    """Salesforce CRM integration using REST API"""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self._access_token: Optional[str] = None
        self._instance_url: Optional[str] = None
    
    @property
    def integration_name(self) -> str:
        return "Salesforce CRM"
    
    @property
    def integration_slug(self) -> str:
        return "salesforce"
    
    def test_connection(self) -> IntegrationResult:
        """Test Salesforce connection"""
        try:
            # Get access token first
            auth_result = self._authenticate()
            if not auth_result.success:
                return auth_result
            
            # Make a simple API call to verify connection
            url = f"{self._instance_url}/services/data/v58.0/sobjects/"
            headers = self._get_headers()
            headers["Authorization"] = f"Bearer {self._access_token}"
            
            with httpx.Client(timeout=self.config.timeout) as client:
                response = client.get(url, headers=headers)
            
            if response.status_code == 200:
                return IntegrationResult(
                    success=True,
                    status_code=200,
                    data={"message": "Successfully connected to Salesforce"}
                )
            else:
                return IntegrationResult(
                    success=False,
                    status_code=response.status_code,
                    error=f"Salesforce API error: {response.text}"
                )
        except Exception as e:
            return IntegrationResult(
                success=False,
                error=str(e)
            )
    
    def send(self, endpoint: str, data: Dict[str, Any], method: str = "POST") -> IntegrationResult:
        """Send data to Salesforce"""
        try:
            # Ensure we have valid authentication
            if not self._access_token:
                auth_result = self._authenticate()
                if not auth_result.success:
                    return auth_result
            
            url = f"{self._instance_url}/services/data/v58.0{endpoint}"
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
            logger.error(f"Salesforce API error: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def create_lead(self, lead_data: Dict[str, Any]) -> IntegrationResult:
        """Create a new lead in Salesforce"""
        return self.send("/sobjects/Lead/", lead_data, "POST")
    
    def update_lead(self, lead_id: str, lead_data: Dict[str, Any]) -> IntegrationResult:
        """Update an existing lead"""
        return self.send(f"/sobjects/Lead/{lead_id}", lead_data, "PATCH")
    
    def create_contact(self, contact_data: Dict[str, Any]) -> IntegrationResult:
        """Create a new contact in Salesforce"""
        return self.send("/sobjects/Contact/", contact_data, "POST")
    
    def update_contact(self, contact_id: str, contact_data: Dict[str, Any]) -> IntegrationResult:
        """Update an existing contact"""
        return self.send(f"/sobjects/Contact/{contact_id}", contact_data, "PATCH")
    
    def create_opportunity(self, opportunity_data: Dict[str, Any]) -> IntegrationResult:
        """Create a new opportunity in Salesforce"""
        return self.send("/sobjects/Opportunity/", opportunity_data, "POST")
    
    def upload_document(self, document_data: Dict[str, Any]) -> IntegrationResult:
        """Upload a document to Salesforce Files"""
        return self.send("/sobjects/ContentVersion/", document_data, "POST")
    
    def query(self, soql: str) -> IntegrationResult:
        """Execute a SOQL query"""
        encoded_query = httpx.utils.quote(soql)
        return self.send(f"/query/?q={encoded_query}", {}, "GET")
    
    def _authenticate(self) -> IntegrationResult:
        """Authenticate with Salesforce OAuth2"""
        try:
            auth_url = "https://login.salesforce.com/services/oauth2/token"
            
            data = {
                "grant_type": "client_credentials",
                "client_id": self.config.credentials.get("client_id"),
                "client_secret": self.config.credentials.get("client_secret")
            }
            
            with httpx.Client(timeout=self.config.timeout) as client:
                response = client.post(auth_url, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self._access_token = token_data.get("access_token")
                self._instance_url = token_data.get("instance_url")
                
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
    
    @classmethod
    def create_config(
        cls,
        client_id: str,
        client_secret: str,
        instance_url: str = "https://login.salesforce.com"
    ) -> IntegrationConfig:
        """Create a Salesforce configuration"""
        return IntegrationConfig(
            integration_type=IntegrationType.CRM,
            auth_type=AuthenticationType.OAUTH2,
            base_url=instance_url,
            credentials={
                "client_id": client_id,
                "client_secret": client_secret
            }
        )
