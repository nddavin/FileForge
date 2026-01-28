"""Webhook service for handling incoming and outgoing webhooks"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import hashlib
import hmac
import json
import logging
import uuid

logger = logging.getLogger(__name__)


class WebhookEventType(Enum):
    """Types of webhook events"""

    # File events
    FILE_UPLOADED = "file.uploaded"
    FILE_PROCESSED = "file.processed"
    FILE_DELETED = "file.deleted"
    FILE_CLASSIFIED = "file.classified"

    # Workflow events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    WORKFLOW_STEP_COMPLETED = "workflow.step.completed"

    # Integration events
    INTEGRATION_CONNECTED = "integration.connected"
    INTEGRATION_DISCONNECTED = "integration.disconnected"
    INTEGRATION_ERROR = "integration.error"

    # Custom events
    CUSTOM = "custom"


@dataclass
class WebhookPayload:
    """Payload structure for webhooks"""

    event_type: WebhookEventType
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = "fileforge"

    def to_dict(self) -> Dict[str, Any]:
        """Convert payload to dictionary"""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "event_id": self.event_id,
            "data": self.data,
            "metadata": self.metadata,
            "source": self.source,
        }

    def to_json(self) -> str:
        """Convert payload to JSON string"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebhookPayload":
        """Create payload from dictionary"""
        return cls(
            event_type=WebhookEventType(data.get("event_type", "custom")),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            event_id=data.get("event_id", str(uuid.uuid4())),
            data=data.get("data", {}),
            metadata=data.get("metadata", {}),
            source=data.get("source", "fileforge"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "WebhookPayload":
        """Create payload from JSON string"""
        return cls.from_dict(json.loads(json_str))


@dataclass
class WebhookSubscription:
    """Webhook subscription configuration"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    url: str = ""
    events: List[WebhookEventType] = field(default_factory=list)
    secret: str = ""
    active: bool = True
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_triggered: Optional[str] = None
    failure_count: int = 0
    headers: Dict[str, str] = field(default_factory=dict)

    def should_trigger(self, event_type: WebhookEventType) -> bool:
        """Check if this subscription should trigger for the event"""
        return event_type in self.events or WebhookEventType.CUSTOM in self.events


@dataclass
class WebhookDeliveryResult:
    """Result of webhook delivery"""

    subscription_id: str
    success: bool
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    error: Optional[str] = None
    duration_ms: float = 0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    retry_attempted: bool = False


class WebhookService:
    """Service for managing webhooks"""

    def __init__(self):
        self._subscriptions: Dict[str, WebhookSubscription] = {}
        self._event_handlers: Dict[
            WebhookEventType, List[Callable[[WebhookPayload], None]]
        ] = {}
        self._delivery_history: List[WebhookDeliveryResult] = []
        self._max_history: int = 1000

    def subscribe(
        self,
        name: str,
        url: str,
        events: List[WebhookEventType],
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> WebhookSubscription:
        """Create a new webhook subscription"""
        secret = secret or self._generate_secret()
        subscription = WebhookSubscription(
            name=name, url=url, events=events, secret=secret, headers=headers or {}
        )
        self._subscriptions[subscription.id] = subscription
        logger.info(f"Created webhook subscription: {subscription.id} for {name}")
        return subscription

    def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a webhook subscription"""
        if subscription_id in self._subscriptions:
            del self._subscriptions[subscription_id]
            logger.info(f"Removed webhook subscription: {subscription_id}")
            return True
        return False

    def get_subscription(self, subscription_id: str) -> Optional[WebhookSubscription]:
        """Get a webhook subscription by ID"""
        return self._subscriptions.get(subscription_id)

    def list_subscriptions(self) -> List[WebhookSubscription]:
        """List all active webhook subscriptions"""
        return [sub for sub in self._subscriptions.values() if sub.active]

    def update_subscription(
        self, subscription_id: str, **kwargs: Any
    ) -> Optional[WebhookSubscription]:
        """Update a webhook subscription"""
        subscription = self._subscriptions.get(subscription_id)
        if not subscription:
            return None

        for key, value in kwargs.items():
            if hasattr(subscription, key) and key not in ["id"]:
                setattr(subscription, key, value)

        return subscription

    def trigger(
        self, payload: WebhookPayload, http_client: Optional[Any] = None
    ) -> List[WebhookDeliveryResult]:
        """Trigger webhooks for an event"""
        results: List[WebhookDeliveryResult] = []

        for subscription in self._subscriptions.values():
            if not subscription.active:
                continue
            if not subscription.should_trigger(payload.event_type):
                continue

            result = self._deliver_webhook(subscription, payload, http_client)
            results.append(result)

            # Update subscription
            subscription.last_triggered = result.timestamp
            if not result.success:
                subscription.failure_count += 1
                if subscription.failure_count >= 10:
                    subscription.active = False
                    logger.warning(
                        f"Webhook {subscription.id} disabled due to too many failures"
                    )

        self._delivery_history.extend(results)
        if len(self._delivery_history) > self._max_history:
            self._delivery_history = self._delivery_history[-self._max_history :]

        return results

    def register_handler(
        self, event_type: WebhookEventType, handler: Callable[[WebhookPayload], None]
    ) -> None:
        """Register a local event handler"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    def emit(self, payload: WebhookPayload) -> None:
        """Emit a webhook event (triggers both local handlers and webhooks)"""
        # Call local handlers
        event_handlers = self._event_handlers.get(payload.event_type, [])
        event_handlers.extend(self._event_handlers.get(WebhookEventType.CUSTOM, []))

        for handler in event_handlers:
            try:
                handler(payload)
            except Exception as e:
                logger.error(f"Error in webhook handler: {e}")

        # Trigger webhooks
        self.trigger(payload)

    def _deliver_webhook(
        self,
        subscription: WebhookSubscription,
        payload: WebhookPayload,
        http_client: Optional[Any],
    ) -> WebhookDeliveryResult:
        """Deliver a webhook to a subscription"""
        import time

        start_time = time.time()

        # Generate signature
        signature = self._generate_signature(payload.to_json(), subscription.secret)

        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Event": payload.event_type.value,
            "X-Webhook-Event-ID": payload.event_id,
            "X-Webhook-Signature": f"sha256={signature}",
            "X-Webhook-Timestamp": payload.timestamp,
            **subscription.headers,
        }

        # If no HTTP client provided, use httpx
        if http_client is None:
            try:
                import httpx

                with httpx.Client(timeout=30) as client:
                    response = client.post(
                        subscription.url, content=payload.to_json(), headers=headers
                    )
                    duration_ms = (time.time() - start_time) * 1000

                    return WebhookDeliveryResult(
                        subscription_id=subscription.id,
                        success=200 <= response.status_code < 300,
                        status_code=response.status_code,
                        response_body=response.text[:1000] if response.text else None,
                        duration_ms=duration_ms,
                    )
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                return WebhookDeliveryResult(
                    subscription_id=subscription.id,
                    success=False,
                    error=str(e),
                    duration_ms=duration_ms,
                    retry_attempted=True,
                )

        # Use provided HTTP client
        try:
            response = http_client.post(
                subscription.url, json=payload.to_dict(), headers=headers
            )
            duration_ms = (time.time() - start_time) * 1000

            return WebhookDeliveryResult(
                subscription_id=subscription.id,
                success=200 <= response.status_code < 300,
                status_code=response.status_code,
                response_body=response.text[:1000] if response.text else None,
                duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return WebhookDeliveryResult(
                subscription_id=subscription.id,
                success=False,
                error=str(e),
                duration_ms=duration_ms,
                retry_attempted=True,
            )

    def _generate_secret(self) -> str:
        """Generate a random secret for webhook signing"""
        import secrets

        return secrets.token_urlsafe(32)

    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook payload"""
        return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

    def verify_signature(self, payload: str, signature: str, secret: str) -> bool:
        """Verify webhook signature"""
        expected = f"sha256={self._generate_signature(payload, secret)}"
        return hmac.compare_digest(expected, signature)

    def get_delivery_history(
        self, subscription_id: Optional[str] = None, limit: int = 100
    ) -> List[WebhookDeliveryResult]:
        """Get webhook delivery history"""
        history = self._delivery_history

        if subscription_id:
            history = [h for h in history if h.subscription_id == subscription_id]

        return history[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get webhook statistics"""
        total = len(self._delivery_history)
        successful = sum(1 for h in self._delivery_history if h.success)
        failed = total - successful

        return {
            "total_deliveries": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total > 0 else 0,
            "active_subscriptions": len(self.list_subscriptions()),
            "event_types": {},
        }
