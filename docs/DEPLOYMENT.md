# Deployment Guide

This guide covers deploying FileForge to production environments across various cloud providers and configurations.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Cloud Providers](#cloud-providers)
- [Configuration](#configuration)
- [Security](#security)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## Overview

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Load Balancer                         │
│                    (ALB / Cloud Load Balancer)               │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   Frontend  │ │   Backend   │ │   Backend   │
│(Vite+React) │ │  (FastAPI)  │ │  (FastAPI)  │
└─────────────┘ └─────────────┘ └─────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│    Redis    │ │  PostgreSQL │ │  Celery     │
│   (Queue)   │ │  (Database) │ │  Workers    │
└─────────────┘ └─────────────┘ └─────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                      Object Storage                          │
│                   (S3 / GCS / Azure Blob)                    │
└─────────────────────────────────────────────────────────────┘
```

### Components

| Component | Image | Description |
|-----------|-------|-------------|
| Frontend | `fileforge/frontend` | Vite + React web application |
| Backend | `fileforge/backend` | FastAPI REST API |
| Worker | `fileforge/worker` | Celery task workers |
| Redis | `redis:7-alpine` | Message queue |
| PostgreSQL | `postgres:15` | Primary database |

---

## Prerequisites

### Required Accounts

| Service | Purpose | Required For |
|---------|---------|--------------|
| Docker Hub / ECR / GCR | Container registry | All deployments |
| Cloud Provider | Infrastructure | Cloud deployment |
| Domain Registrar | DNS management | Production |

### CLI Tools

| Tool | Version | Purpose |
|------|---------|---------|
| Docker | 20.x+ | Containerization |
| kubectl | 1.27+ | Kubernetes management |
| helm | 3.x+ | Kubernetes package management |
| Terraform | 1.5+ | Infrastructure as Code |
| AWS CLI | 2.x | AWS management (if applicable) |

### Local Testing Prerequisites

```bash
# Check Docker version
docker --version  # Must be 20.x+

# Check kubectl
kubectl version --client

# Check Helm
helm version
```

---

## Docker Deployment

### 1. Build Images

```bash
# Build all images
docker-compose -f docker-compose.prod.yml build

# Build specific service
docker build -t fileforge/backend ./backend
docker build -t fileforge/frontend ./frontend
docker build -t fileforge/worker ./backend
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env.production

# Edit configuration
nano .env.production
```

#### Required Environment Variables

```bash
# ===========================================
# PRODUCTION CONFIGURATION
# ===========================================

# Database
DATABASE_URL=postgresql://user:password@hostname:5432/fileforge

# Redis
REDIS_URL=redis://:password@hostname:6379/0

# Security
SECRET_KEY=change-this-in-production-256-bit-secret
JWT_SECRET_KEY=change-this-in-production-jwt-secret
ENCRYPTION_KEY=change-this-in-production-fernet-key

# Application
DEBUG=false
ALLOWED_ORIGINS=https://yourdomain.com

# Storage (S3 compatible)
S3_BUCKET_NAME=fileforge-uploads
S3_ACCESS_KEY=$AWS_ACCESS_KEY_ID
S3_SECRET_KEY=$AWS_SECRET_ACCESS_KEY
S3_REGION=us-east-1
S3_ENDPOINT=https://s3.amazonaws.com

# Monitoring
SENTRY_DSN=$SENTRY_DSN
LOG_LEVEL=INFO
```

### 3. Run with Docker Compose

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale worker=4
```

### 4. Health Checks

```bash
# Check service health
curl http://localhost/health

# Check all containers
docker-compose ps

# View container resources
docker stats
```

---

## Kubernetes Deployment

### 1. Prerequisites

```bash
# Create namespace
kubectl create namespace fileforge

# Create secrets
kubectl apply -f k8s/secrets/
```

### 2. Install with Helm

```bash
# Add Helm repository (if available)
helm repo add fileforge https://charts.fileforge.io
helm repo update

# Install chart
helm install fileforge fileforge/fileforge \
  --namespace fileforge \
  --values values.yaml
```

### 3. Manual Deployment

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get deployments -n fileforge

# View pods
kubectl get pods -n fileforge
```

### 4. Scaling

```bash
# Scale backend
kubectl scale deployment fileforge-backend --replicas=5 -n fileforge

# Scale workers
kubectl scale deployment fileforge-worker --replicas=4 -n fileforge

# View HPA
kubectl get hpa -n fileforge
```

### 5. Rolling Updates

```bash
# Update image
kubectl set image deployment/fileforge-backend backend=fileforge/backend:v2.0.0 -n fileforge

# View rollout status
kubectl rollout status deployment/fileforge-backend -n fileforge

# Rollback if needed
kubectl rollout undo deployment/fileforge-backend -n fileforge
```

---

## Cloud Providers

### AWS (ECS + EKS)

#### ECS with Fargate

```bash
# Configure ECS
aws ecs create-cluster --cluster-name fileforge-prod

# Register task definition
aws ecs register-task-definition --cli-input-json file://ecs/task-definition.json

# Create service
aws ecs create-service \
  --cluster fileforge-prod \
  --service-name fileforge-backend \
  --task-definition fileforge \
  --desired-count 2
```

#### EKS (Recommended)

```bash
# Create EKS cluster
eksctl create cluster \
  --name fileforge-prod \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type m5.xlarge \
  --nodes 3

# Deploy FileForge
kubectl apply -f k8s/eks/
```

#### AWS Resources Required

| Resource | Purpose |
|----------|---------|
| VPC | Network isolation |
| ALB | Load balancing |
| RDS PostgreSQL | Database |
| ElastiCache Redis | Queue/cache |
| S3 Bucket | File storage |
| Secrets Manager | Secret storage |
| CloudWatch | Logging |

### Google Cloud Platform (GCP)

#### Cloud Run (Recommended for small deployments)

```bash
# Deploy backend
gcloud run deploy fileforge-backend \
  --image gcr.io/project/fileforge/backend \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --min-instances 2

# Deploy frontend
gcloud run deploy fileforge-frontend \
  --image gcr.io/project/fileforge/frontend \
  --platform managed \
  --region us-central1 \
  --memory 1Gi
```

#### GKE (Recommended for large deployments)

```bash
# Create cluster
gcloud container clusters create fileforge \
  --region us-central1 \
  --node-pool=default \
  --num-nodes=3

# Deploy
kubectl apply -f k8s/gke/
```

#### GCP Resources Required

| Resource | Purpose |
|----------|---------|
| Cloud SQL PostgreSQL | Database |
| Cloud Memorystore | Redis |
| Cloud Storage | File storage |
| Cloud Load Balancing | Load balancer |
| Secret Manager | Secrets |

### Azure (AKS)

```bash
# Create AKS cluster
az aks create \
  --resource-group fileforge-rg \
  --name fileforge-prod \
  --node-count 3 \
  --enable-managed-identity

# Get credentials
az aks get-credentials -g fileforge-rg -n fileforge-prod

# Deploy
kubectl apply -f k8s/azure/
```

#### Azure Resources Required

| Resource | Purpose |
|----------|---------|
| Azure Database for PostgreSQL | Database |
| Azure Cache for Redis | Queue/cache |
| Azure Blob Storage | File storage |
| Azure Load Balancer | Load balancer |
| Azure Key Vault | Secrets |

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `REDIS_URL` | Yes | - | Redis connection string |
| `SECRET_KEY` | Yes | - | Application secret key |
| `JWT_SECRET_KEY` | Yes | - | JWT signing key |
| `ENCRYPTION_KEY` | Yes | - | File encryption key |
| `DEBUG` | No | `false` | Debug mode |
| `ALLOWED_ORIGINS` | Yes | - | CORS origins |
| `SENTRY_DSN` | No | - | Sentry monitoring |
| `LOG_LEVEL` | No | `INFO` | Logging level |

### Resource Limits

| Component | CPU | Memory |
|-----------|-----|--------|
| Frontend | 500m | 512Mi |
| Backend | 1000m | 1Gi |
| Worker | 2000m | 2Gi |
| Redis | 500m | 1Gi |
| PostgreSQL | 1000m | 2Gi |

### Scaling Configuration

#### Horizontal Pod Autoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fileforge-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fileforge-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## Security

### TLS Configuration

```nginx
# nginx.conf snippet
server {
    listen 443 ssl http2;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Secret Management

#### AWS Secrets Manager

```bash
# Store secrets
aws secretsmanager create-secret \
  --name fileforge/production \
  --secret-string file://secrets.json
```

#### HashiCorp Vault

```bash
# Enable secrets
vault kv put secret/fileforge/production \
  DATABASE_URL="postgresql://..." \
  REDIS_URL="redis://..."
```

### Network Security

| Layer | Configuration |
|-------|---------------|
| VPC | Private subnets for DB, public for LB |
| Security Groups | Restrictive ingress/egress |
| WAF | SQL injection, XSS protection |
| DDoS | Cloud provider protection |

---

## Monitoring

### Metrics Endpoints

| Endpoint | Description |
|----------|-------------|
| `/metrics` | Prometheus metrics |
| `/health` | Basic health check |
| `/ready` | Readiness probe |

### Health Check Configuration

```yaml
# k8s/deployment.yaml (health check section)
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Logging

| Log Type | Destination | Retention |
|----------|-------------|-----------|
| Application | CloudWatch/Stackdriver | 30 days |
| Audit | S3/GCS | 7 years |
| Access | ELK/Splunk | 90 days |

### Alerting

| Alert | Threshold | Action |
|-------|-----------|--------|
| High CPU | >80% for 5min | Scale up |
| High Memory | >85% for 5min | Scale up |
| High Error Rate | >5% | Page on-call |
| Database Connection | >80% | Alert |
| Queue Length | >1000 | Scale workers |

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Pods not starting | Image pull error | Check credentials, image name |
| Database connection | Wrong URL | Verify DATABASE_URL |
| High latency | Resource limits | Increase CPU/memory |
| 502 errors | Backend down | Check backend logs |
| Queue buildup | Worker shortage | Scale workers |

### Debug Commands

```bash
# View pod logs
kubectl logs -f deployment/fileforge-backend -n fileforge

# Describe pod
kubectl describe pod <pod-name> -n fileforge

# Port forward for testing
kubectl port-forward svc/fileforge-backend 8000:8000 -n fileforge

# Check events
kubectl get events -n fileforge --sort-by='.lastTimestamp'

# Debug container
kubectl exec -it <pod-name> -n fileforge -- /bin/bash
```

### Rollback Procedure

```bash
# List releases
helm list -n fileforge

# Rollback
helm rollback fileforge 1 -n fileforge

# Or with kubectl
kubectl rollout undo deployment/fileforge-backend -n fileforge
```

---

## Post-Deployment Checklist

- [ ] Health checks passing
- [ ] TLS certificate installed and valid
- [ ] DNS records pointing to load balancer
- [ ] Monitoring dashboards configured
- [ ] Alerts set up and tested
- [ ] Backup jobs running
- [ ] SSL/TLS scan passing
- [ ] Penetration test complete
- [ ] Documentation updated
- [ ] Team trained on new deployment

---

## Support

| Resource | Link |
|----------|------|
| Documentation | https://docs.fileforge.io |
| GitHub Issues | https://github.com/fileforge/fileforge/issues |
| Support Email | support@fileforge-app.com |
| Status Page | https://status.fileforge.io |
