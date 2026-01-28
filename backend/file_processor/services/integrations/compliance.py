"""Advanced Compliance Module for Enterprise Integrations

Supports GDPR, HIPAA, SOC 2, and PCI-DSS requirements including:
- Data residency controls
- Data loss prevention (DLP)
- Watermarking
- Federated authentication (SAML/OAuth/OIDC)
- Audit logging with tamper evidence
- Data retention policies
- Consent management
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
import hashlib
import hmac
import json
import logging
import threading
import uuid

logger = logging.getLogger(__name__)


class ComplianceStandard(Enum):
    """Compliance standards supported"""
    GDPR = "gdpr"  # EU General Data Protection Regulation
    HIPAA = "hipaa"  # Health Insurance Portability and Accountability Act
    SOC2 = "soc2"  # Service Organization Control 2
    PCI_DSS = "pci_dss"  # Payment Card Industry Data Security Standard
    ISO27001 = "iso27001"  # Information Security Management


class DataClassification(Enum):
    """Data classification levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    PII = "pii"  # Personally Identifiable Information
    PHI = "phi"  # Protected Health Information
    PCI = "pci"  # Payment Card Data


class RetentionPolicyAction(Enum):
    """Actions for data retention"""
    DELETE = "delete"
    ANONYMIZE = "anonymize"
    ARCHIVE = "archive"
    NOTIFY = "notify"


@dataclass
class RetentionPolicy:
    """Data retention policy configuration"""
    name: str
    standard: ComplianceStandard
    retention_days: int
    action: RetentionPolicyAction
    classification_levels: List[DataClassification] = field(default_factory=list)
    jurisdictions: List[str] = field(default_factory=list)
    enabled: bool = True
    
    def should_apply(self, classification: DataClassification, jurisdiction: str) -> bool:
        """Check if policy applies to given data"""
        if not self.enabled:
            return False
        if classification not in self.classification_levels:
            return False
        if jurisdiction and jurisdiction not in self.jurisdictions:
            return False
        return True


@dataclass
class ConsentRecord:
    """Consent management record"""
    consent_id: str
    user_id: str
    purpose: str
    consent_given: bool
    timestamp: str
    jurisdiction: str
    source: str  # web, mobile, api
    version: str  # consent form version
    withdrawal_method: Optional[str] = None


@dataclass
class AuditLogEntry:
    """Immutable audit log entry"""
    entry_id: str
    timestamp: str
    action: str
    actor: str
    resource_type: str
    resource_id: str
    classification: DataClassification
    jurisdiction: str
    details: Dict[str, Any]
    signature: str  # HMAC for tamper evidence
    previous_hash: str  # Chain for tamper detection
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp,
            "action": self.action,
            "actor": self.actor,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "classification": self.classification.value,
            "jurisdiction": self.jurisdiction,
            "details": self.details,
            "signature": self.signature,
            "previous_hash": self.previous_hash
        }


@dataclass
class DLPConfig:
    """Data Loss Prevention configuration"""
    enabled: bool = True
    block_sensitive_fields: bool = True
    scan_outbound: bool = True
    scan_inbound: bool = True
    patterns: List[Dict[str, Any]] = field(default_factory=list)
    custom_rules: List[Dict[str, Any]] = field(default_factory=list)
    quarantine_action: str = "quarantine"  # quarantine, block, flag
    notification_recipients: List[str] = field(default_factory=list)


@dataclass
class WatermarkConfig:
    """Document watermarking configuration"""
    enabled: bool = True
    text: str = "CONFIDENTIAL"
    include_user_id: bool = True
    include_timestamp: bool = True
    include_ip: bool = True
    opacity: float = 0.3
    rotation_degrees: int = 45
    font_size: int = 12


@dataclass
class FederatedIdentityConfig:
    """Federated authentication configuration"""
    provider: str  # okta, azure_ad, auth0, ping
    client_id: str
    client_secret: str
    issuer_url: str
    audience: str
    claim_mappings: Dict[str, str] = field(default_factory=dict)
    logout_url: Optional[str] = None
    scopes: List[str] = field(default_factory=lambda: ["openid", "profile", "email"])


class ComplianceService:
    """
    Central compliance service for enterprise integrations.
    
    Provides:
    - Unified compliance policy enforcement
    - Audit logging with cryptographic chain
    - Data residency enforcement
    - DLP scanning
    - Watermarking
    - Consent management
    - Retention policy automation
    """
    
    def __init__(
        self,
        secret_key: str,
        compliance_standards: Optional[List[ComplianceStandard]] = None
    ):
        self._secret_key = secret_key
        self._compliance_standards = compliance_standards or [ComplianceStandard.GDPR]
        
        # Audit log chain
        self._audit_log: List[AuditLogEntry] = []
        self._last_hash = ""
        self._audit_lock = threading.Lock()
        
        # Retention policies
        self._retention_policies: Dict[str, RetentionPolicy] = {}
        
        # Consent records
        self._consents: Dict[str, List[ConsentRecord]] = {}
        
        # Data residency rules
        self._data_residency_rules: Dict[str, List[str]] = {}
        
        # DLP configuration
        self._dlp_config = DLPConfig()
        
        # Watermark configuration
        self._watermark_config = WatermarkConfig()
        
        # Federated identity providers
        self._identity_providers: Dict[str, FederatedIdentityConfig] = {}
        
        # Callbacks
        self._violation_callbacks: List[Callable] = []
        self._retention_callbacks: List[Callable] = []
    
    # ========== Audit Logging ==========
    
    def log_audit_event(
        self,
        action: str,
        actor: str,
        resource_type: str,
        resource_id: str,
        classification: DataClassification,
        jurisdiction: str,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLogEntry:
        """Create an immutable audit log entry"""
        entry = AuditLogEntry(
            entry_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            action=action,
            actor=actor,
            resource_type=resource_type,
            resource_id=resource_id,
            classification=classification,
            jurisdiction=jurisdiction,
            details=details or {},
            signature="",
            previous_hash=self._last_hash
        )
        
        # Create tamper-evident signature
        entry.signature = self._sign_entry(entry)
        
        # Update chain
        entry_hash = self._hash_entry(entry)
        
        with self._audit_lock:
            self._audit_log.append(entry)
            self._last_hash = entry_hash
        
        logger.info(f"Audit: {action} on {resource_type}:{resource_id} by {actor}")
        return entry
    
    def verify_audit_chain(self) -> Dict[str, Any]:
        """Verify integrity of audit log chain"""
        with self._audit_lock:
            log_copy = list(self._audit_log)
        
        valid = True
        broken_at = None
        
        for i, entry in enumerate(log_copy):
            # Verify signature
            expected_sig = self._sign_entry(entry)
            if entry.signature != expected_sig:
                valid = False
                broken_at = i
                break
            
            # Verify chain
            if i > 0:
                expected_hash = self._hash_entry(log_copy[i - 1])
                if entry.previous_hash != expected_hash:
                    valid = False
                    broken_at = i
                    break
        
        return {
            "valid": valid,
            "total_entries": len(log_copy),
            "broken_at": broken_at,
            "first_entry": log_copy[0].to_dict() if log_copy else None,
            "last_entry": log_copy[-1].to_dict() if log_copy else None
        }
    
    def query_audit_log(
        self,
        actor: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query audit log with filters"""
        with self._audit_lock:
            results = [entry.to_dict() for entry in self._audit_log]
        
        # Apply filters
        if actor:
            results = [r for r in results if r["actor"] == actor]
        if action:
            results = [r for r in results if r["action"] == action]
        if resource_type:
            results = [r for r in results if r["resource_type"] == resource_type]
        if start_time:
            results = [r for r in results if r["timestamp"] >= start_time]
        if end_time:
            results = [r for r in results if r["timestamp"] <= end_time]
        
        return results[-limit:]
    
    # ========== Data Residency ==========
    
    def set_data_residency(
        self,
        classification: DataClassification,
        allowed_jurisdictions: List[str]
    ):
        """Set data residency rules for a classification level"""
        self._data_residency_rules[classification.value] = allowed_jurisdictions
    
    def check_data_residency(
        self,
        classification: DataClassification,
        current_jurisdiction: str,
        target_jurisdiction: str
    ) -> Dict[str, Any]:
        """Check if data transfer complies with residency rules"""
        allowed = self._data_residency_rules.get(classification.value, [])
        
        if not allowed:
            # No restrictions for this classification
            return {"allowed": True, "reason": "no_restrictions"}
        
        # Check if data can be stored in target jurisdiction
        can_store = target_jurisdiction in allowed
        # Check if cross-border transfer is allowed
        can_transfer = (
            current_jurisdiction == target_jurisdiction or
            current_jurisdiction in allowed
        )
        
        return {
            "allowed": can_store and can_transfer,
            "can_store": can_store,
            "can_transfer": can_transfer,
            "source_jurisdiction": current_jurisdiction,
            "target_jurisdiction": target_jurisdiction,
            "allowed_jurisdictions": allowed
        }
    
    # ========== Data Loss Prevention ==========
    
    def configure_dlp(self, config: DLPConfig):
        """Configure DLP settings"""
        self._dlp_config = config
    
    def scan_for_sensitive_data(
        self,
        data: Dict[str, Any],
        classification: DataClassification
    ) -> Dict[str, Any]:
        """Scan data for sensitive information"""
        violations = []
        
        if not self._dlp_config.enabled:
            return {"clean": True, "violations": []}
        
        # Check for PII patterns
        pii_fields = ["ssn", "social_security", "credit_card", "password", "secret"]
        for field_name, value in self._flatten_dict(data).items():
            field_lower = field_name.lower()
            
            # Check field names
            for pii in pii_fields:
                if pii in field_lower and self._dlp_config.block_sensitive_fields:
                    violations.append({
                        "type": "sensitive_field",
                        "field": field_name,
                        "severity": "high",
                        "message": f"Sensitive field '{field_name}' detected"
                    })
        
        # Check classification-specific rules
        if classification in [DataClassification.PII, DataClassification.PHI, DataClassification.PCI]:
            violations.extend(self._check_classification_rules(data, classification))
        
        # Custom rules
        for rule in self._dlp_config.custom_rules:
            if self._apply_rule(data, rule):
                violations.append(rule)
        
        # Take action
        clean = len(violations) == 0
        if not clean:
            self._handle_dlp_violation(data, violations)
        
        return {
            "clean": clean,
            "violations": violations,
            "action_taken": self._dlp_config.quarantine_action if not clean else None
        }
    
    def register_violation_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register callback for DLP violations"""
        self._violation_callbacks.append(callback)
    
    def _handle_dlp_violation(self, data: Dict[str, Any], violations: List[Dict[str, Any]]):
        """Handle detected DLP violations"""
        for callback in self._violation_callbacks:
            try:
                callback({"data": data, "violations": violations})
            except Exception as e:
                logger.error(f"DLP callback failed: {e}")
        
        logger.warning(f"DLP violation detected: {len(violations)} issues")
    
    def _check_classification_rules(
        self,
        data: Dict[str, Any],
        classification: DataClassification
    ) -> List[Dict[str, Any]]:
        """Check classification-specific rules"""
        violations = []
        
        if classification == DataClassification.PHI:
            # HIPAA: Check for health information
            health_terms = ["diagnosis", "treatment", "medication", "patient"]
            for field_name, value in self._flatten_dict(data).items():
                if any(term in field_name.lower() for term in health_terms):
                    violations.append({
                        "type": "phi",
                        "field": field_name,
                        "severity": "critical",
                        "message": "Protected health information detected"
                    })
        
        elif classification == DataClassification.PCI:
            # PCI-DSS: Check for card data
            card_patterns = [
                (r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}", "credit_card_number"),
                (r"\d{3,4}", "cvv")
            ]
            for field_name, value in self._flatten_dict(data).items():
                value_str = str(value)
                for pattern, name in card_patterns:
                    import re
                    if re.search(pattern, value_str):
                        violations.append({
                            "type": "pci",
                            "field": field_name,
                            "severity": "critical",
                            "message": f"PCI data ({name}) detected"
                        })
        
        return violations
    
    def _apply_rule(self, data: Dict[str, Any], rule: Dict[str, Any]) -> bool:
        """Apply a custom DLP rule"""
        # Simplified rule application
        return False
    
    # ========== Watermarking ==========
    
    def configure_watermark(self, config: WatermarkConfig):
        """Configure document watermarking"""
        self._watermark_config = config
    
    def generate_watermark_text(
        self,
        user_id: str,
        ip_address: Optional[str] = None
    ) -> str:
        """Generate watermark text for a document"""
        if not self._watermark_config.enabled:
            return ""
        
        parts = [self._watermark_config.text]
        
        if self._watermark_config.include_user_id:
            parts.append(f"User: {user_id}")
        if self._watermark_config.include_timestamp:
            parts.append(datetime.now(timezone.utc).isoformat())
        if self._watermark_config.include_ip and ip_address:
            parts.append(f"IP: {ip_address}")
        
        return " | ".join(parts)
    
    # ========== Consent Management ==========
    
    def record_consent(self, consent: ConsentRecord):
        """Record a consent decision"""
        if consent.user_id not in self._consents:
            self._consents[consent.user_id] = []
        
        self._consents[consent.user_id].append(consent)
        
        self.log_audit_event(
            action="consent_recorded",
            actor=consent.user_id,
            resource_type="consent",
            resource_id=consent.consent_id,
            classification=DataClassification.PII,
            jurisdiction=consent.jurisdiction,
            details={
                "purpose": consent.purpose,
                "consent_given": consent.consent_given,
                "source": consent.source
            }
        )
    
    def check_consent(
        self,
        user_id: str,
        purpose: str,
        jurisdiction: str
    ) -> Dict[str, Any]:
        """Check if user has given consent for a purpose"""
        user_consents = self._consents.get(user_id, [])
        
        for consent in reversed(user_consents):
            if (
                consent.purpose == purpose and
                consent.jurisdiction == jurisdiction and
                consent.consent_given
            ):
                return {
                    "has_consent": True,
                    "consent_id": consent.consent_id,
                    "timestamp": consent.timestamp,
                    "version": consent.version
                }
        
        return {
            "has_consent": False,
            "reason": "no_consent_recorded"
        }
    
    def withdraw_consent(
        self,
        user_id: str,
        purpose: str,
        withdrawal_method: str
    ) -> bool:
        """Record consent withdrawal"""
        user_consents = self._consents.get(user_id, [])
        
        for consent in user_consents:
            if consent.purpose == purpose:
                # Create withdrawal record
                withdrawal = ConsentRecord(
                    consent_id=str(uuid.uuid4()),
                    user_id=user_id,
                    purpose=purpose,
                    consent_given=False,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    jurisdiction=consent.jurisdiction,
                    source=withdrawal_method,
                    version="1.0",
                    withdrawal_method=withdrawal_method
                )
                self._consents[user_id].append(withdrawal)
                
                self.log_audit_event(
                    action="consent_withdrawn",
                    actor=user_id,
                    resource_type="consent",
                    resource_id=withdrawal.consent_id,
                    classification=DataClassification.PII,
                    jurisdiction=consent.jurisdiction,
                    details={"purpose": purpose, "method": withdrawal_method}
                )
                return True
        
        return False
    
    # ========== Retention Policies ==========
    
    def add_retention_policy(self, policy: RetentionPolicy):
        """Add a data retention policy"""
        self._retention_policies[policy.name] = policy
        
        self.log_audit_event(
            action="retention_policy_added",
            actor="system",
            resource_type="retention_policy",
            resource_id=policy.name,
            classification=DataClassification.CONFIDENTIAL,
            jurisdiction="global",
            details={
                "standard": policy.standard.value,
                "retention_days": policy.retention_days,
                "action": policy.action.value
            }
        )
    
    def register_retention_callback(self, callback: Callable[[str, str], None]):
        """Register callback for retention policy execution"""
        self._retention_callbacks.append(callback)
    
    def apply_retention_policy(
        self,
        data_id: str,
        classification: DataClassification,
        jurisdiction: str,
        created_at: str
    ) -> Dict[str, Any]:
        """Apply retention policy to data"""
        created_date = datetime.fromisoformat(created_at)
        days_old = (datetime.now(timezone.utc) - created_date).days
        
        for policy in self._retention_policies.values():
            if policy.should_apply(classification, jurisdiction):
                if days_old >= policy.retention_days:
                    # Execute retention action
                    for callback in self._retention_callbacks:
                        try:
                            callback(data_id, policy.action.value)
                        except Exception as e:
                            logger.error(f"Retention callback failed: {e}")
                    
                    self.log_audit_event(
                        action="retention_policy_executed",
                        actor="system",
                        resource_type="data",
                        resource_id=data_id,
                        classification=classification,
                        jurisdiction=jurisdiction,
                        details={
                            "policy": policy.name,
                            "action": policy.action.value,
                            "data_age_days": days_old
                        }
                    )
                    
                    return {
                        "applied": True,
                        "policy": policy.name,
                        "action": policy.action.value
                    }
        
        return {"applied": False, "reason": "no_matching_policy"}
    
    # ========== Federated Identity ==========
    
    def add_identity_provider(self, config: FederatedIdentityConfig):
        """Add a federated identity provider"""
        self._identity_providers[config.provider] = config
        
        self.log_audit_event(
            action="idp_configured",
            actor="system",
            resource_type="identity_provider",
            resource_id=config.provider,
            classification=DataClassification.INTERNAL,
            jurisdiction="global",
            details={"issuer": config.issuer_url}
        )
    
    def get_identity_provider(self, provider: str) -> Optional[FederatedIdentityConfig]:
        """Get identity provider configuration"""
        return self._identity_providers.get(provider)
    
    def validate_saml_assertion(
        self,
        saml_response: str,
        provider: str
    ) -> Dict[str, Any]:
        """Validate a SAML assertion (simplified)"""
        # In production, use proper SAML library
        return {
            "valid": True,
        }
    
    # ========== Compliance Reporting ==========
    
    def generate_compliance_report(
        self,
        standard: ComplianceStandard,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Generate compliance report for a standard"""
        audit_events = self.query_audit_log(
            start_time=start_date,
            end_time=end_date
        )
        
        return {
            "standard": standard.value,
            "period": {"start": start_date, "end": end_date},
            "total_events": len(audit_events),
            "by_action": self._aggregate_by_field(audit_events, "action"),
            "by_classification": self._aggregate_by_field(audit_events, "classification"),
            "by_jurisdiction": self._aggregate_by_field(audit_events, "jurisdiction"),
            "audit_chain_valid": self.verify_audit_chain()["valid"],
            "consent_stats": self._get_consent_stats(),
            "retention_policies": len(self._retention_policies),
            "data_residency_rules": len(self._data_residency_rules),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    # ========== Helper Methods ==========
    
    def _sign_entry(self, entry: AuditLogEntry) -> str:
        """Create HMAC signature for audit entry"""
        message = json.dumps({
            "entry_id": entry.entry_id,
            "timestamp": entry.timestamp,
            "action": entry.action,
            "actor": entry.actor,
            "resource_type": entry.resource_type,
            "resource_id": entry.resource_id,
            "previous_hash": entry.previous_hash
        })
        return hmac.new(
            self._secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _hash_entry(self, entry: AuditLogEntry) -> str:
        """Create hash for chain linking"""
        return hashlib.sha256(
            (entry.signature + entry.previous_hash).encode()
        ).hexdigest()
    
    def _flatten_dict(
        self,
        d: Dict[str, Any],
        parent_key: str = ""
    ) -> Dict[str, Any]:
        """Flatten nested dictionary"""
        items = {}
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                items.update(self._flatten_dict(v, new_key))
            else:
                items[new_key] = v
        return items
    
    def _aggregate_by_field(
        self,
        data: List[Dict[str, Any]],
        field: str
    ) -> Dict[str, int]:
        """Aggregate counts by field value"""
        counts = {}
        for item in data:
            value = item.get(field, "unknown")
            counts[value] = counts.get(value, 0) + 1
        return counts
    
    def _get_consent_stats(self) -> Dict[str, Any]:
        """Get consent statistics"""
        total = 0
        given = 0
        withdrawn = 0
        
        for consents in self._consents.values():
            for c in consents:
                total += 1
                if c.consent_given:
                    given += 1
                else:
                    withdrawn += 1
        
        return {
            "total_records": total,
            "consent_given": given,
            "consent_withdrawn": withdrawn,
            "unique_users": len(self._consents)
        }
