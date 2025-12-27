# Technology Stack: Task Manager MCP Server

**Version**: 1.1.0
**Created**: 2025-12-25
**Auto-Generated**: No (specification-based)
**Status**: Active

## Overview

This document defines the approved technology stack for the Task Manager MCP Server project. All implementation work must use these technologies unless explicitly approved as an addition.

**Project Type**: Model Context Protocol (MCP) Server
**Deployment Target**: Google Cloud Run (serverless containers)
**Project Phase**: Specification → Implementation

## Core Technologies

### Language & Runtime

#### Python 3.11+
- **Purpose**: Primary programming language
- **Version**: 3.11 or higher (required for modern type hints)
- **Notes**:
  - Use latest stable Python 3.x version
  - Leverage modern features (match/case, improved error messages, performance improvements)
  - Always use virtual environments (venv)

### Web Framework

#### FastAPI
- **Purpose**: HTTP server and MCP endpoint handler
- **Version**: 0.104.1+ (or latest stable)
- **Notes**:
  - Async-first framework (required for MCP server performance)
  - Automatic OpenAPI documentation generation
  - Pydantic integration for request/response validation
  - Use dependency injection for database sessions and auth

#### Uvicorn
- **Purpose**: ASGI server
- **Version**: 0.24.0+ with standard extras
- **Notes**:
  - Production-grade async server
  - Use `uvicorn[standard]` for performance optimizations
  - Configure with proper workers in production

### MCP Integration

#### MCP Python SDK
- **Purpose**: Official Model Context Protocol implementation
- **Version**: 0.9.0+ (or latest)
- **Notes**:
  - Strict adherence to MCP Specification 2025-06-18
  - Use official SDK for protocol compliance
  - Implement all required methods (initialize, tools/list, tools/call)
  - Follow MCP error code standards

### Database

#### SQLAlchemy 2.0+
- **Purpose**: ORM and database abstraction
- **Version**: 2.0.23+ (required for async support)
- **Notes**:
  - Use async session and engine
  - Leverage 2.0 style queries (not legacy 1.x)
  - All models inherit from declarative_base()
  - Proper relationship mapping

#### SQLite (Development) / PostgreSQL (Production)
- **Development**: SQLite 3.x (file-based, bundled with Python)
- **Production**: PostgreSQL 15+ (Cloud SQL recommended)
- **Notes**:
  - Same ORM code works for both (SQLAlchemy abstraction)
  - Use proper indexes for performance (see PROJECT_SPEC.md)
  - Connection pooling in production

#### Alembic
- **Purpose**: Database migrations
- **Version**: 1.12.1+
- **Notes**:
  - Track all schema changes
  - Migrations must be reversible
  - Test migrations before deployment

### Authentication

#### google-auth
- **Purpose**: OAuth 2.1 implementation
- **Version**: 2.35.0+
- **Notes**:
  - Google OAuth 2.1 for user authentication
  - Dynamic Client Registration for mobile clients
  - Token validation on every MCP tool call
  - Native JWT validation via google.auth.jwt module

#### google-auth-oauthlib
- **Purpose**: OAuth 2.1 flow helpers for Google authentication
- **Version**: 1.2.0+
- **Notes**:
  - Simplifies OAuth authorization code flow
  - Handles PKCE (Proof Key for Code Exchange) for mobile clients
  - Provides credential refreshing utilities
  - Integrates seamlessly with google-auth library

#### python-jose
- **Purpose**: JWT token handling
- **Version**: 3.3.0+ with cryptography extra
- **Notes**:
  - Use `python-jose[cryptography]` for secure crypto
  - Token encoding/decoding
  - Never store secrets in code

#### passlib
- **Purpose**: Password hashing (if needed)
- **Version**: 1.7.4+ with bcrypt extra
- **Notes**:
  - Use bcrypt algorithm
  - Only if implementing custom auth (OAuth is primary)

### Data Validation

#### Pydantic
- **Purpose**: Data validation and settings management
- **Version**: 2.5.0+
- **Notes**:
  - Define all request/response schemas
  - Use for configuration (BaseSettings)
  - Leverage v2 features (serialization modes, computed fields)

#### pydantic-settings
- **Purpose**: Environment-based configuration
- **Version**: 2.1.0+
- **Notes**:
  - Load settings from .env files
  - Type-safe configuration
  - Validation on startup

### Testing

#### pytest
- **Purpose**: Test framework
- **Version**: 7.4.3+
- **Notes**:
  - Write tests before implementation (TDD encouraged)
  - Minimum 80% code coverage required
  - Use fixtures for common setup

#### pytest-asyncio
- **Purpose**: Async test support
- **Version**: 0.21.1+
- **Notes**:
  - Required for testing async functions
  - Use `@pytest.mark.asyncio` decorator
  - Test concurrent operations

#### httpx
- **Purpose**: HTTP client for testing
- **Version**: 0.25.1+
- **Notes**:
  - Test FastAPI endpoints
  - Async client support
  - Better than requests for async code

### Development Tools

#### python-dotenv
- **Purpose**: Environment variable management
- **Version**: 1.0.0+
- **Notes**:
  - Load .env files for local development
  - Never commit .env to git
  - Use .env.example for templates

## Approved Patterns

### Async Everywhere
```python
# ✅ Correct: Async database operations
async def get_task(db: Session, task_id: int):
    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()

# ❌ Wrong: Synchronous database operations
def get_task(db: Session, task_id: int):
    return db.query(Task).filter(Task.id == task_id).first()
```

### Dependency Injection
```python
# ✅ Correct: FastAPI dependency injection
@app.post("/")
async def mcp_handler(
    request: Request,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_from_token)
):
    ...

# ❌ Wrong: Global database connection
db = create_engine(...)  # Global state
```

### Pydantic Schemas
```python
# ✅ Correct: Use Pydantic for validation
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    priority: int = Field(default=3, ge=1, le=5)

# ❌ Wrong: Plain dictionaries without validation
def create_task(data: dict):  # No validation
    ...
```

### User Isolation
```python
# ✅ Correct: Always filter by user_id
async def list_tasks(db: Session, user_id: str):
    query = select(Task).where(Task.user_id == user_id)
    ...

# ❌ Wrong: No user filtering (security vulnerability!)
async def list_tasks(db: Session):
    query = select(Task)  # Returns all users' tasks!
    ...
```

## Prohibited Technologies & Patterns

### ❌ Synchronous Database Operations
- Do not use synchronous SQLAlchemy sessions
- Async is required for MCP server performance
- Blocking operations degrade user experience

### ❌ Global State
- No global database connections
- No global configuration objects (use dependency injection)
- Exception: Settings loaded once at startup

### ❌ Direct SQL Queries
- Always use SQLAlchemy ORM
- Parameterized queries prevent SQL injection
- ORM provides database portability

### ❌ Non-MCP-Compliant Responses
- Must follow MCP spec exactly
- Use correct error codes (-32600, -32601, etc.)
- Response format must match specification

### ❌ Hardcoded Credentials
- Never commit secrets to git
- Use environment variables
- Use Google Secret Manager in production

### ❌ Legacy Python Patterns
- No Python 2.x compatibility code
- No legacy typing (use modern type hints)
- Avoid deprecated libraries (e.g., Flask-SQLAlchemy 2.x)

## External Services & APIs

### Google Cloud Platform
- **Cloud Run**: Container deployment platform
- **Cloud SQL**: Managed PostgreSQL (production)
- **Secret Manager**: Secure credential storage
- **Cloud Logging**: Centralized log aggregation
- **Cloud Monitoring**: Performance metrics

### Google Calendar API (Phase 2)
- **google-api-python-client**: Official client library
- **Purpose**: Calendar integration for task scheduling
- **OAuth Scopes**: calendar.events (read/write)

## Build & Deployment

### Containerization
- **Docker**: Multi-stage builds for minimal image size
- **Base Image**: python:3.11-slim
- **Port**: 8000 (configurable via environment)

### CI/CD
- **GitHub Actions**: Automated testing and deployment
- **Quality Gates**: Type checking, tests, linting, coverage
- **Auto-deploy**: On merge to main (after passing gates)

### Environment Variables
Required in production:
```bash
DATABASE_URL          # PostgreSQL connection string
GOOGLE_CLIENT_ID      # OAuth credentials
GOOGLE_CLIENT_SECRET  # OAuth credentials
SECRET_KEY            # App secret for sessions
ALLOWED_ORIGINS       # CORS configuration
PORT                  # Server port (default: 8080 on Cloud Run)
```

## Dependency Management

### requirements.txt
Maintain a single requirements.txt with pinned versions:
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
mcp==0.9.0
sqlalchemy==2.0.23
...
```

### Virtual Environment
Always use virtual environments:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### Updates
- Review dependency updates monthly
- Test updates in development before production
- Use `/specswarm:upgrade` workflow for major version changes

## Documentation Requirements

### Code Documentation
- All public functions: Docstrings with Args, Returns, Raises
- Complex logic: Inline comments explaining why (not what)
- MCP tools: Complete schema documentation

### Project Documentation
- README.md: High-level overview, quick start
- PROJECT_SPEC.md: Detailed requirements and scope
- ARCHITECTURE.md: System design and data flow
- SETUP_GUIDE.md: Step-by-step implementation guide
- CLAUDE.md: Guidance for AI assistants

## Version Control

### Git Workflow
- Feature branches for all changes
- Pull requests required for main branch
- Squash commits on merge
- Conventional commit messages

### .gitignore
Must ignore:
- `*.pyc`, `__pycache__/`
- `venv/`, `.venv/`
- `.env` (but commit `.env.example`)
- `*.db` (SQLite databases)
- `.DS_Store`, `Thumbs.db`

## Notes

- This stack is specifically designed for MCP server development
- Follows MCP Specification 2025-06-18 requirements
- Optimized for Google Cloud Run deployment
- All technologies chosen for async performance
- Created during project initialization phase
- Update this file when adding new approved technologies

## Changelog

### v1.1.0 (2025-12-26)
- Updated google-auth to v2.35.0+ for enhanced OAuth 2.1 support
- Added google-auth-oauthlib v1.2.0+ for OAuth flow helpers
- Added native JWT validation note (google.auth.jwt module)
- Feature 003: OAuth 2.1 Authentication implementation

### v1.0.0 (2025-12-25)
- Initial technology stack defined
- Python 3.11+, FastAPI, SQLAlchemy 2.0+, MCP SDK specified
- Async-first patterns established
- OAuth 2.1 authentication required
- Google Cloud Platform for deployment
