"""ERP system integration base (SAP, Oracle, etc.)"""

from typing import Any, Dict, Optional
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


class SAPConnector(IntegrationBase):
    """SAP ERP integration using OData or RFC/BAPI"""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self._csrf_token: Optional[str] = None
    
    @property
    def integration_name(self) -> str:
        return "SAP ERP"
    
    @property
    def integration_slug(self) -> str:
        return "sap"
    
    def test_connection(self) -> IntegrationResult:
        """Test SAP connection"""
        try:
            url = f"{self.config.base_url}/sap/opu/odata/sap/API_BUSINESS_PARTNER/A_BusinessPartner"
            headers = self._get_headers()
            
            with httpx.Client(timeout=self.config.timeout) as client:
                response = client.get(url, headers=headers)
            
            if response.status_code in [200, 201]:
                return IntegrationResult(
                    success=True,
                    status_code=response.status_code,
                    data={"message": "Successfully connected to SAP"}
                )
            else:
                return IntegrationResult(
                    success=False,
                    status_code=response.status_code,
                    error=f"SAP API error: {response.text}"
                )
        except Exception as e:
            return IntegrationResult(success=False, error=str(e))
    
    def send(
        self,
        endpoint: str,
        data: Dict[str, Any],
        method: str = "GET"
    ) -> IntegrationResult:
        """Send data to SAP"""
        try:
            url = f"{self.config.base_url}{endpoint}"
            headers = self._get_headers()
            
            if self._csrf_token:
                headers["X-CSRF-Token"] = self._csrf_token
            
            self._log_request(method, url, data)
            
            with httpx.Client(timeout=self.config.timeout) as client:
                if method == "GET":
                    response = client.get(url, headers=headers)
                elif method == "POST":
                    response = client.post(url, json=data, headers=headers)
                elif method == "PATCH":
                    response = client.patch(url, json=data, headers=headers)
                elif method == "DELETE":
                    response = client.delete(url, headers=headers)
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
            logger.error(f"SAP API error: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def get_business_partners(self, top: int = 100) -> IntegrationResult:
        """Get business partners from SAP"""
        return self.send(
            f"/sap/opu/odata/sap/API_BUSINESS_PARTNER/A_BusinessPartner?$top={top}",
            {},
            "GET"
        )
    
    def create_material(self, material_data: Dict[str, Any]) -> IntegrationResult:
        """Create a material in SAP"""
        return self.send(
            "/sap/opu/odata/sap/API_PRODUCT_SRV/A_Product",
            material_data,
            "POST"
        )
    
    def create_purchase_order(self, po_data: Dict[str, Any]) -> IntegrationResult:
        """Create a purchase order in SAP"""
        return self.send(
            "/sap/opu/odata/sap/API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrder",
            po_data,
            "POST"
        )
    
    def upload_document(self, doc_data: Dict[str, Any]) -> IntegrationResult:
        """Upload a document to SAP"""
        return self.send(
            "/sap/opu/odata/sap/API_DOCUMENT_SRV/A_Document",
            doc_data,
            "POST"
        )
    
    def _authenticate(self) -> IntegrationResult:
        """Get CSRF token for SAP OData"""
        try:
            url = f"{self.config.base_url}/sap/opu/odata/sap/API_BUSINESS_PARTNER"
            headers = self._get_headers()
            headers["X-CSRF-Token"] = "Fetch"
            
            with httpx.Client(timeout=self.config.timeout) as client:
                response = client.get(url, headers=headers)
            
            if response.status_code == 200:
                self._csrf_token = response.headers.get("X-CSRF-Token")
                return IntegrationResult(
                    success=True,
                    data={"csrf_token": self._csrf_token}
                )
            else:
                return IntegrationResult(
                    success=False,
                    error=f"CSRF token fetch failed: {response.text}"
                )
        except Exception as e:
            return IntegrationResult(success=False, error=str(e))
    
    @classmethod
    def create_config(
        cls,
        base_url: str,
        username: str,
        password: str
    ) -> IntegrationConfig:
        """Create SAP configuration"""
        return IntegrationConfig(
            integration_type=IntegrationType.ERP,
            auth_type=AuthenticationType.BASIC,
            base_url=base_url,
            credentials={
                "username": username,
                "password": password
            }
        )


class OracleERPConnector(IntegrationBase):
    """Oracle ERP Cloud integration using REST API"""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self._access_token: Optional[str] = None
    
    @property
    def integration_name(self) -> str:
        return "Oracle ERP Cloud"
    
    @property
    def integration_slug(self) -> str:
        return "oracle_erp"
    
    def test_connection(self) -> IntegrationResult:
        """Test Oracle ERP connection"""
        try:
            auth_result = self._authenticate()
            if not auth_result.success:
                return auth_result
            
            url = f"{self.config.base_url}/fscmRestApi/resources/11.13.18.05/financialPlanAndBudgets"
            headers = self._get_headers()
            headers["Authorization"] = f"Bearer {self._access_token}"
            
            with httpx.Client(timeout=self.config.timeout) as client:
                response = client.get(url, headers=headers)
            
            return IntegrationResult(
                success=response.status_code == 200,
                status_code=response.status_code,
                data={"message": "Successfully connected to Oracle ERP"}
            )
        except Exception as e:
            return IntegrationResult(success=False, error=str(e))
    
    def send(
        self,
        endpoint: str,
        data: Dict[str, Any],
        method: str = "GET"
    ) -> IntegrationResult:
        """Send data to Oracle ERP"""
        try:
            if not self._access_token:
                auth_result = self._authenticate()
                if not auth_result.success:
                    return auth_result
            
            url = f"{self.config.base_url}{endpoint}"
            headers = self._get_headers()
            headers["Authorization"] = f"Bearer {self._access_token}"
            
            self._log_request(method, url, data)
            
            with httpx.Client(timeout=self.config.timeout) as client:
                if method == "GET":
                    response = client.get(url, headers=headers)
                elif method == "POST":
                    response = client.post(url, json=data, headers=headers)
                elif method == "PATCH":
                    response = client.patch(url, json=data, headers=headers)
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
            logger.error(f"Oracle ERP API error: {e}")
            return IntegrationResult(success=False, error=str(e))
    
    def create_supplier(self, supplier_data: Dict[str, Any]) -> IntegrationResult:
        """Create a supplier in Oracle ERP"""
        return self.send(
            "/fscmRestApi/resources/11.13.18.05/suppliers",
            supplier_data,
            "POST"
        )
    
    def create_invoice(self, invoice_data: Dict[str, Any]) -> IntegrationResult:
        """Create an invoice in Oracle ERP"""
        return self.send(
            "/fscmRestApi/resources/11.13.18.05/invoices",
            invoice_data,
            "POST"
        )
    
    def upload_document(self, doc_data: Dict[str, Any]) -> IntegrationResult:
        """Upload a document to Oracle ERP"""
        return self.send(
            "/fscmRestApi/resources/11.13.18.05/documents",
            doc_data,
            "POST"
        )
    
    def _authenticate(self) -> IntegrationResult:
        """Authenticate with Oracle OAuth2"""
        try:
            token_url = f"{self.config.base_url}/oauth2/v1/token"
            
            data = {
                "grant_type": "client_credentials",
                "client_id": self.config.credentials.get("client_id"),
                "client_secret": self.config.credentials.get("client_secret")
            }
            
            with httpx.Client(timeout=self.config.timeout) as client:
                response = client.post(token_url, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self._access_token = token_data.get("access_token")
                
                return IntegrationResult(
                    success=True,
                    data=token_data
                )
            else:
                return IntegrationResult(
                    success=False,
                    error=f"Authentication failed: {response.text}"
                )
        except Exception as e:
            return IntegrationResult(success=False, error=str(e))
    
    @classmethod
    def create_config(
        cls,
        base_url: str,
        client_id: str,
        client_secret: str
    ) -> IntegrationConfig:
        """Create Oracle ERP configuration"""
        return IntegrationConfig(
            integration_type=IntegrationType.ERP,
            auth_type=AuthenticationType.OAUTH2,
            base_url=base_url,
            credentials={
                "client_id": client_id,
                "client_secret": client_secret
            }
        )
