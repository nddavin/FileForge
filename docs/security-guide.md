# Security Guide

This document covers security features, best practices, configuration, and enterprise compliance for the FileForge application.

## 🔐 Authentication

### JWT Tokens

The application uses JWT (JSON Web Tokens) for authentication with enterprise-grade security:

- **Access Token**: Short-lived (default 30 minutes) for API access
- **Refresh Token**: Long-lived (default 7 days) for session persistence
- **Token Signing**: HS256 algorithm with 256-bit secret keys
- **Token Payload**:
```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "role": "admin",
  "permissions": ["read", "write", "delete", "admin"],
  "exp": 1234567890,
  "iat": 1234567890,
  "jti": "unique-token-id"
}
```

### Password Policy

Enterprise-grade password requirements:

| Requirement | Value | Description |
|------------|-------|-------------|
| Minimum Length | 12 characters | NIST SP 800-63B compliant |
| Uppercase | Required | At least 1 character |
| Lowercase | Required | At least 1 character |
| Numbers | Required | At least 1 digit |
| Special Characters | Required | At least 1 special char |
| Bcrypt Rounds | 12 | Computational cost factor |
| Maximum Age | 90 days | Password expiration |
| History | 10 passwords | Prevent password reuse |
| Lockout Threshold | 5 attempts | Account lockout after failures |
| Lockout Duration | 30 minutes | Automatic unlock time |

### Session Management

- Sessions expire after 30 minutes of inactivity
- Maximum 3 concurrent sessions per user
- Session invalidation on password change
- Secure session cookies with HttpOnly and Secure flags
- CSRF protection for all state-changing operations

## 🔒 Authorization

### Role-Based Access Control (RBAC)

The system implements a hierarchical RBAC model with three primary roles:

| Role | Description | Key Permissions |
|------|-------------|-----------------|
| **User** | Standard file processor | Upload, download, sort own files, create rules |
| **Manager** | Team oversight | Manage team files, view analytics, approve workflows |
| **Admin** | System administration | Full access including user management, system config |

### Detailed Permission Matrix

| Permission | User | Manager | Admin |
|------------|------|---------|-------|
| Upload Files | ✅ Own | ✅ Team | ✅ All |
| Download Files | ✅ Own | ✅ Team | ✅ All |
| Delete Files | ✅ Own | ✅ Team | ✅ All |
| View Files | ✅ Own | ✅ Team | ✅ All |
| Create Sorting Rules | ✅ | ✅ | ✅ |
| Edit Sorting Rules | ✅ Own | ✅ Team | ✅ All |
| Delete Sorting Rules | ✅ Own | ✅ Team | ✅ All |
| View Analytics | ❌ | ✅ Team | ✅ All |
| Manage Users | ❌ | ❌ | ✅ |
| Manage Roles | ❌ | ❌ | ✅ |
| System Configuration | ❌ | ❌ | ✅ |
| View Audit Logs | ❌ | ❌ | ✅ |
| Export Data | ✅ Own | ✅ Team | ✅ All |
| API Access | ✅ | ✅ | ✅ |

### Custom Permissions

Enterprise deployments can define custom permission sets:

```python
# Example custom permission definition
CUSTOM_PERMISSIONS = {
    "file_classification": ["read", "write"],
    "workflow_approval": ["read", "approve"],
    "compliance_reporting": ["read", "export"]
}
```

## 🛡️ Security Features

### File Upload Security

| Security Measure | Implementation | Validation |
|-----------------|----------------|------------|
| Filename Sanitization | Remove path traversal (`../`) | Regex pattern matching |
| MIME Type Validation | Content-based detection | Python `magic` library |
| File Signature Verification | Magic bytes validation | Configurable signatures |
| Size Limits | Configurable max file size | Default: 100MB |
| Type Restrictions | Whitelist of allowed types | Extension + MIME + signature |
| Content Scanning | Virus/malware detection | ClamAV integration |
| Malware Scanning | Real-time virus detection | Optional ClamAV daemon |
| Ransomware Protection | Extension blocking | Block .crypt, .locky, etc. |
| ZIP Bomb Detection | Recursive extraction limits | Max 10,000 files/folder |

### API Security

| Security Layer | Implementation | Configuration |
|---------------|----------------|---------------|
| Rate Limiting | slowapi + Redis | 100 req/min per user |
| Input Validation | Pydantic models | All endpoints |
| SQL Injection | SQLAlchemy ORM | Parameterized queries |
| XSS Prevention | Content-Type headers | Strict MIME types |
| CORS | FastAPI CORS middleware | Configurable origins |
| Request Size Limits | Maximum body size | 100MB default |
| Timeout Protection | Request timeouts | 300 seconds default |
| IP Allowlisting | Optional restrictions | Enterprise config |

### Data Protection

| Protection Type | Algorithm | Key Management |
|----------------|-----------|----------------|
| File Encryption | Fernet (AES-128-CBC) | Per-file keys derived from master |
| Database Encryption | PostgreSQL TDE | Transparent encryption |
| Field Encryption | AES-256-GCM | Application-level sensitive data |
| Key Storage | HashiCorp Vault (optional) | Enterprise secrets management |
| TLS | TLS 1.2/1.3 | Certificate-based |

#### Encryption Key Generation

```bash
# Generate Fernet encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Generate AES-256 key
python -c "import secrets; print(secrets.token_hex(32))"
```

### Audit Logging

All security-relevant actions are logged:

| Event Type | Fields Logged | Retention |
|-----------|---------------|-----------|
| Authentication | user_id, ip, timestamp, method, status | 7+ years |
| File Operations | user_id, file_id, action, ip, timestamp | 7+ years |
| Permission Changes | admin_id, target_user, change, timestamp | 7+ years |
| Configuration Changes | admin_id, setting, old_value, new_value | 7+ years |
| System Errors | error_type, stack_trace, timestamp | 1 year |
| Security Alerts | alert_type, severity, details, timestamp | 7+ years |

### Audit Log Format

```json
{
  "id": "audit-log-uuid",
  "timestamp": "2024-01-15T10:30:00Z",
  "user_id": "user123",
  "user_ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "action": "file_upload",
  "resource_type": "file",
  "resource_id": "file-uuid",
  "details": {
    "filename": "document.pdf",
    "size": 1048576,
    "mime_type": "application/pdf"
  },
  "status": "success",
  "risk_level": "low",
  "compliance_tags": ["GDPR", "HIPAA"]
}
```

## ⚙️ Configuration

### Environment Variables

```bash
# ============================================
# SECURITY CONFIGURATION
# ============================================

# Required - Encryption Keys
SECRET_KEY=$SECRET_KEY  # Generate: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=$JWT_SECRET_KEY  # Generate: python -c "import secrets; print(secrets.token_hex(32))"
ENCRYPTION_KEY=$ENCRYPTION_KEY  # Generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
AES_ENCRYPTION_KEY=$AES_ENCRYPTION_KEY  # Generate: python -c "import secrets; print(secrets.token_hex(32))"

# Required - Database Security
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require

# Optional - Token Configuration
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
TOKEN_REFRESH_THRESHOLD_MINUTES=5

# File Security
MAX_FILE_SIZE=104857600  # 100MB
ALLOWED_EXTENSIONS=pdf,docx,xlsx,jpg,png,mp4
ALLOWED_MIME_TYPES=application/pdf,application/vnd.openxmlformats-officedocument
MAX_UPLOAD_THREADS=4

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_BURST=20
RATE_LIMIT_STORAGE=redis://localhost:6379/1

# Session Security
SESSION_TIMEOUT_MINUTES=30
MAX_CONCURRENT_SESSIONS=3
SESSION_INACTIVITY_TIMEOUT=1800

# Password Policy
PASSWORD_MIN_LENGTH=12
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_NUMBER=true
PASSWORD_REQUIRE_SPECIAL=true
PASSWORD_MAX_AGE_DAYS=90
PASSWORD_HISTORY_COUNT=10
ACCOUNT_LOCKOUT_THRESHOLD=5
ACCOUNT_LOCKOUT_DURATION=1800

# Audit & Compliance
AUDIT_LOG_RETENTION_DAYS=2555  # 7+ years
ENABLE_COMPLIANCE_LOGGING=true
COMPLIANCE_FRAMEWORK=GDPR,HIPAA,SOX

# Optional - Vault Integration
VAULT_ENABLED=false
VAULT_ADDR=https://vault.fileforge.io
VAULT_TOKEN=your-vault-token

# Optional - External Scanning
CLAMAV_ENABLED=false
CLAMAV_HOST=localhost
CLAMAV_PORT=3310
```

## 🔧 Security Best Practices

### For Production

1. **Use HTTPS Only**
   ```nginx
   server {
       listen 443 ssl http2;
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_ciphers HIGH:!aNULL:!MD5;
       ssl_prefer_server_ciphers on;
       add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
   }
   ```

2. **Set Secure Headers**
   ```python
   from fastapi.middleware.trustedhost import TrustedHostMiddleware
   from fastapi.middleware.gzip import GZipMiddleware
   
   app.add_middleware(
       TrustedHostMiddleware,
       allowed_hosts=["fileforge.io", "*.fileforge.io"]
   )
   ```

3. **Enable Rate Limiting**
   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address, storage_uri="redis://localhost:6379/1")
   app.state.limiter = limiter
   ```

4. **Regular Security Updates**
   ```bash
   pip install --upgrade -r requirements.txt
   safety check -r requirements.txt
   ```

### Database Security

- Use PostgreSQL with SSL connection (`sslmode=require`)
- Create dedicated application user with minimal privileges
- Enable database audit logging
- Regular encrypted backups
- Network isolation (private subnets)

### File Storage Security

- Store uploads outside web root (`/var/fileforge/uploads`)
- Use separate partition with limited permissions (chmod 750)
- Implement file quarantine for suspicious files
- Regular cleanup of temporary files
- S3 with server-side encryption (SSE-S3 or SSE-KMS)

## 📋 Compliance Checklists

### GDPR Compliance

| Requirement | Implementation | Status |
|------------|----------------|--------|
| Data Minimization | Collect only required fields | ✅ |
| Purpose Limitation | Processing limited to declared purposes | ✅ |
| Storage Limitation | Configurable retention policies | ✅ |
| Right to Erasure | User-initiated data deletion | ✅ |
| Right to Portability | Export data in machine-readable format | ✅ |
| Consent Management | Document and manage user consent | ✅ |
| Data Protection Officer | Contact: dpo@fileforge-app.com | ✅ |
| Privacy Policy | Available at /privacy | ✅ |
| Data Processing Agreement | Available upon request | ✅ |
| Cross-border Transfers | Standard Contractual Clauses | ✅ |
| Data Breach Notification | 72-hour response procedure | ✅ |
| Processing Records | Maintained internally | ✅ |

### HIPAA Compliance

| Requirement | Implementation | Status |
|------------|----------------|--------|
| Access Controls | RBAC with unique user identification | ✅ |
| Audit Controls | Comprehensive audit logging | ✅ |
| Integrity Controls | File hash verification | ✅ |
| Transmission Security | TLS 1.2+ for all data in transit | ✅ |
| Encryption at Rest | AES-256 for PHI | ✅ |
| PHI Detection | Automatic detection and marking | ✅ |
| PHI Redaction | Automated redaction options | ✅ |
| Access Logs | 6-year retention minimum | ✅ |
| Emergency Access | Break-glass procedures documented | ✅ |
| Disposal Procedures | Secure file deletion | ✅ |
| Business Associate Agreements | Available for partners | ✅ |
| Risk Analysis | Annual security assessments | ✅ |

### GoBD Compliance (German Accounting Standards)

| Requirement | Implementation | Status |
|------------|----------------|--------|
| Audit Trail | Complete transaction logging | ✅ |
| Document Integrity | Immutable audit records | ✅ |
| Access Control | Role-based access | ✅ |
| Data Retention | Configurable retention periods | ✅ |
| Digital Signatures | Support for qualified signatures | ✅ |
| Time Stamping | Trusted time sources | ✅ |
| Archive Integrity | Hash verification for archives | ✅ |
| System Documentation | Complete system documentation | ✅ |

## 📊 Monitoring & Auditing

### Audit Log Events

| Category | Events |
|----------|--------|
| Authentication | login, logout, token_refresh, password_change, mfa_verify |
| File Operations | upload, download, view, move, rename, delete, restore |
| Rule Management | rule_create, rule_update, rule_delete, rule_execute |
| User Management | user_create, user_update, user_delete, user_disable |
| System Operations | config_change, backup, restore, maintenance |
| Security | suspicious_activity, malware_detected, brute_force_attempt |

### Alerting Configuration

Configure alerts for:

| Alert Type | Threshold | Response |
|------------|-----------|----------|
| Failed Logins | 5 attempts in 5 min | Account lockout + notification |
| Unusual File Access | 3x normal volume | Security review |
| Permission Escalation | Any attempt | Immediate alert |
| Malware Detection | Any detection | Quarantine + alert |
| Bulk Download | >100 files/hour | Rate limit + alert |
| Configuration Change | Any change | Audit log + notification |

### Log Format

```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "event_type": "security.alert",
  "severity": "high",
  "user_id": "user123",
  "user_ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "action": "file_upload",
  "resource_type": "file",
  "resource_id": "file-uuid-123",
  "outcome": "success",
  "risk_score": 15,
  "compliance_tags": ["GDPR", "HIPAA"],
  "details": {
    "filename": "document.pdf",
    "size": 1048576,
    "threat_scan_result": "clean"
  },
  "correlation_id": "corr-uuid-456"
}
```

## 🚨 Incident Response

### Reporting Security Issues

- **Email**: security@fileforge-app.com
- **GitHub**: Report through security advisory
- **PGP Key**: Available at security@fileforge-app.com/pgp.txt

### Response Procedure

1. **Acknowledge** - Response within 24 hours
2. **Assess** - Prioritize based on severity
3. **Contain** - Implement immediate mitigations
4. **Remediate** - Develop and test fixes
5. **Recover** - Restore normal operations
6. **Notify** - Communicate with affected parties
7. **Document** - Publish security advisory
8. **Review** - Post-incident analysis

### Severity Levels

| Level | Response Time | Examples |
|-------|---------------|----------|
| Critical | 1 hour | Data breach, active exploitation |
| High | 4 hours | Vulnerability with exploit |
| Medium | 24 hours | Significant weakness |
| Low | 72 hours | Minor improvement |

## 🧪 Security Testing

### Running Security Scans

```bash
# Docker security scan
docker-compose --profile security run --rm security-scan

# Dependency vulnerability check
pip install safety
safety check -r requirements.txt

# Static analysis
bandit -r file_forge/

# OWASP dependency check
dependency-check --project "FileForge" --scan .
```

### Penetration Testing

When conducting penetration tests:

1. Use dedicated staging environment
2. Coordinate with security team 48 hours in advance
3. Document all findings with severity
4. Follow responsible disclosure timeline
5. Share results with development team

### Security Assessment Schedule

| Assessment | Frequency | Provider |
|------------|-----------|----------|
| Automated Vulnerability Scan | Weekly | Internal |
| Penetration Test | Annually | Third-party |
| Code Review | Per release | Automated + Manual |
| Infrastructure Audit | Annually | Third-party |
| Compliance Audit | Annually | External Auditor |

## 📄 Data Processing Agreement (DPA)

### GDPR-Compliant DPA Template

**Data Controller**: [Customer Organization]
**Data Processor**: FileForge Application

#### 1. Subject Matter and Duration

| Aspect | Details |
|--------|---------|
| Subject Matter | Processing of files and associated metadata |
| Duration | Until termination of service agreement |
| Termination | Data deletion within 30 days of termination |

#### 2. Nature and Purpose

| Aspect | Details |
|--------|---------|
| Nature of Processing | Storage, categorization, retrieval of digital files |
| Purpose | Enterprise file management and workflow automation |
| Data Categories | File content, metadata, user credentials, audit logs |

#### 3. Data Subjects and Categories

| Category | Examples |
|----------|----------|
| User Data | Names, emails, authentication credentials |
| File Metadata | Filenames, sizes, types, timestamps |
| File Content | User-uploaded documents, images, videos |
| Audit Records | Actions, timestamps, IP addresses |

#### 4. PHI Redaction (Medical Files)

For HIPAA-compliant environments:

```python
# Automatic PHI detection and redaction
PHI_PATTERNS = [
    r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
    r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',  # Email
    r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone
]

def redact_phi(file_content: str) -> str:
    """Redact PHI patterns from file content."""
    for pattern in PHI_PATTERNS:
        file_content = re.sub(pattern, '[REDACTED]', file_content)
    return file_content
```

#### 5. Data Residency Options

| Region | Compliance | Availability |
|--------|------------|--------------|
| EU (Frankfurt) | GDPR | Standard |
| US (Virginia) | HIPAA, SOC 2 | Standard |
| UK (London) | UK GDPR | Standard |
| APAC (Singapore) | PDPA | Standard |
| On-Premise | Any | Enterprise |

#### 6. Audit Log Retention

| Log Type | Retention | Justification |
|----------|-----------|---------------|
| Authentication Logs | 7 years | Compliance requirement |
| File Operations | 7 years | Legal discovery |
| System Access | 7 years | Security auditing |
| Configuration Changes | 7 years | Change management |

## 🔐 Threat Model

### Assets

| Asset | Value | Sensitivity |
|-------|-------|-------------|
| User Credentials | High | Critical |
| File Content | High | Varies by file |
| Encryption Keys | Critical | Critical |
| Audit Logs | High | Compliance |
| System Config | Medium | Internal |

### Threats

| Threat | Likelihood | Impact | Mitigation |
|--------|------------|--------|------------|
| Unauthorized Access | Medium | Critical | RBAC, MFA |
| Data Breach | Low | Critical | Encryption, monitoring |
| Malware Upload | Medium | High | File scanning, validation |
| DoS Attack | Medium | High | Rate limiting, scaling |
| Insider Threat | Low | Critical | Audit logging, access control |
| Data Loss | Low | High | Backups, redundancy |
| API Abuse | Medium | Medium | Rate limiting, monitoring |

### Attack Vectors

1. **Path Traversal**
   - Mitigation: Input validation, path normalization
   - Testing: `/api/files?path=../../../etc/passwd`

2. **File Upload Abuse**
   - Mitigation: Content-type validation, magic bytes
   - Testing: Malicious file extensions, embedded scripts

3. **Authentication Bypass**
   - Mitigation: JWT validation, token refresh limits
   - Testing: Token manipulation, replay attacks

4. **SQL Injection**
   - Mitigation: ORM with parameterized queries
   - Testing: SQL injection payloads

5. **Cross-Site Scripting (XSS)**
   - Mitigation: Output encoding, CSP headers
   - Testing: Script injection in file names

6. **CSRF Attacks**
   - Mitigation: CSRF tokens, SameSite cookies
   - Testing: Cross-site request forgery attempts

## 📞 Security Contacts

| Contact | Purpose | Response Time |
|---------|---------|---------------|
| security@fileforge-app.com | Security issues | 24 hours |
| dpo@fileforge-app.com | Privacy/DPO | 48 hours |
| support@fileforge-app.com | General support | 24 hours |
| emergency@fileforge-app.com | Critical incidents | 1 hour |
