"""Tests for integration services"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from backend.file_processor.services.integrations.webhook import (
    WebhookService,
    WebhookPayload,
    WebhookSubscription,
    WebhookEventType,
    WebhookDeliveryResult
)
from backend.file_processor.services.integrations.base import (
    IntegrationConfig,
    IntegrationResult,
    IntegrationBase,
    IntegrationType,
    AuthenticationType
)


class TestWebhookPayload:
    """Tests for WebhookPayload dataclass"""
    
    def test_create_payload(self):
        """Test creating a webhook payload"""
        payload = WebhookPayload(
            event_type=WebhookEventType.FILE_PROCESSED,
            data={"file_id": "123", "status": "completed"}
        )
        
        assert payload.event_type == WebhookEventType.FILE_PROCESSED
        assert payload.data["file_id"] == "123"
        assert payload.source == "fileforge"
        assert payload.event_id is not None
        assert payload.timestamp is not None
    
    def test_payload_to_dict(self):
        """Test converting payload to dictionary"""
        payload = WebhookPayload(
            event_type=WebhookEventType.WORKFLOW_COMPLETED,
            data={"workflow_id": "wf-1"}
        )
        
        result = payload.to_dict()
        
        assert result["event_type"] == "workflow.completed"
        assert result["data"]["workflow_id"] == "wf-1"
        assert result["source"] == "fileforge"
    
    def test_payload_to_json(self):
        """Test converting payload to JSON"""
        payload = WebhookPayload(
            event_type=WebhookEventType.FILE_UPLOADED,
            data={"filename": "test.pdf"}
        )
        
        json_str = payload.to_json()
        parsed = json.loads(json_str)
        
        assert parsed["event_type"] == "file.uploaded"
        assert parsed["data"]["filename"] == "test.pdf"
    
    def test_payload_from_dict(self):
        """Test creating payload from dictionary"""
        data = {
            "event_type": "file.deleted",
            "data": {"file_id": "456"},
            "metadata": {"user": "admin"}
        }
        
        payload = WebhookPayload.from_dict(data)
        
        assert payload.event_type == WebhookEventType.FILE_DELETED
        assert payload.data["file_id"] == "456"
        assert payload.metadata["user"] == "admin"


class TestWebhookSubscription:
    """Tests for WebhookSubscription dataclass"""
    
    def test_should_trigger_for_matching_event(self):
        """Test that subscription triggers for matching events"""
        subscription = WebhookSubscription(
            name="Test Webhook",
            url="https://example.com/webhook",
            events=[WebhookEventType.FILE_PROCESSED]
        )
        
        assert subscription.should_trigger(WebhookEventType.FILE_PROCESSED) is True
        assert subscription.should_trigger(WebhookEventType.FILE_DELETED) is False
    
    def test_should_trigger_for_custom_event(self):
        """Test that custom event subscription triggers for all events"""
        subscription = WebhookSubscription(
            name="Custom Webhook",
            url="https://example.com/webhook",
            events=[WebhookEventType.CUSTOM]
        )
        
        assert subscription.should_trigger(WebhookEventType.FILE_PROCESSED) is True
        assert subscription.should_trigger(WebhookEventType.WORKFLOW_STARTED) is True


class TestWebhookService:
    """Tests for WebhookService"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.webhook_service = WebhookService()
    
    def test_subscribe(self):
        """Test creating a webhook subscription"""
        subscription = self.webhook_service.subscribe(
            name="Test Webhook",
            url="https://example.com/webhook",
            events=[WebhookEventType.FILE_PROCESSED]
        )
        
        assert subscription.name == "Test Webhook"
        assert subscription.url == "https://example.com/webhook"
        assert WebhookEventType.FILE_PROCESSED in subscription.events
        assert subscription.secret is not None
        assert subscription.active is True
    
    def test_unsubscribe(self):
        """Test removing a webhook subscription"""
        subscription = self.webhook_service.subscribe(
            name="Test Webhook",
            url="https://example.com/webhook",
            events=[WebhookEventType.FILE_PROCESSED]
        )
        
        result = self.webhook_service.unsubscribe(subscription.id)
        
        assert result is True
        assert self.webhook_service.get_subscription(subscription.id) is None
    
    def test_unsubscribe_nonexistent(self):
        """Test removing a nonexistent subscription"""
        result = self.webhook_service.unsubscribe("nonexistent-id")
        
        assert result is False
    
    def test_list_subscriptions(self):
        """Test listing active subscriptions"""
        self.webhook_service.subscribe(
            name="Active Webhook",
            url="https://example.com/webhook1",
            events=[WebhookEventType.FILE_PROCESSED]
        )
        
        sub2 = self.webhook_service.subscribe(
            name="Inactive Webhook",
            url="https://example.com/webhook2",
            events=[WebhookEventType.FILE_UPLOADED]
        )
        sub2.active = False
        
        subscriptions = self.webhook_service.list_subscriptions()
        
        assert len(subscriptions) == 1
        assert subscriptions[0].name == "Active Webhook"
    
    def test_update_subscription(self):
        """Test updating a subscription"""
        subscription = self.webhook_service.subscribe(
            name="Original Name",
            url="https://example.com/webhook",
            events=[WebhookEventType.FILE_PROCESSED]
        )
        
        updated = self.webhook_service.update_subscription(
            subscription.id,
            name="Updated Name",
            active=False
        )
        
        assert updated.name == "Updated Name"
        assert updated.active is False
    
    def test_register_handler(self):
        """Test registering a local event handler"""
        handler = Mock()
        
        self.webhook_service.register_handler(
            WebhookEventType.FILE_PROCESSED,
            handler
        )
        
        assert WebhookEventType.FILE_PROCESSED in self.webhook_service._event_handlers
        assert handler in self.webhook_service._event_handlers[WebhookEventType.FILE_PROCESSED]
    
    def test_emit_triggers_handler(self):
        """Test that emit triggers registered handlers"""
        handler = Mock()
        
        self.webhook_service.register_handler(
            WebhookEventType.FILE_PROCESSED,
            handler
        )
        
        payload = WebhookPayload(
            event_type=WebhookEventType.FILE_PROCESSED,
            data={"test": "data"}
        )
        
        self.webhook_service.emit(payload)
        
        handler.assert_called_once_with(payload)
    
    def test_verify_signature(self):
        """Test webhook signature verification"""
        service = WebhookService()
        secret = "test-secret"
        payload = '{"event": "test"}'
        signature = service._generate_signature(payload, secret)
        
        assert service.verify_signature(payload, signature, secret) is True
    
    def test_get_statistics(self):
        """Test getting webhook statistics"""
        self.webhook_service.subscribe(
            name="Test Webhook",
            url="https://example.com/webhook",
            events=[WebhookEventType.FILE_PROCESSED]
        )
        
        stats = self.webhook_service.get_statistics()
        
        assert "total_deliveries" in stats
        assert "successful" in stats
        assert "failed" in stats
        assert "active_subscriptions" in stats
        assert stats["active_subscriptions"] == 1


class TestIntegrationConfig:
    """Tests for IntegrationConfig"""
    
    def test_create_config(self):
        """Test creating an integration configuration"""
        config = IntegrationConfig(
            integration_type=IntegrationType.CRM,
            auth_type=AuthenticationType.API_KEY,
            base_url="https://api.example.com",
            credentials={"api_key": "test-key"}
        )
        
        assert config.integration_type == IntegrationType.CRM
        assert config.auth_type == AuthenticationType.API_KEY
        assert config.base_url == "https://api.example.com"
        assert config.credentials["api_key"] == "test-key"
    
    def test_config_validation(self):
        """Test configuration validation"""
        with pytest.raises(ValueError):
            IntegrationConfig(
                integration_type=IntegrationType.CRM,
                auth_type=AuthenticationType.API_KEY,
                base_url="",  # Empty URL should fail
                credentials={"api_key": "test-key"}
            )
    
    def test_api_key_validation(self):
        """Test API key authentication validation"""
        with pytest.raises(ValueError):
            IntegrationConfig(
                integration_type=IntegrationType.CRM,
                auth_type=AuthenticationType.API_KEY,
                base_url="https://api.example.com",
                credentials={}  # Missing API key
            )


class TestIntegrationResult:
    """Tests for IntegrationResult"""
    
    def test_create_success_result(self):
        """Test creating a successful result"""
        result = IntegrationResult(
            success=True,
            data={"id": "123"},
            status_code=200
        )
        
        assert result.success is True
        assert result.data["id"] == "123"
        assert result.status_code == 200
        assert result.error is None
    
    def test_create_error_result(self):
        """Test creating an error result"""
        result = IntegrationResult(
            success=False,
            error="Connection failed",
            status_code=500
        )
        
        assert result.success is False
        assert result.error == "Connection failed"
        assert result.status_code == 500


class TestConnectors:
    """Tests for integration connectors"""
    
    def test_salesforce_connector_properties(self):
        """Test Salesforce connector properties"""
        from backend.file_processor.services.integrations import SalesforceConnector
        
        config = IntegrationConfig(
            integration_type=IntegrationType.CRM,
            auth_type=AuthenticationType.OAUTH2,
            base_url="https://login.salesforce.com",
            credentials={
                "client_id": "test-client-id",
                "client_secret": "test-client-secret"
            }
        )
        
        connector = SalesforceConnector(config)
        
        assert connector.integration_name == "Salesforce CRM"
        assert connector.integration_slug == "salesforce"
    
    def test_docusign_connector_properties(self):
        """Test DocuSign connector properties"""
        from backend.file_processor.services.integrations import DocuSignConnector
        
        config = IntegrationConfig(
            integration_type=IntegrationType.ESIGNATURE,
            auth_type=AuthenticationType.OAUTH2,
            base_url="https://demo.docusign.net/restapi",
            credentials={
                "integration_key": "test-key",
                "secret_key": "test-secret"
            }
        )
        
        connector = DocuSignConnector(config)
        
        assert connector.integration_name == "DocuSign"
        assert connector.integration_slug == "docusign"
    
    def test_slack_connector_properties(self):
        """Test Slack connector properties"""
        from backend.file_processor.services.integrations import SlackConnector
        
        config = IntegrationConfig(
            integration_type=IntegrationType.COLLABORATION,
            auth_type=AuthenticationType.BEARER_TOKEN,
            base_url="https://slack.com/api",
            credentials={"bot_token": "xoxb-test-token"}
        )
        
        connector = SlackConnector(config)
        
        assert connector.integration_name == "Slack"
        assert connector.integration_slug == "slack"
    
    def test_sap_connector_properties(self):
        """Test SAP connector properties"""
        from backend.file_processor.services.integrations import SAPConnector
        
        config = IntegrationConfig(
            integration_type=IntegrationType.ERP,
            auth_type=AuthenticationType.BASIC,
            base_url="https://sap.example.com",
            credentials={
                "username": "testuser",
                "password": "testpass"
            }
        )
        
        connector = SAPConnector(config)
        
        assert connector.integration_name == "SAP ERP"
        assert connector.integration_slug == "sap"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
