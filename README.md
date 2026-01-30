# 🚀 **FILEFORGE - Enterprise File Processing System**

## 🎯 **Enterprise-Grade File Processing & Sorting Platform**

A production-ready, enterprise-grade file processing system with advanced security, automation, and scalability features. Built for modern organizations requiring robust file management, intelligent sorting, and comprehensive workflow automation.

---

## ✨ **Key Features**

### 🔐 **Advanced Security & Authentication**
- **JWT-based Authentication** with refresh tokens and secure session management
- **Role-Based Access Control** (Admin/Manager/User) with granular permissions
- **Multi-layered Security** with input validation, sanitization, and encryption
- **File Content Scanning** for dangerous signatures and malware detection
- **Rate Limiting & Abuse Prevention** with configurable thresholds
- **Encrypted Storage** with access controls and audit trails
- **Complete Audit Trail** for compliance and forensic analysis

### 📁 **Comprehensive File Processing**
- **Multi-format Support**: 50+ formats across Documents, Images, Videos, Audio, Archives, Business Files, CAD, Medical, Geospatial, and more
- **Intelligent Metadata Extraction** with type-specific processing
- **Advanced Sorting Engine** with customizable rules and criteria
- **Background Processing** for heavy operations and performance optimization
- **File Conversion & Transformation** capabilities
- **Content Analysis** with text extraction and indexing

### 🤖 **Workflow Automation**
- **Automated Processing Pipelines** with conditional logic
- **Scheduled Tasks** using cron expressions and event triggers
- **Rule-based Sorting** with intelligent categorization
- **Batch Processing** for thousands of files
- **Event-driven Workflows** responding to system changes
- **Approval Workflows** with multi-level validation

### 📊 **Analytics & Monitoring**
- **Real-time Performance Metrics** and system health monitoring
- **Comprehensive Logging** with structured output and search capabilities
- **Usage Analytics** with detailed reporting and insights
- **Scalability Monitoring** with load balancing and optimization
- **Error Tracking** with Sentry integration and automated alerts

---

## 🏗️ **System Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FILEFORGE PROCESSING PIPELINE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────┐    ┌──────────────┐ │
│  │  UPLOAD  │───▶│  VALIDATION  │───▶│  EXTRACTION   │───▶│   SORTING    │ │
│  └──────────┘    └──────────────┘    └───────────────┘    └──────────────┘ │
│       │               │                   │                      │          │
│       ▼               ▼                   ▼                      ▼          │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────┐    ┌──────────────┐ │
│  │   Queue  │    │  Security    │    │   Metadata    │    │    Rules     │ │
│  │  System  │    │   Checks     │    │   Extractors  │    │    Engine    │ │
│  └──────────┘    └──────────────┘    └───────────────┘    └──────────────┘ │
│                                                                              │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────┐                      │
│  │   AI/ML  │◀───│   Workflow   │◀───│  Storage      │                      │
│  │ Processor│    │   Engine     │    │  (Encrypted)  │                      │
│  └──────────┘    └──────────────┘    └───────────────┘                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 **Supported File Types**

| Category | Formats | Processing Capabilities |
|----------|---------|------------------------|
| **Documents** | PDF, DOCX, XLSX, PPTX, TXT, CSV | OCR, metadata, text extraction |
| **Images** | JPG, PNG, GIF, TIFF, WebP, RAW | EXIF, dimensions, OCR |
| **Videos** | MP4, AVI, MOV, MKV, WebM | Duration, codec, thumbnails |
| **Audio** | MP3, WAV, FLAC, AAC, OGG | ID3 tags, duration, waveform |
| **Archives** | ZIP, RAR, 7Z, TAR, GZ | Contents listing, extraction |
| **Business** | XLSX, PDF, CSV, XML | Invoice processing, data extraction |
| **CAD** | DWG, DXF, STEP, IGES | Entity count, BOM extraction |
| **Medical** | DICOM, HL7, PDF/A | Patient info, PHI detection |
| **Geospatial** | Shapefile, GeoJSON, KML | Features, projection, bounds |
| **Code** | 35+ languages | Syntax analysis, complexity |

**Full format support matrix**: See [File Format Support](docs/file-format-support.md)

---

## 🚀 **Quick Start**

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- PostgreSQL (optional, SQLite for dev)
- Redis (optional)

### Installation

1. **Clone the repository**
    ```bash
    git clone <repository-url>
    cd fileforge
    ```

2. **Environment Setup**
    ```bash
    cp .env.example .env
    # Edit .env with your configuration
    ```

3. **Docker Deployment**
    ```bash
    docker-compose up -d
    ```

4. **Access the Application**
    - Frontend: http://localhost:3000
    - Backend API: http://localhost:8000

### How to run tests

See the canonical testing instructions in `docs/TESTING.md` for backend and frontend test commands and CI notes.
    - API Documentation: http://localhost:8000/docs

### Manual Installation

1. **Backend Setup**
    ```bash
    cd backend
    pip install -r requirements.txt
    # Database setup (auto-creates tables on startup)
    ```

2. **Frontend Setup**
    ```bash
    cd frontend
    npm install
    ```

3. **Run the Application**
    ```bash
    # Backend (from backend/ directory)
    uvicorn file_processor.main:app --host 0.0.0.0 --port 8000 --reload

    # Frontend (from frontend/ directory)
    npm run dev
    ```

---

## 📚 **Documentation**

| Guide | Description | Link |
|-------|-------------|------|
| **User Guide** | End-user documentation, file upload, sorting rules | [docs/user-guide.md](docs/user-guide.md) |
| **Developer Guide** | Development setup, API development, deployment | [docs/developer-guide.md](docs/developer-guide.md) |
| **Security Guide** | Security features, RBAC, compliance, audit trails | [docs/security-guide.md](docs/security-guide.md) |
| **File Format Support** | Comprehensive format matrix, processing capabilities | [docs/file-format-support.md](docs/file-format-support.md) |
| **Processing Pipeline** | Pipeline architecture, workflows, error handling | [docs/processing-pipeline.md](docs/processing-pipeline.md) |
| **API Documentation** | OpenAPI/Swagger docs (available at /docs when running) | [docs/README.md](docs/README.md) |
| **Deployment Guide** | Production deployment for Docker, K8s, cloud providers | [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) |
| **Operations Runbook** | Incident response, monitoring, disaster recovery | [docs/RUNBOOK.md](docs/RUNBOOK.md) |
| **Privacy Policy** | GDPR-compliant data collection and usage | [docs/PRIVACY_POLICY.md](docs/PRIVACY_POLICY.md) |
| **Data Processing Addendum** | DPA template for church data protection | [docs/DATA_PROCESSING_ADDENDUM.md](docs/DATA_PROCESSING_ADDENDUM.md) |
| **Contributing Guide** | PR guidelines, code standards, development workflow | [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) |
| **Code of Conduct** | Community standards and enforcement | [docs/CODE_OF_CONDUCT.md](docs/CODE_OF_CONDUCT.md) |
| **Architecture Decision Records** | Technical design decisions and rationale | [docs/adrs/](docs/adrs/) |

---

## 🔒 **Security & Compliance**

### Enterprise Security Features
- ✅ **RBAC**: Admin, Manager, User roles with granular permissions
- ✅ **Encryption**: Fernet (AES-128) for files, AES-256 for sensitive data
- ✅ **Audit Logging**: 7+ year retention for compliance
- ✅ **Rate Limiting**: Configurable request throttling
- ✅ **Input Validation**: File type, size, content validation

### Compliance Certifications
| Standard | Status | Coverage |
|----------|--------|----------|
| **GDPR** | ✅ Compliant | Data protection, DPA, consent |
| **HIPAA** | ✅ Ready | PHI detection, redaction, audit |
| **GoBD** | ✅ Ready | German accounting standards |
| **SOC 2** | ✅ Ready | Security, availability, confidentiality |

**Security documentation**: [docs/SECURITY.md](docs/SECURITY.md) (overview) | [docs/security-guide.md](docs/security-guide.md) (detailed)

---

## 🔧 **Configuration**

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/dbname

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key
ENCRYPTION_KEY=your-encryption-key

# File Storage
UPLOAD_DIR=/path/to/uploads
MAX_FILE_SIZE=52428800  # 50MB

# AI/ML Features
OCR_ENABLED=true
CLASSIFICATION_ENABLED=true
AUTO_TAGGING_ENABLED=true

# Email (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

**Full configuration guide**: [docs/developer-guide.md](docs/developer-guide.md#configuration)

---

## 📊 **API Documentation**

### Core Endpoints

#### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | User login |
| POST | `/api/v1/auth/register` | User registration |
| POST | `/api/auth/refresh` | Token refresh |
| GET | `/api/auth/me` | Current user info |

#### File Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/files/upload` | Upload files |
| GET | `/api/v1/files` | List files |
| GET | `/api/v1/files/{id}` | Get file details |
| GET | `/api/v1/files/download/{id}` | Download files |
| DELETE | `/api/v1/files/{id}` | Delete files |

#### Sorting & Rules
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/sorting-rules` | Create sorting rules |
| GET | `/api/v1/sorting-rules` | List sorting rules |
| POST | `/api/v1/sort` | Apply sorting |

#### AI Features
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/ai/classify` | AI document classification |
| POST | `/api/v1/ai/ocr` | OCR text extraction |
| POST | `/api/v1/ai/auto-tag` | Auto-tagging |

#### Workflows
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/workflows` | Create workflow |
| GET | `/api/v1/workflows` | List workflows |
| POST | `/api/v1/workflows/{id}/execute` | Execute workflow |

### API Examples

```python
import requests

# Login first
login_response = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'username': 'your_username',
    'password': 'your_password'
})
token = login_response.json()['access_token']

# Upload a file
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/files/upload',
        files={'file': f},
        headers={'Authorization': f'Bearer {token}'}
    )
    print(response.json())

# AI Classification
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/ai/classify',
        files={'file': f},
        headers={'Authorization': f'Bearer {token}'}
    )
    print(response.json())
```

---

## 🚀 **Deployment Options**

### Docker (Recommended)

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose up -d --scale worker=4
```

### Kubernetes

```bash
# Deploy to Kubernetes
kubectl apply -f k8s/

# Scale backend
kubectl scale deployment fileforge-api --replicas=5

# View HPA status
kubectl get hpa
```

### Cloud Deployment
- **AWS**: ECS, EKS, Lambda
- **Google Cloud**: Cloud Run, GKE
- **Azure**: Container Instances, AKS

**Full deployment guide**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

## 📈 **Scaling & Performance**

| Component | Min | Max | Scaling Trigger |
|-----------|-----|-----|-----------------|
| API Service | 2 | 10 | CPU > 70% or RPS > 500 |
| Worker Service | 2 | 5 | Queue length > 100 |
| Frontend | 1 | 3 | CPU > 80% |
| Redis | 1 | Cluster | Memory > 80% |
| PostgreSQL | 1 | Read replicas | CPU > 80% |

---

## 🛠️ **Development**

### Setup
```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# Run development servers
# Backend (from backend/ directory)
uvicorn file_processor.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (from frontend/ directory)
npm run dev
```

### Testing
```bash
# Run all tests (from root directory)
pytest backend/tests/

# Run with coverage
pytest backend/tests/ --cov=backend/file_processor --cov-report=html

# Run specific test categories
pytest backend/tests/test_security/ -v
pytest backend/tests/test_api/ --disable-warnings
```

### Contributing
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 **Support**

### Documentation
- 📖 [User Guide](docs/user-guide.md)
- 🛠️ [Developer Guide](docs/developer-guide.md)
- 🔒 [Security Overview](docs/SECURITY.md) | [Security Guide](docs/security-guide.md)
- 📋 [File Format Support](docs/file-format-support.md)
- 🔄 [Processing Pipeline](docs/processing-pipeline.md)
- 🚀 [Deployment Guide](docs/DEPLOYMENT.md)
- 📊 [Operations Runbook](docs/RUNBOOK.md)
- 📜 [Privacy Policy](docs/PRIVACY_POLICY.md)
- 📑 [Data Processing Addendum](docs/DATA_PROCESSING_ADDENDUM.md)
- 🤝 [Contributing Guide](docs/CONTRIBUTING.md)
- 👥 [Code of Conduct](docs/CODE_OF_CONDUCT.md)
- 🏛️ [Architecture Decision Records](docs/adrs/)

### Support Channels
- 📧 Email: support@fileforge-app.com
- 📖 Docs: https://docs.fileforge-app.com
- 🐛 Issues: https://github.com/your-org/fileforge/issues
- 💬 Discussions: https://github.com/your-org/fileforge/discussions

---

**FileForge** - Enterprise-grade file processing with intelligent automation and comprehensive security. Built for modern organizations requiring robust, scalable file management solutions.
