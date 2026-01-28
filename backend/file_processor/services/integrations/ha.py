"""High Availability and Resilience for Enterprise Integrations"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar
import logging
import time
import random
import threading

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status of a service"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class Endpoint:
    """Load-balanced endpoint configuration"""

    url: str
    weight: int = 1
    health: HealthStatus = HealthStatus.HEALTHY
    failure_count: int = 0
    last_failure: Optional[str] = None
    latency_avg_ms: float = 0
    request_count: int = 0

    def is_healthy(self) -> bool:
        """Check if endpoint is healthy"""
        return self.health == HealthStatus.HEALTHY and self.failure_count < 3


@dataclass
class FailoverConfig:
    """Configuration for failover behavior"""

    max_retries: int = 3
    retry_delay_ms: int = 1000
    max_retry_delay_ms: int = 10000
    exponential_base: float = 2.0
    circuit_open_after_failures: int = 5
    circuit_half_open_requests: int = 3
    circuit_reset_timeout_ms: int = 30000
    fallback_enabled: bool = True
    timeout_ms: int = 30000


@dataclass
class HAResult:
    """Result from HA-aware operation"""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    endpoint_used: Optional[str] = None
    attempt_number: int = 1
    latency_ms: float = 0
    from_cache: bool = False
    circuit_state: CircuitState = CircuitState.CLOSED


class CircuitBreaker:
    """Circuit breaker for preventing cascade failures"""

    def __init__(
        self,
        name: str,
        config: FailoverConfig,
        health_check: Optional[Callable[[], bool]] = None,
    ):
        self.name = name
        self.config = config
        self.health_check = health_check
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        if self._state == CircuitState.OPEN:
            # Check if we should transition to half_open
            if self._last_failure_time:
                elapsed = (time.time() - self._last_failure_time) * 1000
                if elapsed >= self.config.circuit_reset_timeout_ms:
                    self._state = CircuitState.HALF_OPEN
        return self._state

    def record_success(self):
        """Record a successful request"""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.circuit_half_open_requests:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    logger.info(f"Circuit {self.name}: closed (recovered)")
            else:
                self._failure_count = max(0, self._failure_count - 1)

    def record_failure(self):
        """Record a failed request"""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning(f"Circuit {self.name}: opened (half-open failed)")
            elif self._failure_count >= self.config.circuit_open_after_failures:
                self._state = CircuitState.OPEN
                logger.warning(f"Circuit {self.name}: opened (threshold reached)")

    def allow_request(self) -> bool:
        """Check if a request should be allowed"""
        if self._state == CircuitState.CLOSED:
            return True
        if self._state == CircuitState.OPEN:
            return False
        # HALF_OPEN - allow limited requests
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure": self._last_failure_time,
        }


class LoadBalancer:
    """Weighted round-robin load balancer with health checks"""

    def __init__(self, endpoints: List[Endpoint]):
        self.endpoints = endpoints
        self._current_index = 0
        self._lock = threading.Lock()

    def get_next(self) -> Optional[Endpoint]:
        """Get the next healthy endpoint"""
        with self._lock:
            if not self.endpoints:
                return None

            # Try to find a healthy endpoint
            attempts = len(self.endpoints)
            for _ in range(attempts):
                endpoint = self.endpoints[self._current_index]
                self._current_index = (self._current_index + 1) % len(self.endpoints)

                if endpoint.is_healthy():
                    endpoint.request_count += 1
                    return endpoint

            # All endpoints unhealthy, return least bad one
            endpoint = min(self.endpoints, key=lambda e: e.failure_count)
            endpoint.request_count += 1
            return endpoint

    def mark_failure(self, endpoint: Endpoint):
        """Mark an endpoint as failed"""
        endpoint.failure_count += 1
        endpoint.last_failure = datetime.now(timezone.utc).isoformat()
        endpoint.health = (
            HealthStatus.DEGRADED
            if endpoint.failure_count < 5
            else HealthStatus.UNHEALTHY
        )

    def mark_success(self, endpoint: Endpoint, latency_ms: float):
        """Mark an endpoint as successful"""
        # Update moving average latency
        endpoint.latency_avg_ms = (endpoint.latency_avg_ms * 0.7) + (latency_ms * 0.3)
        endpoint.failure_count = max(0, endpoint.failure_count - 1)
        endpoint.health = HealthStatus.HEALTHY

    def get_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics"""
        return {
            "total_endpoints": len(self.endpoints),
            "healthy_endpoints": sum(1 for e in self.endpoints if e.is_healthy()),
            "endpoints": [
                {
                    "url": e.url,
                    "healthy": e.is_healthy(),
                    "failure_count": e.failure_count,
                    "latency_avg_ms": e.latency_avg_ms,
                    "request_count": e.request_count,
                }
                for e in self.endpoints
            ],
        }


class HighAvailabilityMixin(ABC):
    """Mixin providing HA features for connectors"""

    def __init__(self, *args, **kwargs):
        self._ha_config = kwargs.pop("ha_config", None)
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._load_balancers: Dict[str, LoadBalancer] = {}
        self._fallback_handlers: Dict[str, Callable] = {}
        self._request_cache: Dict[str, tuple] = {}
        self._cache_ttl_seconds = 300
        super().__init__(*args, **kwargs)

    def add_circuit_breaker(
        self, name: str, health_check: Optional[Callable[[], bool]] = None
    ) -> CircuitBreaker:
        """Add a circuit breaker for an endpoint"""
        config = self._ha_config or FailoverConfig()
        cb = CircuitBreaker(name, config, health_check)
        self._circuit_breakers[name] = cb
        return cb

    def add_load_balancer(self, name: str, endpoints: List[Endpoint]) -> LoadBalancer:
        """Add a load balancer for multiple endpoints"""
        lb = LoadBalancer(endpoints)
        self._load_balancers[name] = lb
        return lb

    def register_fallback(self, operation: str, handler: Callable[[Exception], Any]):
        """Register a fallback handler for an operation"""
        self._fallback_handlers[operation] = handler

    def _execute_with_ha(
        self,
        operation: str,
        executor: Callable[[], Any],
        circuit_name: Optional[str] = None,
        endpoint_name: Optional[str] = None,
        use_cache: bool = False,
        cache_key: Optional[str] = None,
    ) -> HAResult:
        """Execute an operation with HA features"""
        start_time = time.time()
        attempt = 0
        circuit = self._circuit_breakers.get(circuit_name) if circuit_name else None

        # Check cache
        if use_cache and cache_key and cache_key in self._request_cache:
            cached_data, timestamp = self._request_cache[cache_key]
            if time.time() - timestamp < self._cache_ttl_seconds:
                return HAResult(
                    success=True,
                    data=cached_data,
                    from_cache=True,
                    circuit_state=circuit._state if circuit else CircuitState.CLOSED,
                )

        # Execute with retries
        while attempt < (self._ha_config.max_retries if self._ha_config else 3):
            attempt += 1

            # Check circuit breaker
            if circuit and not circuit.allow_request():
                return HAResult(
                    success=False,
                    error=f"Circuit {circuit_name} is open",
                    attempt_number=attempt,
                    circuit_state=circuit.state,
                )

            # Get load-balanced endpoint
            endpoint = None
            if endpoint_name:
                lb = self._load_balancers.get(endpoint_name)
                if lb:
                    endpoint = lb.get_next()

            try:
                # Execute the operation
                result = executor()

                # Record success
                if circuit:
                    circuit.record_success()
                if endpoint:
                    latency_ms = (time.time() - start_time) * 1000
                    lb.mark_success(endpoint, latency_ms)

                # Update cache
                if use_cache and cache_key:
                    self._request_cache[cache_key] = (result, time.time())

                return HAResult(
                    success=True,
                    data=result,
                    endpoint_used=endpoint.url if endpoint else None,
                    attempt_number=attempt,
                    latency_ms=(time.time() - start_time) * 1000,
                    circuit_state=circuit._state if circuit else CircuitState.CLOSED,
                )

            except Exception as e:
                logger.warning(f"Operation {operation} failed (attempt {attempt}): {e}")

                # Record failure
                if circuit:
                    circuit.record_failure()
                if endpoint:
                    lb.mark_failure(endpoint)

                # Check for fallback
                if operation in self._fallback_handlers:
                    try:
                        fallback_result = self._fallback_handlers[operation](e)
                        return HAResult(
                            success=True,
                            data=fallback_result,
                            error=f"From fallback: {str(e)}",
                            endpoint_used=endpoint.url if endpoint else None,
                            attempt_number=attempt,
                        )
                    except Exception as fallback_error:
                        logger.error(f"Fallback failed: {fallback_error}")

                # Calculate retry delay with exponential backoff
                if attempt < (self._ha_config.max_retries if self._ha_config else 3):
                    delay_ms = self._calculate_retry_delay(attempt)
                    time.sleep(delay_ms / 1000)

        # All retries exhausted
        return HAResult(
            success=False,
            error=f"Operation failed after {attempt} attempts",
            attempt_number=attempt,
            circuit_state=circuit.state if circuit else CircuitState.CLOSED,
        )

    def _calculate_retry_delay(self, attempt: int) -> int:
        """Calculate retry delay with exponential backoff and jitter"""
        if not self._ha_config:
            return 1000

        base_delay = self._ha_config.retry_delay_ms
        max_delay = self._ha_config.max_retry_delay_ms
        base = self._ha_config.exponential_base

        delay = base_delay * (base ** (attempt - 1))
        delay = min(delay, max_delay)

        # Add jitter (random variation)
        jitter = random.uniform(-0.2, 0.2) * delay
        return int(delay + jitter)

    def get_ha_stats(self) -> Dict[str, Any]:
        """Get HA statistics for all circuits and load balancers"""
        return {
            "circuits": {
                name: cb.get_stats() for name, cb in self._circuit_breakers.items()
            },
            "load_balancers": {
                name: lb.get_stats() for name, lb in self._load_balancers.items()
            },
            "cache_size": len(self._request_cache),
        }


@dataclass
class ClusterConfig:
    """Configuration for multi-region clustering"""

    region: str
    primary_region: str
    failover_regions: List[str]
    health_check_interval_seconds: int = 30
    failover_threshold_percent: int = 90
    dns_ttl_seconds: int = 60


class ClusterManager:
    """Manages multi-region cluster failover"""

    def __init__(self, config: ClusterConfig):
        self.config = config
        self._region_status: Dict[str, HealthStatus] = {}
        self._active_region = config.primary_region
        self._lock = threading.Lock()

    def register_region(self, region: str, status: HealthStatus = HealthStatus.UNKNOWN):
        """Register a region"""
        self._region_status[region] = status

    def update_region_health(self, region: str, status: HealthStatus):
        """Update health status of a region"""
        with self._lock:
            self._region_status[region] = status

            # Check for failover
            if region == self._active_region and status != HealthStatus.HEALTHY:
                self._check_failover()

    def _check_failover(self):
        """Check if we need to failover to another region"""
        healthy_regions = [
            r
            for r in self.config.failover_regions
            if self._region_status.get(r, HealthStatus.UNKNOWN) == HealthStatus.HEALTHY
        ]

        if healthy_regions:
            self._active_region = healthy_regions[0]
            logger.warning(f"Failed over to region: {self._active_region}")

    def get_active_region(self) -> str:
        """Get the currently active region"""
        return self._active_region

    def get_region_status(self) -> Dict[str, Any]:
        """Get status of all regions"""
        return {
            "active_region": self._active_region,
            "regions": {
                region: status.value for region, status in self._region_status.items()
            },
        }
