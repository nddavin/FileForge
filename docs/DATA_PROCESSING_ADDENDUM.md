# Data Processing Agreement (DPA)

## FileForge Church Data Protection Addendum

**Version:** 1.0  
**Effective Date:** January 2024

---

## 1. Parties

| Role | Entity | Details |
|------|--------|---------|
| **Data Controller** | [Customer Church/Organization] | You, as the church using FileForge |
| **Data Processor** | FileForge Application | We process data on your behalf |

---

## 2. Purpose and Scope

### 2.1 Subject Matter

The processing concerns the FileForge Enterprise Sermon Processing Platform, including:

| Service | Description |
|---------|-------------|
| File Storage | Audio/video sermon archives |
| Metadata Processing | Extraction, categorization, search indexing |
| AI Processing | Speaker identification, transcription |
| Distribution | Podcast feeds, streaming |

### 2.2 Nature of Processing

| Category | Details |
|----------|---------|
| Collection | Upload of sermon files and metadata |
| Storage | Secure cloud storage with encryption |
| Processing | Transcoding, metadata extraction, AI analysis |
| Retrieval | Search, download, categorization |
| Deletion | Upon request or account termination |

### 2.3 Duration

| Phase | Duration |
|-------|----------|
| Service Agreement | Per subscription term |
| Post-Termination | 30-day data export, 90-day deletion |

---

## 3. Data Categories

### 3.1 Personal Data

| Category | Examples | Processing Purpose |
|----------|----------|--------------------|
| User Accounts | Name, email, password | Authentication |
| Speaker Profiles | Voice samples, name, title | Identification |
| Administrative | Staff roles, permissions | Access control |

### 3.2 Church Data

| Category | Examples | Processing Purpose |
|----------|----------|--------------------|
| Sermon Files | Audio/video recordings | Processing services |
| Series Information | Series titles, dates | Organization |
| Sermon Metadata | Scripture references, topics | Search & retrieval |
| Member Information | Speaker names, contributors | Attribution |

### 3.3 Sensitive Data (Optional)

| Category | Examples | Protection Level |
|----------|----------|------------------|
| Medical Information | Hospital chaplains, pastoral counseling | HIPAA compliance |
| Financial Data | Donation records, budgets | Enhanced encryption |
| Counseling Notes | Confidential pastoral care records | Restricted access |

---

## 4. Data Processing Principles

### 4.1 Compliance with Law

FileForge shall:

| Requirement | Implementation |
|-------------|----------------|
| Lawful Processing | Only on Controller instructions |
| Data Minimization | Collect only necessary data |
| Purpose Limitation | Use only for declared purposes |
| Accuracy | Maintain accurate data |
| Storage Limitation | Delete when no longer needed |
| Integrity & Confidentiality | Appropriate security measures |

### 4.2 Controller Instructions

Processing shall only occur upon instructions from the Controller, unless required by:

- EU or member state law
- Court order
- Legal obligation

### 4.3 Sub-Processors

FileForge uses the following sub-processors:

| Sub-Processor | Service | Data Shared | Compliance |
|---------------|---------|-------------|------------|
| AWS | Cloud Hosting | Processing data | SOC 2, ISO 27001 |
| Supabase | Database | User data | SOC 2 |
| OpenAI | Transcription | Audio content | SOC 2, HIPAA |
| SendGrid | Email | Notification data | SOC 2 |
| Sentry | Monitoring | Error logs | SOC 2 |

---

## 5. Data Subject Rights

### 5.1 Controller Responsibilities

The Data Controller is responsible for:

| Right | Controller Action |
|-------|-------------------|
| Access | Provide copy to data subject |
| Rectification | Correct inaccurate data |
| Erasure | Delete data upon request |
| Restriction | Limit processing |
| Portability | Export machine-readable data |
| Objection | Handle opt-out requests |

### 5.2 Processor Assistance

FileForge shall assist the Controller in:

| Obligation | Method |
|------------|--------|
| Security | Audit logs, access controls |
| Breach Notification | Alert within 24 hours |
| Data Subject Requests | API access, export tools |
| DPIA Support | Documentation, risk assessment |

---

## 6. Security Measures

### 6.1 Technical Measures

| Measure | Implementation |
|---------|----------------|
| Encryption | AES-256 at rest, TLS 1.3 in transit |
| Access Control | RBAC, MFA, session management |
| Network Security | Firewalls, intrusion detection |
| Backup | Daily encrypted backups |
| Logging | Comprehensive audit trail |

### 6.2 Organizational Measures

| Measure | Implementation |
|---------|----------------|
| Training | Annual security awareness |
| Access Management | Principle of least privilege |
| Incident Response | Documented procedures |
| Vendor Management | Due diligence, contracts |

### 6.3 Security Certifications

| Certification | Scope | Expiry |
|---------------|-------|--------|
| SOC 2 Type II | Security, availability | Annual |
| ISO 27001 | Information security | Annual |
| HIPAA | Healthcare data | Annual |

---

## 7. Data Transfers

### 7.1 Transfer Mechanisms

| From | To | Mechanism |
|------|-----|-----------|
| EU | US | Standard Contractual Clauses |
| UK | US | UK Addendum to SCCs |
| Global | Any | Standard Contractual Clauses |

### 7.2 Data Residency Options

| Region | Location | Compliance |
|--------|----------|------------|
| United States | Virginia, Oregon | HIPAA, SOC 2 |
| European Union | Frankfurt | GDPR |
| United Kingdom | London | UK GDPR |
| Asia Pacific | Singapore | PDPA |
| Australia | Sydney | APP |

---

## 8. Audit Rights

### 8.1 Controller Audit Rights

The Controller has the right to audit FileForge:

| Audit Type | Frequency | Scope |
|------------|-----------|-------|
| Self-assessment | Annual | Internal review |
| Third-party audit | Annual | External review |
| Spot audit | 1 per year | Specific concern |

### 8.2 Audit Process

```
1. REQUEST (30 days notice)
   ↓
2. CONFIRMATION (5 business days)
   ↓
3. SCHEDULING (mutually agreed date)
   ↓
4. AUDIT CONDUCTED (on-site or remote)
   ↓
5. FINDINGS REPORT (30 days)
   ↓
6. REMEDIATION PLAN (if needed)
```

### 8.3 Audit Costs

| Item | Cost |
|------|------|
| Self-assessment review | Included |
| Standard audit | Included |
| Extensive audit | Customer responsibility |

---

## 9. Incident Response

### 9.1 Breach Notification

| Timeline | Action |
|----------|--------|
| 24 hours | Initial notification to Controller |
| 48 hours | Preliminary assessment |
| 72 hours | Detailed report |
| 7 days | Remediation plan |

### 9.2 Breach Contents

The notification shall include:

- Nature of the breach
- Categories and approximate numbers of records affected
- Likely consequences
- Measures taken to address the breach

### 9.3 Cooperation

FileForge shall:

- Investigate the breach
- Provide evidence to authorities
- Assist with regulatory communication
- Support affected data subjects

---

## 10. Termination and Data Return

### 10.1 Termination Triggers

| Trigger | Notice Period |
|---------|---------------|
| End of subscription | 30 days |
| Material breach | Immediate (with cure period) |
| Insolvency | Immediate |
| Regulatory action | Per regulator |

### 10.2 Data Return Process

| Phase | Timeline | Action |
|-------|----------|--------|
| Request | Subscription end | Controller requests export |
| Export | 15 days | FileForge provides data |
| Verification | 7 days | Controller confirms completeness |
| Deletion | 90 days | FileForge deletes all data |

### 10.3 Data Formats

| Data Type | Format | Notes |
|-----------|--------|-------|
| Sermon Files | Original format | Audio/video files |
| Metadata | JSON, CSV | Categorization, tags |
| Transcripts | SRT, VTT, TXT | Time-stamped text |
| Database | PostgreSQL dump | Full export |

---

## 11. Liability and Indemnification

### 11.1 Limitations

| Limitation | Amount |
|------------|--------|
| Direct damages | Subscription fees (12 months) |
| Consequential | Excluded |
| Liability cap | Per terms of Service Agreement |

### 11.2 Indemnification

Each party shall indemnify the other for:

| Party | Covers |
|-------|--------|
| Processor | Third-party claims from processor breach |
| Controller | Third-party claims from controller misuse |

---

## 12. Governing Law

| Aspect | Details |
|--------|---------|
| Governing Law | Laws of the jurisdiction |
| Jurisdiction | Courts of [Customer Location] |
| Language | English |

---

## 13. Contact Information

### Data Protection Officer

| Contact | Details |
|---------|---------|
| Email | dpo@fileforge-app.com |
| Response Time | 48 hours |

### Data Subject Requests

| Method | Details |
|--------|---------|
| Email | privacy@fileforge-app.com |
| Portal | https://fileforge-app.com/privacy-portal |
| Phone | [Phone Number] |

---

## 14. Appendix A: Processing Activities

| Activity | Data Categories | Purpose | Duration |
|----------|-----------------|---------|----------|
| File Storage | Audio/video, transcripts | Archive | Subscription |
| Metadata Extraction | File metadata, EXIF | Organization | Subscription |
| AI Transcription | Audio content | Accessibility | Subscription |
| Speaker ID | Voice samples | Attribution | Subscription |
| Search Indexing | Full-text content | Retrieval | Subscription |
| Audit Logging | User actions | Compliance | 7 years |

---

## 15. Appendix B: Security Measures (Detail)

### B.1 Encryption Standards

| Data State | Algorithm | Key Management |
|------------|-----------|----------------|
| Files at Rest | AES-256-GCM | Per-file keys from master |
| Database | PostgreSQL TDE | Database-managed |
| Backups | AES-256 | Separate backup key |
| Network | TLS 1.3 | Certificate-based |
| API Keys | Argon2 | Memory-hard hashing |

### B.2 Access Controls

| Control | Implementation |
|---------|----------------|
| Authentication | JWT tokens + optional MFA |
| Authorization | Role-based (User, Manager, Admin) |
| Sessions | 30-minute timeout, max 3 concurrent |
| Audit | All actions logged |

---

**This Data Processing Addendum is effective upon signature or acceptance.**

For questions, contact: dpo@fileforge-app.com
