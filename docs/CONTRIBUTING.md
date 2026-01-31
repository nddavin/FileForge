# Contributing to FileForge

Thank you for your interest in contributing to FileForge! This guide outlines the process for contributing to our enterprise file processing platform.

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contribution Workflow](#contribution-workflow)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)
- [Community](#community)

---

## Getting Started

### Prerequisites

Before contributing, ensure you have:

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11+ | Core language |
| Docker | 20.x+ | Container development |
| Git | 2.x+ | Version control |
| PostgreSQL | 15.x | Database (or use Docker) |
| Redis | 7.x | Caching (or use Docker) |

### Quick Start

```bash
# 1. Fork the repository
# Visit: https://github.com/fileforge/fileforge/fork

# 2. Clone your fork
git clone https://github.com/YOUR-USERNAME/fileforge.git
cd fileforge

# 3. Create a feature branch
git checkout -b feature/your-feature-name

# 4. Set up development environment
make setup

# 5. Run tests to verify setup
make test
```

---

## Development Setup

### Local Development

#### Option 1: Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Run tests in container
docker-compose exec backend pytest
```

#### Option 2: Local Python Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r backend/requirements.txt

# Install pre-commit hooks
pre-commit install

# Start development server
uvicorn backend.file_processor.main:app --reload
```

### Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Configure your settings
# Required: DATABASE_URL, SECRET_KEY, JWT_SECRET_KEY
```

---

## Contribution Workflow

### 1. Choose an Issue

- Browse [open issues](https://github.com/fileforge/fileforge/issues)
- Look for labels: `good first issue`, `help wanted`, `bug`, `feature`
- Comment on the issue to claim it

### 2. Create a Branch

```bash
# Branch naming conventions
feature/new-feature          # New features
bugfix/issue-description     # Bug fixes
docs/documentation-update    # Documentation
hotfix/critical-issue        # Urgent fixes
refactor/code-improvement    # Code improvements

# Create your branch
git checkout -b feature/your-feature-name
```

### 3. Make Changes

Follow our [Code Standards](#code-standards):

```bash
# Run linting before committing
make lint

# Run type checking
make type-check

# Fix any issues before proceeding
```

### 4. Write Tests

All changes must include appropriate tests:

```bash
# Run specific test
pytest backend/tests/test_api/test_feature.py -v

# Generate coverage report
pytest --cov=backend.file_processor --cov-report=html
```

### 5. Update Documentation

- Update relevant docs in `docs/`
- Add docstrings to all new functions
- Update README if needed

### 6. Commit Changes

```bash
# Stage changes
git add .

# Commit with conventional message
git commit -m "feat: add new sermon sorting feature

- Implement smart categorization based on speaker
- Add support for custom sorting rules
- Include unit tests
- Update user documentation

Closes #123"
```

### 7. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create Pull Request
# Visit: https://github.com/fileforge/fileforge/compare
```

---

## Code Standards

### Python Style (PEP 8)

| Rule | Convention |
|------|------------|
| Line length | 100 characters max |
| Type hints | Required for all functions |
| Docstrings | Google style, all public functions |
| Imports | Sorted, grouped by stdlib/third-party/local |

```python
def process_sermon(
    file_path: str,
    options: ProcessingOptions
) -> ProcessingResult:
    """
    Process a sermon file with the specified options.
    
    Args:
        file_path: Path to the sermon file
        options: Processing configuration options
        
    Returns:
        ProcessingResult containing extracted data and metadata
        
    Raises:
        ProcessingError: If file cannot be processed
    """
    # Implementation
    pass
```

### Git Commit Messages

```
type(scope): subject

body (optional)

footer (optional)
```

#### Types

| Type | Description |
|------|-------------|
| feat | New feature |
| fix | Bug fix |
| docs | Documentation only |
| style | Formatting, no code change |
| refactor | Code restructuring |
| test | Adding tests |
| chore | Maintenance tasks |

### JavaScript/TypeScript Style

| Rule | Convention |
|------|------------|
| Line length | 100 characters |
| Semicolons | Required |
| Quotes | Single quotes |
| ESLint | Airbnb config |

### CSS/Styling

- Use CSS modules for component styles
- Follow BEM naming convention
- Use CSS custom properties for theming

---

## Testing Requirements

### Test Coverage Requirements

| Category | Minimum Coverage |
|----------|------------------|
| Core functionality | 90% |
| API endpoints | 95% |
| Security features | 100% |
| Data processing | 85% |

### Test Types

#### Unit Tests

```python
# backend/tests/test_services/test_sermon_processor.py
import pytest
from backend.file_processor.services.sermon_processor import SermonProcessor

def test_extract_metadata():
    """Test metadata extraction from sermon files."""
    processor = SermonProcessor()
    result = processor.extract_metadata("tests/fixtures/sermon.mp3")
    
    assert result.duration == 1800
    assert result.speaker == "Pastor John"
    assert result.series == "Genesis"
```

#### Integration Tests

```python
# backend/tests/test_api/test_files.py
def test_file_upload_flow(client, auth_token):
    """Test complete file upload and processing flow."""
    response = client.post(
        "/api/v1/files/upload",
        files={"file": open("test.mp3", "rb")},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "processing"
```

#### E2E Tests

```typescript
// frontend/src/__tests__/fileManager.test.tsx
test("uploads sermon file successfully", async () => {
    render(<FileManager />);
    
    const file = new File(["audio"], "sermon.mp3", { type: "audio/mpeg" });
    const input = screen.getByLabelText(/upload/i);
    
    userEvent.upload(input, file);
    
    await waitFor(() => {
        expect(screen.getByText(/processing/i)).toBeInTheDocument();
    });
});
```

### Running Tests

```bash
# All tests
make test

# With coverage
make test-cov

# Specific test file
pytest backend/tests/test_api/test_files.py -v

# With verbose output
pytest -vv backend/tests/

# Run in Docker
docker-compose exec backend pytest
```

---

## Documentation

### Required Documentation

| Change Type | Documentation Required |
|-------------|------------------------|
| New feature | User guide update, API docs |
| Bug fix | Update relevant guide if needed |
| Breaking change | Migration guide, CHANGELOG |
| New API endpoint | OpenAPI spec, API docs |

### Documentation Style

- Use clear, concise language
- Include code examples
- Add screenshots for UI changes
- Update table of contents

### Updating OpenAPI Spec

When adding or modifying API endpoints:

```python
# backend/file_processor/api/v1/files.py
@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a sermon file for processing.
    
    - **file**: Audio or video file (max 100MB)
    - **Returns**: File ID and processing status
    """
    # Implementation
```

---

## Submitting Changes

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (requires major version)
- [ ] Documentation update
- [ ] Refactoring (no functional change)

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] E2E tests added/updated
- [ ] All tests pass locally

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings introduced
- [ ] Breaking changes documented

## Screenshots (if UI change)

## Related Issues
Fixes #XXX
Related to #XXX
```

### PR Review Process

1. **Automated Checks**
   - CI pipeline passes
   - Test coverage maintained
   - No linting errors
   - Type checking passes

2. **Code Review**
   - At least 1 reviewer approval
   - All comments addressed
   - Security review for sensitive changes

3. **Merge**
   - Squash and merge
   - Delete feature branch
   - PR linked in release notes

---

## Community

### Communication Channels

| Channel | Purpose |
|---------|---------|
| [GitHub Issues](https://github.com/fileforge/fileforge/issues) | Bug reports, feature requests |
| [GitHub Discussions](https://github.com/fileforge/fileforge/discussions) | Questions, ideas |
| [Discord](https://discord.gg/fileforge) | Real-time chat |
| [ mailing list](mailto:dev@fileforge-app.com) | Announcements |

### Recognition

Contributors are recognized in:
- RELEASE_NOTES.md
- CONTRIBUTORS.md
- Annual contributor awards

### Code of Conduct

All contributors must follow our [Code of Conduct](CODE_OF_CONDUCT.md). Violations should be reported to: conduct@fileforge-app.com

---

## Additional Resources

| Resource | Link |
|----------|------|
| Architecture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| API Documentation | [http://localhost:8000/docs](http://localhost:8000/docs) |
| Security | [docs/SECURITY.md](docs/SECURITY.md) |
| Contributing | This file |

---

Thank you for contributing to FileForge! Your efforts help churches worldwide manage their sermon archives effectively.
