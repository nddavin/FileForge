# Operations Runbook

This runbook provides procedures for day-to-day operations, incident response, and maintenance tasks for the FileForge platform.

## 📋 Table of Contents

- [Quick Reference](#quick-reference)
- [Daily Operations](#daily-operations)
- [Incident Response](#incident-response)
- [Maintenance Tasks](#maintenance-tasks)
- [Disaster Recovery](#disaster-recovery)
- [Escalation Procedures](#escalation-procedures)
- [Post-Incident Review](#post-incident-review)

---

## Quick Reference

### Service Endpoints

| Service | URL | Health Check |
|---------|-----|--------------|
| API | https://api.fileforge.io/health | `/health` |
| Frontend | https://app.fileforge.io | - |
| Prometheus | https://metrics.fileforge.io | /metrics |
| Grafana | https://grafana.fileforge.io | - |

### Key Metrics

| Metric | Warning | Critical |
|--------|---------|----------|
| API Response Time | >500ms | >1s |
| Error Rate | >1% | >5% |
| Queue Length | >100 | >1000 |
| CPU Usage | >70% | >90% |
| Memory Usage | >80% | >95% |
| Disk Usage | >80% | >90% |

### Emergency Contacts

| Role | Contact | Response Time |
|------|---------|---------------|
| On-Call Engineer | [PagerDuty](https://fileforge.pagerduty.com) | 15 min |
| Platform Lead | platform@fileforge-app.com | 1 hour |
| Security Team | security@fileforge-app.com | 1 hour |
| CTO | cto@fileforge-app.com | 4 hours |

---

## Daily Operations

### Morning Checklist

```bash
#!/bin/bash
# daily-check.sh

echo "=== FileForge Daily Health Check ==="
echo "Date: $(date)"

# 1. Check all services
echo -e "\n1. Service Status:"
kubectl get pods -n fileforge

# 2. Check recent errors
echo -e "\n2. Recent Errors (last 24h):"
kubectl logs -n fileforge -l app=fileforge-backend \
  --since=24h | grep -i error | tail -100

# 3. Check queue status
echo -e "\n3. Celery Queue Status:"
redis-cli -h redis.fileforge.io LLEN fileforge-tasks

# 4. Check database health
echo -e "\n4. Database Status:"
psql -c "SELECT pg_current_wal_lsn();" 2>/dev/null || echo "DB check failed"

# 5. Check backup status
echo -e "\n5. Last Backup:"
aws s3 ls s3://fileforge-backups/database/ | tail -1

# 6. Check disk usage
echo -e "\n6. Disk Usage:"
df -h /app/uploads

# 7. Check SSL certificate expiry
echo -e "\n7. SSL Certificate:"
echo | openssl s_client -servername fileforge.io -connect fileforge.io:443 2>/dev/null | openssl x509 -noout -dates
```

### Monitoring Dashboard

Access Grafana dashboards at https://grafana.fileforge.io:

| Dashboard | Description |
|-----------|-------------|
| [Overview](https://grafana.fileforge.io/d/overview) | System-wide metrics |
| [API](https://grafana.fileforge.io/d/api) | API performance |
| [Workers](https://grafana.fileforge.io/d/workers) | Celery worker status |
| [Database](https://grafana.fileforge.io/d/database) | PostgreSQL metrics |
| [Storage](https://grafana.fileforge.io/d/storage) | Storage usage |

### Routine Tasks

| Task | Frequency | Owner |
|------|-----------|-------|
| Log review | Daily | On-call |
| SSL certificate check | Weekly | Platform |
| Security patch review | Weekly | Security |
| Performance review | Weekly | Platform |
| Capacity planning | Monthly | Platform |
| Penetration test | Quarterly | Security |

---

## Incident Response

### Incident Severity Levels

| Level | Definition | Response Time | Examples |
|-------|------------|---------------|----------|
| **SEV-1** | Critical - Service down | 15 min | Complete outage |
| **SEV-2** | Major - Significant degradation | 1 hour | API slow/unavailable |
| **SEV-3** | Minor - Limited impact | 4 hours | Feature not working |
| **SEV-4** | Low - Minimal impact | 24 hours | Cosmetic issues |

### SEV-1 Response Procedure

```
⏱️ T+0 min - DETECTION
├── Alert received (PagerDuty/Sentry)
├── Acknowledge alert
└── Initial assessment (is it real?)

⏱️ T+15 min - ESCALATION
├── If not resolved, escalate to on-call
├── Notify #incidents Slack channel
└── Begin incident bridge call

⏱️ T+30 min - TRIAGE
├── Identify affected components
├── Determine root cause
└── Implement workaround if available

⏱️ T+1 hour - RESOLUTION
├── Apply fix
├── Verify fix works
└── Monitor for stability

⏱️ T+2 hours - COMMUNICATION
├── Update status page
├── Notify affected customers
└── Document timeline
```

### Common Incidents

#### Incident: API Unavailable

**Symptoms:**
- 502/503 errors
- Health check failing
- Increased error rate

**Diagnosis:**
```bash
# Check pod status
kubectl get pods -n fileforge -l app=fileforge-backend

# Check resource usage
kubectl top pods -n fileforge -l app=fileforge-backend

# Check events
kubectl describe pod <pod-name> -n fileforge

# Check logs
kubectl logs -n fileforge -l app=fileforge-backend --tail=100
```

**Resolution Steps:**
1. If pods are crashing: Check OOMKilled, restart pods
2. If resources exhausted: Scale up or add nodes
3. If database: Check connection pool, restart if needed
4. If network: Check DNS, load balancer, firewall

#### Incident: Database Issues

**Symptoms:**
- Slow queries
- Connection errors
- Replication lag

**Diagnosis:**
```bash
# Check database connections
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Check locks
psql -c "SELECT * FROM pg_locks WHERE NOT granted;"

# Check replication
psql -c "SELECT * FROM pg_stat_replication;"

# Check slow queries
psql -c "SELECT query, state_change FROM pg_stat_activity WHERE state = 'active' LIMIT 10;"
```

**Resolution Steps:**
1. Kill long-running queries if needed
2. Restart database if unresponsive
3. Failover to replica if primary down
4. Restore from backup if corrupted

#### Incident: High Queue Backlog

**Symptoms:**
- Delayed processing
- Increasing queue length
- User complaints about delays

**Diagnosis:**
```bash
# Check queue length
redis-cli LLEN fileforge-tasks

# Check worker status
kubectl get pods -n fileforge -l app=fileforge-worker

# Check worker logs
kubectl logs -n fileforge -l app=fileforge-worker --tail=50
```

**Resolution Steps:**
1. Scale up workers: `kubectl scale deployment fileforge-worker --replicas=10`
2. Check for stuck workers and restart
3. Investigate cause of slowdown
4. Consider clearing queue if backed up >24h

---

## Maintenance Tasks

### Database Maintenance

#### Routine Maintenance (Weekly)

```bash
#!/bin/bash
# db-maintenance.sh

# 1. VACUUM ANALYZE (non-blocking)
psql -c "VACUUM ANALYZE;"

# 2. Reindex if needed
psql -c "SELECT indexname FROM pg_indexes WHERE tablename = 'files';"

# 3. Check for bloat
psql -c "SELECT schemaname, tablename, 
  pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as size,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total
FROM pg_tables WHERE schemaname = 'public';"
```

#### Index Rebuild (Monthly)

```bash
# Create new index without locking
CREATE INDEX CONCURRENTLY idx_new ON files (updated_at);

# Drop old index
DROP INDEX CONCURRENTLY idx_old;

# Rename new index
ALTER INDEX idx_new RENAME TO idx_files_updated_at;
```

### Log Rotation

```bash
# /etc/logrotate.d/fileforge
/var/log/fileforge/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 root root
    postrotate
        systemctl reload fileforge > /dev/null 2>&1 || true
    endscript
}
```

### Certificate Renewal

```bash
#!/bin/bash
# cert-renewal.sh

# Check certificate expiry
days_until_expiry=$(echo | openssl s_client -servername fileforge.io -connect fileforge.io:443 2>/dev/null | openssl x509 -noout -dates | grep "Not After" | awk '{print $4}')

if [ $days_until_expiring -lt 30 ]; then
    # Request renewal
    certbot renew --quiet
    
    # Reload nginx
    nginx -s reload
    
    # Notify
    curl -X POST -d "Certificate renewed for fileforge.io" $SLACK_WEBHOOK_URL
fi
```

### Backup Verification

```bash
#!/bin/bash
# verify-backup.sh

# Download latest backup
aws s3 cp s3://fileforge-backups/database/latest.sql.gz /tmp/latest.sql.gz

# Extract
gunzip /tmp/latest.sql.gz

# Verify checksum
sha256sum /tmp/latest.sql > /tmp/latest.sql.sha256

# Test restore (on isolated database)
psql -c "DROP DATABASE IF EXISTS test_restore;"
psql -c "CREATE DATABASE test_restore;"
psql test_restore < /tmp/latest.sql

# Check row counts
psql test_restore -c "SELECT COUNT(*) FROM files;"
psql test_restore -c "SELECT COUNT(*) FROM users;"

# Cleanup
psql -c "DROP DATABASE test_restore;"
rm /tmp/latest.sql /tmp/latest.sql.sha256

echo "Backup verification complete"
```

---

## Disaster Recovery

### Recovery Objectives

| Metric | Target | Description |
|--------|--------|-------------|
| **RTO** | 4 hours | Maximum acceptable downtime |
| **RPO** | 1 hour | Maximum acceptable data loss |
| **Backup Frequency** | Hourly | Database transaction logs |
| **Off-site Backup** | Real-time | Cross-region replication |

### Recovery Procedures

#### Database Restore (Point-in-Time)

```bash
#!/bin/bash
# restore-database.sh

# Variables
BACKUP_DATE="$1"  # Format: YYYY-MM-DD-HHMM
S3_BUCKET="s3://fileforge-backups"

# Download base backup
aws s3 cp ${S3_BUCKET}/base/${BACKUP_DATE}_base.tar.gz /tmp/base.tar.gz
tar -xzf /tmp/base.tar.gz -C /var/lib/postgresql/

# Download WAL archives
aws s3 cp ${S3_BUCKET}/wal/ ${S3_BUCKET}/base/${BACKUP_DATE}/ /tmp/wal/

# Configure recovery
cat > /var/lib/postgresql/data/recovery.conf
restore_command = 'cp /tmp/wal/%f %p'
recovery_target_time = '${BACKUP_DATE}T${TIME}:00Z'
recovery_target_action = 'promote'

# Restart PostgreSQL
systemctl restart postgresql

# Verify
psql -c "SELECT COUNT(*) FROM files;"
```

#### Full System Restore

```bash
#!/bin/bash
# full-restore.sh

# 1. Restore database
echo "Restoring database..."
./restore-database.sh $1

# 2. Restore uploaded files
echo "Restoring files..."
aws s3 sync s3://fileforge-backups/files/ /app/uploads/ --delete

# 3. Restore configuration
echo "Restoring configuration..."
git checkout production-config/

# 4. Restart services
echo "Restarting services..."
kubectl rollout restart deployment/fileforge-backend -n fileforge
kubectl rollout restart deployment/fileforge-worker -n fileforge

# 5. Verify
echo "Verifying..."
curl -f https://api.fileforge.io/health
```

### Backup Schedule

| Backup Type | Frequency | Retention | Location |
|-------------|-----------|-----------|----------|
| Full Database | Daily | 30 days | S3 + Glacier |
| WAL Logs | Hourly | 7 days | S3 |
| File Uploads | Daily incremental | 90 days | S3 |
| Configuration | On change | Forever | Git |

---

## Escalation Procedures

### Escalation Matrix

```
SEV-1 (Critical)
├── On-call (immediate)
├── Platform Lead (15 min)
├── CTO (1 hour)
└── CEO (if >4 hours)

SEV-2 (Major)
├── On-call (15 min)
├── Platform Lead (1 hour)
└── CTO (4 hours)

SEV-3 (Minor)
├── On-call (4 hours)
└── Platform Lead (next business day)

SEV-4 (Low)
├── Process for next sprint
└── Platform Lead review
```

### Communication Templates

#### Incident Declaration

```
🚨 INCIDENT DECLARED

Severity: SEV-[1/2/3/4]
Status: [Investigating/Monitoring/Resolved]
Title: [Brief description]

Impact:
- [Who/what is affected]
- [Current user impact]

Timeline:
- [T+time] [Event]

Contact: [On-call name] | [Phone]
Slack: #incidents
Bridge: https://meet.fileforge.io/incident-[id]
```

#### Customer Notification

```
Subject: Service Issue - [Service Name]

Dear [Customer],

We are currently experiencing issues with [service]. 
This affects [impact description].

Our team is investigating and we will provide updates every 30 minutes.

Status Page: https://status.fileforge.io/incidents/[id]

We apologize for the inconvenience.

- FileForge Team
```

---

## Post-Incident Review

### Incident Report Template

```markdown
# Incident Report: [INC-1234]

## Summary
| Field | Value |
|-------|-------|
| Date | YYYY-MM-DD |
| Duration | X hours Y minutes |
| Severity | SEV-X |
| Affected | X% of users |

## Impact
- Users affected: [Number]
- API requests failed: [Number]
- Data lost: [Yes/No/Amount]

## Root Cause
[Detailed explanation]

## Timeline
| Time | Event |
|------|-------|
| T+0 | Alert triggered |
| T+15 | Incident declared |
| T+30 | Root cause identified |
| T+60 | Fix implemented |
| T+90 | Service restored |

## Detection
- Alert source: [PagerDuty/Sentry/Manual]
- Detection method: [Automated/Manual]

## Response
- First responder: [Name]
- Escalations: [List]

## Lessons Learned
### What went well
- [Points]

### What went poorly
- [Points]

### Action Items
| Action | Owner | Due Date |
|--------|-------|----------|
| [Action] | [Owner] | [Date] |

## Attachments
- [Links to logs, charts, etc.]
```

### Improvement Tracking

| Issue | Action | Owner | Status |
|-------|--------|-------|--------|
| Alert threshold too high | Lower threshold | @platform | In Progress |
| Runbook outdated | Update procedures | @oncall | Pending |
| Insufficient capacity | Add nodes | @platform | Done |

---

## Appendix: Useful Commands

### Kubernetes

```bash
# View all resources
kubectl get all -n fileforge

# View resource usage
kubectl top pods -n fileforge

# View events
kubectl get events -n fileforge --sort-by='.lastTimestamp'

# Port forward for testing
kubectl port-forward svc/fileforge-backend 8000:8000 -n fileforge

# Execute in pod
kubectl exec -it <pod-name> -n fileforge -- /bin/bash
```

### Database

```bash
# Connect to database
psql $DATABASE_URL

# Check active connections
SELECT count(*) FROM pg_stat_activity;

# Kill idle connections
SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
  WHERE state = 'idle' AND query_start < NOW() - INTERVAL '1 hour';

# Check table sizes
SELECT schemaname, tablename, 
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables WHERE schemaname = 'public';
```

### Redis

```bash
# Check queue length
redis-cli LLEN fileforge-tasks

# Check worker status
redis-cli INFO workers

# Clear stuck jobs
redis-cli DEL fileforge-tasks

# Check memory usage
redis-cli INFO memory
```

---

## Support Resources

| Resource | URL |
|----------|-----|
| Status Page | https://status.fileforge.io |
| PagerDuty | https://fileforge.pagerduty.com |
| Grafana | https://grafana.fileforge.io |
| Sentry | https://fileforge.sentry.io |
| Documentation | https://docs.fileforge.io |

**Document Version:** 1.0  
**Last Updated:** January 2024  
**Next Review:** April 2024
