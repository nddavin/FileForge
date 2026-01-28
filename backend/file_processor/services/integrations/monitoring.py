"""Monitoring & Operations Service - Alerting, Capacity Planning, Cost Analytics, and Anomaly Detection"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Tuple
import hashlib
import json
import logging
import math
import os
import secrets
import statistics
import threading
import time
import uuid

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(Enum):
    """Alert status"""

    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class AlertChannel(Enum):
    """Alert delivery channels"""

    PAGERDUTY = "pagerduty"
    SLACK = "slack"
    EMAIL = "email"
    WEBHOOK = "webhook"
    SMS = "sms"


class MetricType(Enum):
    """Types of metrics"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class AlertRule:
    """Alert rule configuration"""

    rule_id: str
    name: str
    description: str
    metric_name: str
    condition: str  # "gt", "lt", "eq", "gte", "lte", "change_percent"
    threshold: float
    severity: AlertSeverity
    channels: List[AlertChannel]
    evaluation_window: int = 300  # seconds
    cooldown_seconds: int = 300
    enabled: bool = True
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
    """Active alert instance"""

    alert_id: str
    rule_id: str
    rule_name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    metric_value: float
    metric_labels: Dict[str, str]
    started_at: str
    ended_at: Optional[str] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[str] = None
    notification_count: int = 0
    annotations: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricSample:
    """Single metric sample"""

    name: str
    value: float
    timestamp: str
    labels: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE


@dataclass
class CapacityMetrics:
    """System capacity metrics"""

    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    network_io: Dict[str, float] = field(default_factory=dict)
    active_connections: int = 0
    queue_depth: int = 0
    thread_pool_usage: float = 0.0
    database_connections_active: int = 0
    database_connections_idle: int = 0
    cache_hit_rate: float = 0.0
    api_latency_p50_ms: float = 0.0
    api_latency_p99_ms: float = 0.0
    error_rate_percent: float = 0.0
    request_rate_per_sec: float = 0.0
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class CostMetrics:
    """Cloud cost analytics"""

    compute_cost_hourly: float = 0.0
    storage_cost_monthly: float = 0.0
    network_egress_cost: float = 0.0
    api_calls_cost: float = 0.0
    database_cost: float = 0.0
    total_cost_day: float = 0.0
    total_cost_month: float = 0.0
    cost_by_service: Dict[str, float] = field(default_factory=dict)
    cost_trend_percent: float = 0.0
    forecasted_cost_month: float = 0.0
    budget_utilization_percent: float = 0.0
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class AnomalyDetection:
    """Anomaly detection configuration"""

    enabled: bool = True
    sensitivity: float = 0.5  # 0.0 to 1.0
    min_data_points: int = 10
    window_size: int = 3600  # seconds
    algorithms: List[str] = field(
        default_factory=lambda: ["zscore", "iqr", "isolation_forest"]
    )
    train_period_days: int = 7


@dataclass
class DetectedAnomaly:
    """Detected anomaly"""

    anomaly_id: str
    metric_name: str
    metric_labels: Dict[str, str]
    anomaly_type: str  # "spike", "drop", "trend_change", "seasonality_break", "outlier"
    severity: AlertSeverity
    confidence: float  # 0.0 to 1.0
    expected_value: float
    actual_value: float
    deviation_percent: float
    start_time: str
    end_time: Optional[str] = None
    recommended_action: str = ""
    affected_components: List[str] = field(default_factory=list)


class AlertingService:
    """Service for managing alerts and notifications"""

    def __init__(self):
        self._rules: Dict[str, AlertRule] = {}
        self._alerts: Dict[str, Alert] = {}
        self._notification_history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._callbacks: Dict[str, List[Callable]] = {}

    def create_alert_rule(
        self,
        name: str,
        metric_name: str,
        condition: str,
        threshold: float,
        severity: AlertSeverity,
        channels: List[AlertChannel],
        **kwargs,
    ) -> str:
        """Create a new alert rule"""
        rule_id = str(uuid.uuid4())

        rule = AlertRule(
            rule_id=rule_id,
            name=name,
            metric_name=metric_name,
            condition=condition,
            threshold=threshold,
            severity=severity,
            channels=channels,
            **kwargs,
        )

        with self._lock:
            self._rules[rule_id] = rule

        logger.info(f"Created alert rule: {name}")
        return rule_id

    def evaluate_rule(
        self,
        rule_id: str,
        current_value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> Optional[Alert]:
        """Evaluate an alert rule against current metric value"""
        with self._lock:
            if rule_id not in self._rules:
                return None

            rule = self._rules[rule_id]
            if not rule.enabled:
                return None

        # Check condition
        triggered = False
        if rule.condition == "gt" and current_value > rule.threshold:
            triggered = True
        elif rule.condition == "lt" and current_value < rule.threshold:
            triggered = True
        elif rule.condition == "eq" and current_value == rule.threshold:
            triggered = True
        elif rule.condition == "gte" and current_value >= rule.threshold:
            triggered = True
        elif rule.condition == "lte" and current_value <= rule.threshold:
            triggered = True
        elif rule.condition == "change_percent":
            # Would need historical data for this
            pass

        if not triggered:
            return None

        # Check if alert already exists and is not resolved
        with self._lock:
            for alert in self._alerts.values():
                if alert.rule_id == rule_id and alert.status not in [
                    AlertStatus.RESOLVED,
                    AlertStatus.SUPPRESSED,
                ]:
                    # Check cooldown
                    started = datetime.fromisoformat(alert.started_at)
                    if (
                        datetime.now(timezone.utc) - started
                    ).total_seconds() < rule.cooldown_seconds:
                        return None

        # Create new alert
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            rule_id=rule_id,
            rule_name=rule.name,
            severity=rule.severity,
            status=AlertStatus.TRIGGERED,
            message=f"{rule.name}: {current_value} {rule.condition} {rule.threshold}",
            metric_value=current_value,
            metric_labels=labels or {},
            started_at=datetime.now(timezone.utc).isoformat(),
            annotations=rule.annotations,
        )

        with self._lock:
            self._alerts[alert.alert_id] = alert

        # Send notifications
        self._send_notifications(alert, rule)

        return alert

    def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """Acknowledge an alert"""
        with self._lock:
            if alert_id not in self._alerts:
                return False

            alert = self._alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = user_id
            alert.acknowledged_at = datetime.now(timezone.utc).isoformat()

            self._notification_history.append(
                {
                    "alert_id": alert_id,
                    "action": "acknowledge",
                    "user_id": user_id,
                    "timestamp": alert.acknowledged_at,
                }
            )

            return True

    def resolve_alert(self, alert_id: str, user_id: str, note: str = "") -> bool:
        """Resolve an alert"""
        with self._lock:
            if alert_id not in self._alerts:
                return False

            alert = self._alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_by = user_id
            alert.resolved_at = datetime.now(timezone.utc).isoformat()

            self._notification_history.append(
                {
                    "alert_id": alert_id,
                    "action": "resolve",
                    "user_id": user_id,
                    "note": note,
                    "timestamp": alert.resolved_at,
                }
            )

            return True

    def get_active_alerts(
        self, severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """Get all active alerts"""
        with self._lock:
            alerts = [
                a
                for a in self._alerts.values()
                if a.status in [AlertStatus.TRIGGERED, AlertStatus.ACKNOWLEDGED]
            ]

            if severity:
                alerts = [a for a in alerts if a.severity == severity]

            return alerts

    def _send_notifications(self, alert: Alert, rule: AlertRule):
        """Send notifications through configured channels"""
        for channel in rule.channels:
            self._send_channel_notification(alert, channel, rule)
            alert.notification_count += 1

        self._notify_listeners("alert_triggered", alert)

    def _send_channel_notification(
        self, alert: Alert, channel: AlertChannel, rule: AlertRule
    ):
        """Send notification to a specific channel"""
        payload = {
            "alert_id": alert.alert_id,
            "rule_name": rule.name,
            "severity": alert.severity.value,
            "message": alert.message,
            "value": alert.metric_value,
            "timestamp": alert.started_at,
            "labels": alert.metric_labels,
        }

        if channel == AlertChannel.SLACK:
            self._send_slack_notification(payload)
        elif channel == AlertChannel.PAGERDUTY:
            self._send_pagerduty_notification(payload)
        elif channel == AlertChannel.WEBHOOK:
            self._send_webhook_notification(payload)

        self._notification_history.append(
            {
                "alert_id": alert.alert_id,
                "channel": channel.value,
                "payload": payload,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def _send_slack_notification(self, payload: Dict[str, Any]):
        """Send Slack notification (placeholder)"""
        logger.info(f"[SLACK] Alert: {payload['message']}")

    def _send_pagerduty_notification(self, payload: Dict[str, Any]):
        """Send PagerDuty notification (placeholder)"""
        logger.info(f"[PAGERDUTY] Alert: {payload['message']}")

    def _send_webhook_notification(self, payload: Dict[str, Any]):
        """Send webhook notification (placeholder)"""
        logger.info(f"[WEBHOOK] Alert: {payload['message']}")

    def register_callback(self, event: str, callback: Callable):
        """Register callback for alert events"""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)

    def _notify_listeners(self, event: str, data: Any):
        """Notify registered listeners"""
        for callback in self._callbacks.get(event, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")


class MetricsService:
    """Service for collecting and storing metrics"""

    def __init__(self, retention_days: int = 30):
        self._samples: List[MetricSample] = []
        self._lock = threading.Lock()
        self._retention_days = retention_days

    def record_metric(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        metric_type: MetricType = MetricType.GAUGE,
    ):
        """Record a metric sample"""
        sample = MetricSample(
            name=name,
            value=value,
            timestamp=datetime.now(timezone.utc).isoformat(),
            labels=labels or {},
            metric_type=metric_type,
        )

        with self._lock:
            self._samples.append(sample)

    def get_metric_values(
        self,
        name: str,
        since: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> List[MetricSample]:
        """Get metric values with optional filtering"""
        cutoff = (
            datetime.fromisoformat(since)
            if since
            else (datetime.now(timezone.utc) - timedelta(days=self._retention_days))
        )

        with self._lock:
            samples = [
                s
                for s in self._samples
                if s.name == name and datetime.fromisoformat(s.timestamp) >= cutoff
            ]

            if labels:
                for key, value in labels.items():
                    samples = [s for s in samples if s.labels.get(key) == value]

            return samples

    def get_metric_stats(
        self, name: str, since: Optional[str] = None
    ) -> Dict[str, float]:
        """Get statistics for a metric"""
        samples = self.get_metric_values(name, since)

        if not samples:
            return {}

        values = [s.value for s in samples]

        return {
            "count": len(values),
            "sum": sum(values),
            "avg": statistics.mean(values),
            "min": min(values),
            "max": max(values),
            "stddev": statistics.stdev(values) if len(values) > 1 else 0,
            "p50": statistics.median(values),
            "p95": sorted(values)[int(len(values) * 0.95)] if values else 0,
            "p99": sorted(values)[int(len(values) * 0.99)] if values else 0,
        }

    def cleanup_old_samples(self):
        """Remove samples older than retention period"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=self._retention_days)

        with self._lock:
            original_count = len(self._samples)
            self._samples = [
                s
                for s in self._samples
                if datetime.fromisoformat(s.timestamp) >= cutoff
            ]
            removed = original_count - len(self._samples)

        if removed > 0:
            logger.info(f"Cleaned up {removed} old metric samples")


class CapacityPlanningService:
    """Service for capacity planning and resource optimization"""

    def __init__(self):
        self._history: List[CapacityMetrics] = []
        self._lock = threading.Lock()
        self._thresholds = {
            "cpu_warning": 70.0,
            "cpu_critical": 90.0,
            "memory_warning": 80.0,
            "memory_critical": 95.0,
            "disk_warning": 80.0,
            "disk_critical": 95.0,
            "error_rate_warning": 1.0,
            "error_rate_critical": 5.0,
        }

    def record_capacity_metrics(self, metrics: CapacityMetrics):
        """Record capacity metrics snapshot"""
        with self._lock:
            self._history.append(metrics)

            # Keep last 30 days of data (assuming 1 sample per minute)
            max_samples = 30 * 24 * 60
            if len(self._history) > max_samples:
                self._history = self._history[-max_samples:]

    def get_current_capacity(self) -> CapacityMetrics:
        """Get current capacity metrics"""
        with self._lock:
            if not self._history:
                return CapacityMetrics(
                    cpu_usage_percent=0.0,
                    memory_usage_percent=0.0,
                    disk_usage_percent=0.0,
                )
            return self._history[-1]

    def get_capacity_trend(self, metric: str, hours: int = 24) -> Dict[str, Any]:
        """Get capacity trend for a metric"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        with self._lock:
            samples = [
                getattr(m, metric)
                for m in self._history
                if datetime.fromisoformat(m.timestamp) >= cutoff
            ]

        if not samples:
            return {"trend": "unknown", "change_percent": 0.0}

        first_half = samples[: len(samples) // 2]
        second_half = samples[len(samples) // 2 :]

        avg_first = statistics.mean(first_half) if first_half else 0
        avg_second = statistics.mean(second_half) if second_half else 0

        if avg_first == 0:
            return {"trend": "unknown", "change_percent": 0.0}

        change_percent = ((avg_second - avg_first) / avg_first) * 100

        if change_percent > 5:
            trend = "increasing"
        elif change_percent < -5:
            trend = "decreasing"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "change_percent": change_percent,
            "current": samples[-1] if samples else 0,
            "average": statistics.mean(samples),
            "min": min(samples),
            "max": max(samples),
        }

    def get_capacity_forecast(self, hours: int = 168) -> Dict[str, Any]:
        """Forecast capacity needs based on trends"""
        trends = {}
        for metric in [
            "cpu_usage_percent",
            "memory_usage_percent",
            "disk_usage_percent",
        ]:
            trends[metric] = self.get_capacity_trend(metric, hours=24)

        forecasts = {}
        for metric, trend_data in trends.items():
            if trend_data["trend"] == "increasing":
                # Simple linear extrapolation
                current = trend_data["current"]
                change_per_hour = trend_data["change_percent"] / 24
                forecast = current + (change_per_hour * hours)
                forecasts[metric] = min(100.0, max(0.0, forecast))
            else:
                forecasts[metric] = trend_data["current"]

        return {
            "forecasts": forecasts,
            "hours_ahead": hours,
            "recommendations": self._generate_recommendations(forecasts),
        }

    def _generate_recommendations(self, forecasts: Dict[str, float]) -> List[str]:
        """Generate capacity recommendations"""
        recommendations = []

        if forecasts.get("cpu_usage_percent", 0) > 80:
            recommendations.append(
                "Consider scaling up CPU resources or optimizing workloads"
            )

        if forecasts.get("memory_usage_percent", 0) > 85:
            recommendations.append(
                "Memory usage is high - consider adding RAM or optimizing memory usage"
            )

        if forecasts.get("disk_usage_percent", 0) > 80:
            recommendations.append(
                "Disk space is filling up - consider archival or expansion"
            )

        if not recommendations:
            recommendations.append("Current capacity is adequate for projected needs")

        return recommendations

    def get_capacity_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive capacity dashboard data"""
        current = self.get_current_capacity()
        forecast = self.get_capacity_forecast()

        return {
            "current": {
                "cpu_usage_percent": current.cpu_usage_percent,
                "memory_usage_percent": current.memory_usage_percent,
                "disk_usage_percent": current.disk_usage_percent,
                "active_connections": current.active_connections,
                "api_latency_p99_ms": current.api_latency_p99_ms,
                "error_rate_percent": current.error_rate_percent,
            },
            "trends": {
                m: self.get_capacity_trend(m)
                for m in [
                    "cpu_usage_percent",
                    "memory_usage_percent",
                    "error_rate_percent",
                ]
            },
            "forecast": forecast,
            "thresholds": self._thresholds,
        }


class CostAnalyticsService:
    """Service for cloud cost analytics and optimization"""

    def __init__(self, monthly_budget: float = 10000.0):
        self._daily_costs: List[CostMetrics] = []
        self._lock = threading.Lock()
        self._monthly_budget = monthly_budget
        self._cost_by_service: Dict[str, List[float]] = {}

    def record_cost_metrics(self, metrics: CostMetrics):
        """Record daily cost metrics"""
        with self._lock:
            self._daily_costs.append(metrics)

            for service, cost in metrics.cost_by_service.items():
                if service not in self._cost_by_service:
                    self._cost_by_service[service] = []
                self._cost_by_service[service].append(cost)

    def get_cost_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get cost summary for the past N days"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        with self._lock:
            recent_costs = [
                c
                for c in self._daily_costs
                if datetime.fromisoformat(c.timestamp) >= cutoff
            ]

        if not recent_costs:
            return {"total_cost": 0, "cost_by_day": [], "cost_by_service": {}}

        total_cost = sum(c.total_cost_day for c in recent_costs)
        avg_daily = total_cost / len(recent_costs)

        # Calculate trend
        if len(recent_costs) >= 7:
            first_week = recent_costs[:7]
            last_week = recent_costs[-7:]
            first_avg = sum(c.total_cost_day for c in first_week) / 7
            last_avg = sum(c.total_cost_day for c in last_week) / 7
            trend_percent = (
                ((last_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0
            )
        else:
            trend_percent = 0

        # Forecast
        daily_avg = total_cost / len(recent_costs)
        days_in_month = 30
        forecasted = daily_avg * days_in_month

        return {
            "total_cost": total_cost,
            "average_daily_cost": avg_daily,
            "days_analyzed": len(recent_costs),
            "trend_percent": trend_percent,
            "forecasted_monthly_cost": forecasted,
            "budget_utilization": (forecasted / self._monthly_budget) * 100,
            "cost_by_day": [
                {"date": c.timestamp[:10], "cost": c.total_cost_day}
                for c in recent_costs
            ],
            "cost_by_service": {
                service: sum(costs) for service, costs in self._cost_by_service.items()
            },
        }

    def get_cost_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Generate cost optimization recommendations"""
        recommendations = []

        with self._lock:
            recent_costs = self._daily_costs[-30:]

        if not recent_costs:
            return [{"action": "No cost data available", "potential_savings": 0}]

        # Analyze compute costs
        compute_costs = [c.compute_cost_hourly for c in recent_costs]
        avg_compute = statistics.mean(compute_costs) if compute_costs else 0

        if avg_compute > 100:  # Assuming $100/day average
            recommendations.append(
                {
                    "category": "Compute",
                    "action": "Consider reserved instances or spot instances for non-production workloads",
                    "potential_savings": f"${avg_compute * 0.3:.0f}/month",
                    "priority": "high",
                }
            )

        # Analyze storage costs
        storage_costs = [c.storage_cost_monthly for c in recent_costs]
        avg_storage = statistics.mean(storage_costs) if storage_costs else 0

        if avg_storage > 500:
            recommendations.append(
                {
                    "category": "Storage",
                    "action": "Implement lifecycle policies to move cold data to cheaper storage tiers",
                    "potential_savings": f"${avg_storage * 0.2:.0f}/month",
                    "priority": "medium",
                }
            )

        # Analyze network costs
        network_costs = [c.network_egress_cost for c in recent_costs]
        avg_network = statistics.mean(network_costs) if network_costs else 0

        if avg_network > 200:
            recommendations.append(
                {
                    "category": "Network",
                    "action": "Consider CDN implementation to reduce egress costs",
                    "potential_savings": f"${avg_network * 0.15:.0f}/month",
                    "priority": "medium",
                }
            )

        if not recommendations:
            recommendations.append(
                {
                    "category": "General",
                    "action": "Current costs are within expected ranges",
                    "potential_savings": "$0",
                    "priority": "low",
                }
            )

        return recommendations

    def get_cost_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive cost dashboard"""
        summary = self.get_cost_summary()
        recommendations = self.get_cost_optimization_recommendations()

        return {
            "summary": summary,
            "recommendations": recommendations,
            "budget": {
                "monthly_budget": self._monthly_budget,
                "utilization_percent": summary.get("budget_utilization", 0),
                "status": (
                    "over_budget"
                    if summary.get("budget_utilization", 0) > 100
                    else "under_budget"
                ),
            },
        }


class AnomalyDetectionService:
    """Service for AI-driven anomaly detection"""

    def __init__(self, config: Optional[AnomalyDetection] = None):
        self._config = config or AnomalyDetection()
        self._historical_data: Dict[str, List[float]] = {}
        self._detected_anomalies: List[DetectedAnomaly] = []
        self._lock = threading.Lock()
        self._training_data: Dict[str, List[Dict[str, Any]]] = {}

    def add_training_data(
        self,
        metric_name: str,
        value: float,
        timestamp: str,
        labels: Optional[Dict[str, str]] = None,
    ):
        """Add training data point for a metric"""
        key = f"{metric_name}:{hashlib.md5(json.dumps(labels or {}, sort_keys=True).encode()).hexdigest()[:8]}"

        with self._lock:
            if key not in self._training_data:
                self._training_data[key] = []

            self._training_data[key].append({"value": value, "timestamp": timestamp})

    def detect_anomaly(
        self,
        metric_name: str,
        current_value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> Optional[DetectedAnomaly]:
        """Detect if current value is anomalous"""
        if not self._config.enabled:
            return None

        key = f"{metric_name}:{hashlib.md5(json.dumps(labels or {}, sort_keys=True).encode()).hexdigest()[:8]}"

        with self._lock:
            historical = self._historical_data.get(key, [])
            if len(historical) < self._config.min_data_points:
                return None

        # Run detection algorithms
        anomaly = None
        for algorithm in self._config.algorithms:
            result = self._run_detection_algorithm(
                algorithm, historical, current_value, metric_name, key
            )
            if result:
                if not anomaly or result.confidence > anomaly.confidence:
                    anomaly = result

        if anomaly:
            with self._lock:
                self._detected_anomalies.append(anomaly)

        return anomaly

    def _run_detection_algorithm(
        self,
        algorithm: str,
        historical: List[float],
        current_value: float,
        metric_name: str,
        key: str,
    ) -> Optional[DetectedAnomaly]:
        """Run a specific detection algorithm"""
        if algorithm == "zscore":
            return self._zscore_detection(historical, current_value, metric_name, key)
        elif algorithm == "iqr":
            return self._iqr_detection(historical, current_value, metric_name, key)
        elif algorithm == "isolation_forest":
            return self._isolation_forest_detection(
                historical, current_value, metric_name, key
            )
        elif algorithm == "exponential_smoothing":
            return self._exp_smoothing_detection(
                historical, current_value, metric_name, key
            )

        return None

    def _zscore_detection(
        self, historical: List[float], current_value: float, metric_name: str, key: str
    ) -> Optional[DetectedAnomaly]:
        """Z-score based anomaly detection"""
        if len(historical) < 2:
            return None

        mean_val = statistics.mean(historical)
        std_val = statistics.stdev(historical)

        if std_val == 0:
            return None

        zscore = abs(current_value - mean_val) / std_val

        if zscore > (3 - self._config.sensitivity * 2):
            deviation = (
                ((current_value - mean_val) / mean_val * 100) if mean_val != 0 else 0
            )

            return DetectedAnomaly(
                anomaly_id=str(uuid.uuid4()),
                metric_name=metric_name,
                metric_labels={},
                anomaly_type="spike" if current_value > mean_val else "drop",
                severity=AlertSeverity.HIGH if zscore > 4 else AlertSeverity.MEDIUM,
                confidence=min(1.0, zscore / 5.0),
                expected_value=mean_val,
                actual_value=current_value,
                deviation_percent=deviation,
                start_time=datetime.now(timezone.utc).isoformat(),
                recommended_action="Investigate unusual metric behavior",
            )

        return None

    def _iqr_detection(
        self, historical: List[float], current_value: float, metric_name: str, key: str
    ) -> Optional[DetectedAnomaly]:
        """Interquartile range based anomaly detection"""
        if len(historical) < 4:
            return None

        sorted_vals = sorted(historical)
        q1 = statistics.quantiles(sorted_vals, n=4)[0]
        q3 = statistics.quantiles(sorted_vals, n=4)[2]
        iqr = q3 - q1

        lower_bound = q1 - (1.5 + self._config.sensitivity) * iqr
        upper_bound = q3 + (1.5 + self._config.sensitivity) * iqr

        if current_value < lower_bound or current_value > upper_bound:
            deviation = (
                (
                    (current_value - statistics.mean(historical))
                    / statistics.mean(historical)
                    * 100
                )
                if statistics.mean(historical) != 0
                else 0
            )

            return DetectedAnomaly(
                anomaly_id=str(uuid.uuid4()),
                metric_name=metric_name,
                metric_labels={},
                anomaly_type="outlier",
                severity=AlertSeverity.MEDIUM,
                confidence=0.7,
                expected_value=statistics.median(historical),
                actual_value=current_value,
                deviation_percent=deviation,
                start_time=datetime.now(timezone.utc).isoformat(),
                recommended_action="Review metric for unusual values",
            )

        return None

    def _isolation_forest_detection(
        self, historical: List[float], current_value: float, metric_name: str, key: str
    ) -> Optional[DetectedAnomaly]:
        """Simplified isolation forest-like anomaly detection"""
        if len(historical) < 5:
            return None

        # Calculate distance from nearest neighbors
        distances = [abs(current_value - v) for v in historical]
        avg_distance = statistics.mean(distances)
        max_distance = max(distances)

        if max_distance == 0:
            return None

        isolation_score = avg_distance / max_distance

        if isolation_score > (0.7 - self._config.sensitivity * 0.3):
            deviation = (
                (
                    (current_value - statistics.mean(historical))
                    / statistics.mean(historical)
                    * 100
                )
                if statistics.mean(historical) != 0
                else 0
            )

            return DetectedAnomaly(
                anomaly_id=str(uuid.uuid4()),
                metric_name=metric_name,
                metric_labels={},
                anomaly_type="outlier",
                severity=(
                    AlertSeverity.MEDIUM
                    if isolation_score < 0.9
                    else AlertSeverity.HIGH
                ),
                confidence=isolation_score,
                expected_value=statistics.mean(historical),
                actual_value=current_value,
                deviation_percent=deviation,
                start_time=datetime.now(timezone.utc).isoformat(),
                recommended_action="Isolate and investigate anomalous behavior",
            )

        return None

    def _exp_smoothing_detection(
        self, historical: List[float], current_value: float, metric_name: str, key: str
    ) -> Optional[DetectedAnomaly]:
        """Exponential smoothing based anomaly detection"""
        if len(historical) < 3:
            return None

        # Simple exponential smoothing
        alpha = 0.3
        smoothed = historical[0]
        for val in historical[1:]:
            smoothed = alpha * val + (1 - alpha) * smoothed

        error = abs(current_value - smoothed)
        recent_errors = [
            abs(historical[i] - historical[i - 1]) for i in range(1, len(historical))
        ]
        avg_error = statistics.mean(recent_errors) if recent_errors else 1

        if error > avg_error * (3 - self._config.sensitivity * 2):
            deviation = (
                ((current_value - smoothed) / smoothed * 100) if smoothed != 0 else 0
            )

            return DetectedAnomaly(
                anomaly_id=str(uuid.uuid4()),
                metric_name=metric_name,
                metric_labels={},
                anomaly_type="trend_change",
                severity=AlertSeverity.LOW,
                confidence=0.5,
                expected_value=smoothed,
                actual_value=current_value,
                deviation_percent=deviation,
                start_time=datetime.now(timezone.utc).isoformat(),
                recommended_action="Monitor for trend changes",
            )

        return None

    def get_recent_anomalies(
        self, since: Optional[str] = None, severity: Optional[AlertSeverity] = None
    ) -> List[DetectedAnomaly]:
        """Get recent detected anomalies"""
        cutoff = (
            datetime.fromisoformat(since)
            if since
            else (datetime.now(timezone.utc) - timedelta(hours=24))
        )

        with self._lock:
            anomalies = [
                a
                for a in self._detected_anomalies
                if datetime.fromisoformat(a.start_time) >= cutoff
            ]

            if severity:
                anomalies = [a for a in anomalies if a.severity == severity]

            return sorted(anomalies, key=lambda a: a.confidence, reverse=True)

    def get_anomaly_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive anomaly detection dashboard"""
        recent = self.get_recent_anomalies()

        by_severity = {}
        for anomaly in recent:
            if anomaly.severity not in by_severity:
                by_severity[anomaly.severity] = []
            by_severity[anomaly.severity].append(anomaly.anomaly_id)

        by_type = {}
        for anomaly in recent:
            if anomaly.anomaly_type not in by_type:
                by_anomaly_type[anomaly.anomaly_type] = []
            by_type[anomaly.anomaly_type].append(anomaly.anomaly_id)

        return {
            "total_anomalies": len(recent),
            "by_severity": {s.value: len(ids) for s, ids in by_severity.items()},
            "by_type": by_type,
            "recent_anomalies": [
                {
                    "id": a.anomaly_id,
                    "metric": a.metric_name,
                    "type": a.anomaly_type,
                    "severity": a.severity.value,
                    "confidence": a.confidence,
                    "deviation_percent": a.deviation_percent,
                }
                for a in recent[:10]
            ],
            "config": {
                "enabled": self._config.enabled,
                "sensitivity": self._config.sensitivity,
                "algorithms": self._config.algorithms,
            },
        }

    def update_config(self, **kwargs):
        """Update anomaly detection configuration"""
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)

    def add_historical_data_point(self, metric_name: str, value: float):
        """Add a historical data point for training"""
        with self._lock:
            if metric_name not in self._historical_data:
                self._historical_data[metric_name] = []
            self._historical_data[metric_name].append(value)

            # Keep only last 1000 points
            if len(self._historical_data[metric_name]) > 1000:
                self._historical_data[metric_name] = self._historical_data[metric_name][
                    -1000:
                ]


class MonitoringOrchestrator:
    """Orchestrates all monitoring services"""

    def __init__(self, monthly_budget: float = 10000.0):
        self.alerting = AlertingService()
        self.metrics = MetricsService()
        self.capacity = CapacityPlanningService()
        self.cost = CostAnalyticsService(monthly_budget)
        self.anomaly = AnomalyDetectionService()

        self._running = False
        self._collection_thread: Optional[threading.Thread] = None

    def start_background_collection(self, interval_seconds: int = 60):
        """Start background metric collection"""
        self._running = True
        self._collection_thread = threading.Thread(
            target=self._collection_loop, args=(interval_seconds,), daemon=True
        )
        self._collection_thread.start()

    def stop_background_collection(self):
        """Stop background collection"""
        self._running = False
        if self._collection_thread:
            self._collection_thread.join(timeout=5)

    def _collection_loop(self, interval_seconds: int):
        """Background collection loop"""
        while self._running:
            try:
                # Record current metrics (placeholder - would be replaced with real metrics)
                self._collect_system_metrics()
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")

            time.sleep(interval_seconds)

    def _collect_system_metrics(self):
        """Collect system metrics (placeholder implementation)"""
        import psutil

        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent

        # Record metrics
        self.metrics.record_metric("system.cpu_usage", cpu)
        self.metrics.record_metric("system.memory_usage", memory)
        self.metrics.record_metric("system.disk_usage", disk)

        # Update capacity
        self.capacity.record_capacity_metrics(
            CapacityMetrics(
                cpu_usage_percent=cpu,
                memory_usage_percent=memory,
                disk_usage_percent=disk,
            )
        )

        # Check for anomalies
        self.anomaly.add_historical_data_point("cpu_usage", cpu)
        self.anomaly.add_historical_data_point("memory_usage", memory)

        self.anomaly.detect_anomaly("cpu_usage", cpu)
        self.anomaly.detect_anomaly("memory_usage", memory)

    def get_full_dashboard(self) -> Dict[str, Any]:
        """Get complete monitoring dashboard"""
        return {
            "alerts": {
                "active_count": len(self.alerting.get_active_alerts()),
                "critical": len(
                    self.alerting.get_active_alerts(AlertSeverity.CRITICAL)
                ),
                "high": len(self.alerting.get_active_alerts(AlertSeverity.HIGH)),
            },
            "capacity": self.capacity.get_capacity_dashboard(),
            "cost": self.cost.get_cost_dashboard(),
            "anomalies": self.anomaly.get_anomaly_dashboard(),
        }
