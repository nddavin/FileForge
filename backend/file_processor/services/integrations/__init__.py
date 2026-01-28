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
from .ha import (
    HealthStatus,
    CircuitState,
    Endpoint,
    FailoverConfig,
    HAResult,
    CircuitBreaker,
    LoadBalancer,
    HighAvailabilityMixin,
    ClusterConfig,
    ClusterManager
)
from .ha_service import (
    NodeState,
    ReplicationMode,
    ClusterNode,
    ReplicationConfig,
    FailoverPolicy,
    HAMetrics,
    HAClusterService,
    DnsFailoverService
)
from .compliance import (
    ComplianceStandard,
    DataClassification,
    RetentionPolicyAction,
    RetentionPolicy,
    ConsentRecord,
    AuditLogEntry,
    DLPConfig,
    WatermarkConfig,
    FederatedIdentityConfig,
    ComplianceService
)
from .user_experience import (
    SharePermission,
    ShareLinkStatus,
    ShareLinkConfig,
    FileVersion,
    Comment,
    CollaborationSession,
    SharingService,
    VersioningService,
    CollaborationService
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
    # High Availability
    'HealthStatus',
    'CircuitState',
    'Endpoint',
    'FailoverConfig',
    'HAResult',
    'CircuitBreaker',
    'LoadBalancer',
    'HighAvailabilityMixin',
    'ClusterConfig',
    'ClusterManager',
    # HA Service
    'NodeState',
    'ReplicationMode',
    'ClusterNode',
    'ReplicationConfig',
    'FailoverPolicy',
    'HAMetrics',
    'HAClusterService',
    'DnsFailoverService',
    # Compliance
    'ComplianceStandard',
    'DataClassification',
    'RetentionPolicyAction',
    'RetentionPolicy',
    'ConsentRecord',
    'AuditLogEntry',
    'DLPConfig',
    'WatermarkConfig',
    'FederatedIdentityConfig',
    'ComplianceService',
    # User Experience
    'SharePermission',
    'ShareLinkStatus',
    'ShareLinkConfig',
    'FileVersion',
    'Comment',
    'CollaborationSession',
    'SharingService',
    'VersioningService',
    'CollaborationService',
    # Connectors
    'SalesforceConnector',
    'Dynamics365Connector',
    'DocuSignConnector',
    'SlackConnector',
    'TeamsConnector',
    'SAPConnector',
    'OracleERPConnector',
]
