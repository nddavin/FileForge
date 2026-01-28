"""Integration API router"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
import logging

from ..deps import get_current_user
from ...services.integrations import (
    WebhookService,
    WebhookPayload,
    WebhookEventType,
    WebhookSubscription,
    IntegrationType
)
from ...services.integrations.salesforce import SalesforceConnector
from ...services.integrations.dynamics365 import Dynamics365Connector
from ...services.integrations.docusign import DocuSignConnector
from ...services.integrations.slack import SlackConnector
from ...services.integrations.teams import TeamsConnector
from ...services.integrations.erp import SAPConnector, OracleERPConnector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["integrations"])

# Global webhook service instance
webhook_service = WebhookService()


# Pydantic models for API
class WebhookCreate(BaseModel):
    """Create a webhook subscription"""
    name: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., max_length=2048)
    events: List[str] = Field(..., description="Event types to subscribe to")
    secret: Optional[str] = Field(None, max_length=255)
    headers: Optional[Dict[str, str]] = None


class WebhookUpdate(BaseModel):
    """Update a webhook subscription"""
    name: Optional[str] = None
    url: Optional[str] = None
    events: Optional[List[str]] = None
    active: Optional[bool] = None


class IntegrationConfigBase(BaseModel):
    """Base integration configuration"""
    integration_type: str
    auth_type: str
    base_url: str
    credentials: Dict[str, str]
    headers: Optional[Dict[str, str]] = None


class SalesforceConfig(IntegrationConfigBase):
    """Salesforce configuration"""
    client_id: str
    client_secret: str
    instance_url: Optional[str] = "https://login.salesforce.com"


class Dynamics365Config(IntegrationConfigBase):
    """Dynamics 365 configuration"""
    tenant_id: str
    client_id: str
    client_secret: str


class DocuSignConfig(IntegrationConfigBase):
    """DocuSign configuration"""
    integration_key: str
    secret_key: str
    account_id: Optional[str] = None
    base_url: str = "https://demo.docusign.net/restapi"


class SlackConfig(IntegrationConfigBase):
    """Slack configuration"""
    bot_token: str
    signing_secret: Optional[str] = None


class TeamsConfig(IntegrationConfigBase):
    """Microsoft Teams configuration"""
    tenant_id: str
    client_id: str
    client_secret: str


class SAPConfig(IntegrationConfigBase):
    """SAP configuration"""
    username: str
    password: str


class OracleERPConfig(IntegrationConfigBase):
    """Oracle ERP configuration"""
    client_id: str
    client_secret: str


# Webhook endpoints
@router.post("/webhooks")
def create_webhook(
    webhook: WebhookCreate,
    current_user = Depends(get_current_user)
) -> Dict:
    """Create a new webhook subscription"""
    try:
        events = [
            WebhookEventType(e) if e != "custom" else WebhookEventType.CUSTOM
            for e in webhook.events
        ]
        
        subscription = webhook_service.subscribe(
            name=webhook.name,
            url=webhook.url,
            events=events,
            secret=webhook.secret,
            headers=webhook.headers
        )
        
        return {
            "id": subscription.id,
            "name": subscription.name,
            "url": subscription.url,
            "secret": subscription.secret,
            "events": [e.value for e in subscription.events],
            "active": subscription.active,
            "created_at": subscription.created_at
        }
    except Exception as e:
        logger.error(f"Failed to create webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/webhooks")
def list_webhooks(
    current_user = Depends(get_current_user)
) -> List[Dict]:
    """List all webhook subscriptions"""
    subscriptions = webhook_service.list_subscriptions()
    return [
        {
            "id": sub.id,
            "name": sub.name,
            "url": sub.url,
            "events": [e.value for e in sub.events],
            "active": sub.active,
            "created_at": sub.created_at,
            "last_triggered": sub.last_triggered,
            "failure_count": sub.failure_count
        }
        for sub in subscriptions
    ]


@router.get("/webhooks/{webhook_id}")
def get_webhook(
    webhook_id: str,
    current_user = Depends(get_current_user)
) -> Dict:
    """Get a webhook subscription by ID"""
    subscription = webhook_service.get_subscription(webhook_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return {
        "id": subscription.id,
        "name": subscription.name,
        "url": subscription.url,
        "secret": subscription.secret,
        "events": [e.value for e in subscription.events],
        "active": subscription.active,
        "created_at": subscription.created_at,
        "last_triggered": subscription.last_triggered,
        "failure_count": subscription.failure_count,
        "headers": subscription.headers
    }


@router.patch("/webhooks/{webhook_id}")
def update_webhook(
    webhook_id: str,
    update: WebhookUpdate,
    current_user = Depends(get_current_user)
) -> Dict:
    """Update a webhook subscription"""
    subscription = webhook_service.get_subscription(webhook_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    update_data = update.model_dump(exclude_unset=True)
    if "events" in update_data:
        update_data["events"] = [
            WebhookEventType(e) if e != "custom" else WebhookEventType.CUSTOM
            for e in update_data["events"]
        ]
    
    updated = webhook_service.update_subscription(webhook_id, **update_data)
    
    return {
        "id": updated.id,
        "name": updated.name,
        "url": updated.url,
        "events": [e.value for e in updated.events],
        "active": updated.active
    }


@router.delete("/webhooks/{webhook_id}")
def delete_webhook(
    webhook_id: str,
    current_user = Depends(get_current_user)
) -> Dict:
    """Delete a webhook subscription"""
    if not webhook_service.unsubscribe(webhook_id):
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return {"message": "Webhook deleted successfully"}


@router.post("/webhooks/{webhook_id}/test")
def test_webhook(
    webhook_id: str,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
) -> Dict:
    """Test a webhook subscription by sending a test event"""
    subscription = webhook_service.get_subscription(webhook_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Create a test payload
    test_payload = WebhookPayload(
        event_type=WebhookEventType.FILE_PROCESSED,
        data={
            "test": True,
            "message": "This is a test webhook event"
        }
    )
    
    # Trigger the webhook in background
    background_tasks.add_task(webhook_service.trigger, test_payload)
    
    return {
        "message": "Test webhook sent",
        "event_id": test_payload.event_id
    }


@router.get("/webhooks/{webhook_id}/deliveries")
def get_webhook_deliveries(
    webhook_id: str,
    limit: int = 100,
    current_user = Depends(get_current_user)
) -> List[Dict]:
    """Get delivery history for a webhook"""
    history = webhook_service.get_delivery_history(
        subscription_id=webhook_id,
        limit=limit
    )
    return [
        {
            "success": h.success,
            "status_code": h.status_code,
            "error": h.error,
            "duration_ms": h.duration_ms,
            "timestamp": h.timestamp
        }
        for h in history
    ]


@router.get("/webhooks/statistics")
def get_webhook_statistics(
    current_user = Depends(get_current_user)
) -> Dict:
    """Get webhook delivery statistics"""
    return webhook_service.get_statistics()


@router.get("/webhooks/events")
def list_webhook_events() -> List[Dict]:
    """List available webhook event types"""
    return [
        {"value": event.value, "description": event.name}
        for event in WebhookEventType
    ]


# Integration connection endpoints
@router.post("/connect/salesforce")
def connect_salesforce(
    config: SalesforceConfig,
    current_user = Depends(get_current_user)
) -> Dict:
    """Connect to Salesforce CRM"""
    try:
        from ...services.integrations.base import IntegrationConfig, AuthenticationType
        
        integration_config = IntegrationConfig(
            integration_type=IntegrationType.CRM,
            auth_type=AuthenticationType.OAUTH2,
            base_url=config.instance_url,
            credentials={
                "client_id": config.client_id,
                "client_secret": config.client_secret
            }
        )
        
        connector = SalesforceConnector(integration_config)
        result = connector.test_connection()
        
        if result.success:
            return {
                "status": "connected",
                "message": "Successfully connected to Salesforce",
                "data": result.data
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Connection failed: {result.error}"
            )
    except Exception as e:
        logger.error(f"Salesforce connection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connect/dynamics365")
def connect_dynamics365(
    config: Dynamics365Config,
    current_user = Depends(get_current_user)
) -> Dict:
    """Connect to Microsoft Dynamics 365"""
    try:
        from ...services.integrations.base import IntegrationConfig, AuthenticationType
        
        integration_config = IntegrationConfig(
            integration_type=IntegrationType.CRM,
            auth_type=AuthenticationType.OAUTH2,
            base_url=config.base_url,
            credentials={
                "tenant_id": config.tenant_id,
                "client_id": config.client_id,
                "client_secret": config.client_secret
            }
        )
        
        connector = Dynamics365Connector(integration_config)
        result = connector.test_connection()
        
        if result.success:
            return {"status": "connected", "message": "Successfully connected to Dynamics 365"}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Connection failed: {result.error}"
            )
    except Exception as e:
        logger.error(f"Dynamics 365 connection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connect/docusign")
def connect_docusign(
    config: DocuSignConfig,
    current_user = Depends(get_current_user)
) -> Dict:
    """Connect to DocuSign"""
    try:
        from ...services.integrations.base import IntegrationConfig, AuthenticationType
        
        integration_config = IntegrationConfig(
            integration_type=IntegrationType.ESIGNATURE,
            auth_type=AuthenticationType.OAUTH2,
            base_url=config.base_url,
            credentials={
                "integration_key": config.integration_key,
                "secret_key": config.secret_key,
                "account_id": config.account_id or ""
            }
        )
        
        connector = DocuSignConnector(integration_config)
        result = connector.test_connection()
        
        if result.success:
            return {"status": "connected", "message": "Successfully connected to DocuSign"}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Connection failed: {result.error}"
            )
    except Exception as e:
        logger.error(f"DocuSign connection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connect/slack")
def connect_slack(
    config: SlackConfig,
    current_user = Depends(get_current_user)
) -> Dict:
    """Connect to Slack"""
    try:
        from ...services.integrations.base import IntegrationConfig, AuthenticationType
        
        integration_config = IntegrationConfig(
            integration_type=IntegrationType.COLLABORATION,
            auth_type=AuthenticationType.BEARER_TOKEN,
            base_url="https://slack.com/api",
            credentials={
                "bot_token": config.bot_token
            }
        )
        
        connector = SlackConnector(integration_config)
        result = connector.test_connection()
        
        if result.success:
            return {"status": "connected", "message": "Successfully connected to Slack"}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Connection failed: {result.error}"
            )
    except Exception as e:
        logger.error(f"Slack connection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connect/teams")
def connect_teams(
    config: TeamsConfig,
    current_user = Depends(get_current_user)
) -> Dict:
    """Connect to Microsoft Teams"""
    try:
        from ...services.integrations.base import IntegrationConfig, AuthenticationType
        
        integration_config = IntegrationConfig(
            integration_type=IntegrationType.COLLABORATION,
            auth_type=AuthenticationType.OAUTH2,
            base_url="https://graph.microsoft.com/v1.0",
            credentials={
                "tenant_id": config.tenant_id,
                "client_id": config.client_id,
                "client_secret": config.client_secret
            }
        )
        
        connector = TeamsConnector(integration_config)
        result = connector.test_connection()
        
        if result.success:
            return {"status": "connected", "message": "Successfully connected to Microsoft Teams"}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Connection failed: {result.error}"
            )
    except Exception as e:
        logger.error(f"Teams connection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connect/sap")
def connect_sap(
    config: SAPConfig,
    current_user = Depends(get_current_user)
) -> Dict:
    """Connect to SAP ERP"""
    try:
        from ...services.integrations.base import IntegrationConfig, AuthenticationType
        
        integration_config = IntegrationConfig(
            integration_type=IntegrationType.ERP,
            auth_type=AuthenticationType.BASIC,
            base_url=config.base_url,
            credentials={
                "username": config.username,
                "password": config.password
            }
        )
        
        connector = SAPConnector(integration_config)
        result = connector.test_connection()
        
        if result.success:
            return {"status": "connected", "message": "Successfully connected to SAP"}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Connection failed: {result.error}"
            )
    except Exception as e:
        logger.error(f"SAP connection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connect/oracle-erp")
def connect_oracle_erp(
    config: OracleERPConfig,
    current_user = Depends(get_current_user)
) -> Dict:
    """Connect to Oracle ERP Cloud"""
    try:
        from ...services.integrations.base import IntegrationConfig, AuthenticationType
        
        integration_config = IntegrationConfig(
            integration_type=IntegrationType.ERP,
            auth_type=AuthenticationType.OAUTH2,
            base_url=config.base_url,
            credentials={
                "client_id": config.client_id,
                "client_secret": config.client_secret
            }
        )
        
        connector = OracleERPConnector(integration_config)
        result = connector.test_connection()
        
        if result.success:
            return {"status": "connected", "message": "Successfully connected to Oracle ERP"}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Connection failed: {result.error}"
            )
    except Exception as e:
        logger.error(f"Oracle ERP connection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available")
def list_available_integrations() -> List[Dict]:
    """List all available integrations"""
    return [
        {
            "id": "salesforce",
            "name": "Salesforce CRM",
            "type": "crm",
            "description": "Connect to Salesforce for CRM operations",
            "auth_type": "oauth2"
        },
        {
            "id": "dynamics365",
            "name": "Microsoft Dynamics 365",
            "type": "crm",
            "description": "Connect to Microsoft Dynamics 365 CRM",
            "auth_type": "oauth2"
        },
        {
            "id": "docusign",
            "name": "DocuSign",
            "type": "e_signature",
            "description": "Send documents for e-signature with DocuSign",
            "auth_type": "oauth2"
        },
        {
            "id": "slack",
            "name": "Slack",
            "type": "collaboration",
            "description": "Send messages and files to Slack channels",
            "auth_type": "bearer_token"
        },
        {
            "id": "teams",
            "name": "Microsoft Teams",
            "type": "collaboration",
            "description": "Send messages and files to Microsoft Teams",
            "auth_type": "oauth2"
        },
        {
            "id": "sap",
            "name": "SAP ERP",
            "type": "erp",
            "description": "Connect to SAP for ERP operations",
            "auth_type": "basic"
        },
        {
            "id": "oracle-erp",
            "name": "Oracle ERP Cloud",
            "type": "erp",
            "description": "Connect to Oracle ERP Cloud",
            "auth_type": "oauth2"
        }
    ]
