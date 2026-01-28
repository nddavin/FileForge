# Enterprise Integrations Package
# Provides connectors for CRM, ERP, e-signature, and collaboration platforms

from .webhook import (
    WebhookService,
    WebhookPayload,
    WebhookSubscription,
    WebhookEventType,
    WebhookDeliveryResult
)
from .base import (
    IntegrationBase,
    IntegrationConfig,
    IntegrationResult,
    IntegrationType,
    AuthenticationType
)

# Platform connectors
from .salesforce import SalesforceConnector
from .dynamics365 import Dynamics365Connector
from .docusign import DocuSignConnector
from .slack import SlackConnector
from .teams import TeamsConnector
from .erp import SAPConnector, OracleERPConnector

__all__ = [
    # Webhook
    'WebhookService',
    'WebhookPayload',
    'WebhookSubscription',
    'WebhookEventType',
    'WebhookDeliveryResult',
    # Base
    'IntegrationBase',
    'IntegrationConfig',
    'IntegrationResult',
    'IntegrationType',
    'AuthenticationType',
    # Connectors
    'SalesforceConnector',
    'Dynamics365Connector',
    'DocuSignConnector',
    'SlackConnector',
    'TeamsConnector',
    'SAPConnector',
    'OracleERPConnector',
]
