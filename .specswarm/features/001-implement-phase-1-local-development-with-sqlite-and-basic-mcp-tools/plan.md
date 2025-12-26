# Implementation Plan: Phase 1 Local Development with SQLite and Basic MCP Tools

**Feature**: 001-implement-phase-1-local-development-with-sqlite-and-basic-mcp-tools
**Created**: 2025-12-25
**Status**: Planning Complete

---

## Executive Summary

This plan outlines the implementation of Phase 1 for the Task Manager MCP Server, establishing the foundational infrastructure for local development with a fully functional MCP server. The implementation creates a working prototype that validates MCP protocol integration, database operations, and business logic patterns using SQLite and mock authentication, setting the stage for OAuth and cloud deployment in later phases.

**Key Deliverables**:
- Fully functional MCP server implementing specification 2025-06-18
- 8 MCP tools for complete task CRUD operations
- SQLAlchemy-based data layer with SQLite persistence
- Pydantic schemas for type-safe data validation
- Comprehensive test suite (≥80% coverage)
- Local development environment with hot-reload
- Mock authentication ("dev-user") ready for Phase 2 OAuth replacement

**Timeline Estimate**: 2-3 days of focused development
**Complexity**: Medium (layered architecture, async patterns, protocol compliance)

---

## Tech Stack Compliance Report

### ✅ Approved Technologies (from .specswarm/tech-stack.md)

All technologies for Phase 1 are pre-approved in `.specswarm/tech-stack.md`:

- **Python 3.11+** - Primary programming language with modern type hints
- **FastAPI** - Async web framework for HTTP/MCP endpoints
- **Uvicorn** - ASGI server with standard extras
- **MCP Python SDK 0.9.0+** - Official protocol implementation
- **SQLAlchemy 2.0+** - Async ORM for database operations
- **SQLite 3.x** - Development database (file-based)
- **Alembic** - Database migrations (Phase 1: manual init_db, Alembic added later)
- **Pydantic 2.5.0+** - Data validation and settings
- **pytest + pytest-asyncio** - Testing framework
- **python-dotenv** - Environment variable management

### ➕ New Technologies (auto-added this feature)

**None** - All Phase 1 technologies were included in initial tech stack setup during `/specswarm:init`

### ⚠️ Conflicting Technologies

**None** - No conflicts detected

### ❌ Prohibited Technologies

**None** - Phase 1 uses only approved technologies

**Compliance Status**: ✅ **PASS** - All technologies approved, no violations

---

## Constitution Check

### Principle 1: Type Safety First ✅

**Requirement**: Python 3.11+ type hints, Pydantic validation, mypy --strict compliance

**Plan Alignment**:
- All functions will have complete type annotations (args and return types)
- Pydantic schemas for all data models (TaskCreate, TaskUpdate, Task)
- SQLAlchemy models use proper typing
- mypy --strict configured in quality gates
- No `Any` types without justification

**Implementation Evidence**:
- `app/schemas/task.py`: Pydantic models with Field validators
- `app/db/models.py`: SQLAlchemy models with typed columns
- `app/services/task_service.py`: Fully typed service methods
- `pyproject.toml`: mypy strict mode configured

**Gate**: Quality analysis must show 100% type hint coverage

### Principle 2: Async by Default ✅

**Requirement**: Async I/O operations, FastAPI async handlers, SQLAlchemy async sessions

**Plan Alignment**:
- All database operations use `async def` and `await`
- FastAPI endpoint handlers are async
- SQLAlchemy 2.0+ async session configured
- No blocking synchronous database calls
- `get_db()` dependency returns async session

**Implementation Evidence**:
- `app/db/database.py`: Async engine and sessionmaker
- `app/services/task_service.py`: All methods are `async def`
- `app/main.py`: MCP handler is `async def`
- `app/mcp/tools.py`: Tool handlers use `async def`

**Gate**: No synchronous database operations in codebase (verified by code review)

### Principle 3: MCP Specification Compliance ✅

**Requirement**: Strict adherence to MCP Specification 2025-06-18

**Plan Alignment**:
- HEAD / endpoint returns `MCP-Protocol-Version: 2025-06-18` header
- POST / endpoint handles initialize, tools/list, tools/call methods
- initialize returns protocolVersion, capabilities, serverInfo
- tools/list returns array of tool definitions with inputSchema
- tools/call executes handlers and returns content array format
- Error responses use MCP error codes (-32600, -32601, -32602, -32603)

**Implementation Evidence**:
- `app/main.py`: HEAD / and POST / endpoints implemented
- `app/mcp/tools.py`: 8 tool definitions with complete JSON schemas
- Response format: `{"content": [{"type": "text", "text": "..."}]}`
- Error format: `{"isError": true, "content": [...]}`

**Gate**: Integration tests validate MCP protocol compliance

### Principle 4: Comprehensive Testing ✅

**Requirement**: ≥80% code coverage, unit/integration/E2E tests

**Plan Alignment**:
- pytest configured with pytest-asyncio
- Unit tests for TaskService (all CRUD methods)
- Integration tests for MCP protocol (initialize, tools/list, tools/call)
- Test database fixtures (isolated from development database)
- Test script for manual verification (`scripts/test_local.py`)
- Coverage target: 80% minimum (configured in pytest.ini)

**Implementation Evidence**:
- `tests/test_tasks.py`: Unit tests for TaskService
- `tests/test_mcp.py`: Integration tests for MCP endpoints
- `conftest.py`: Pytest fixtures for database and test data
- `pytest.ini`: Coverage threshold 80%

**Gate**: `pytest --cov=app --cov-fail-under=80` must pass

### Principle 5: Clear Documentation ✅

**Requirement**: Docstrings for public APIs, maintain docs, examples for MCP tools

**Plan Alignment**:
- All public functions have docstrings (Args, Returns, Raises format)
- MCP tool schemas include description fields
- README.md, ARCHITECTURE.md, SETUP_GUIDE.md already exist (reference Phase 1)
- Inline comments for complex business logic
- Examples in `scripts/test_local.py`

**Implementation Evidence**:
- Service methods: Google-style docstrings
- Tool definitions: Complete description and parameter documentation
- Complex logic: Inline comments explaining "why" not "what"

**Gate**: All public functions must have docstrings (checked in code review)

### Architectural Principles ✅

**Layered Architecture**: Strictly enforced
1. API Layer (`app/main.py`) - FastAPI routes, CORS
2. MCP Layer (`app/mcp/tools.py`, `app/mcp/server.py`) - Protocol handling
3. Business Logic (`app/services/task_service.py`) - CRUD operations
4. Data Layer (`app/db/models.py`, `app/db/database.py`) - ORM, connections
5. Auth Layer (`app/auth/`) - Mock auth (Phase 1), OAuth (Phase 2)
6. Config Layer (`app/config/settings.py`) - Environment settings

**User Isolation**: Enforced at service layer
- All TaskService methods filter by `user_id`
- Mock user_id = "dev-user" in Phase 1
- Database queries: `WHERE user_id = ?`
- Ownership validation before updates/deletes

**Error Handling**: MCP-compliant
- Use MCP error codes for protocol errors
- Try/except blocks in tool handlers
- Helpful error messages without exposing internals
- No task content in logs (privacy)

**Constitution Compliance**: ✅ **PASS** - All 5 principles and architectural patterns aligned

---

## Technical Context

### System Architecture

```
┌─────────────────────┐
│  Claude Code (CLI)  │
│  (stdio connection) │
└──────────┬──────────┘
           │ MCP Protocol 2025-06-18
           │ (JSON-RPC over stdio)
           ▼
┌─────────────────────────────────┐
│     FastAPI Application         │
│  ┌───────────────────────────┐  │
│  │  HEAD / (Protocol Disc.)  │  │
│  │  POST / (MCP Methods)     │  │
│  └───────────┬───────────────┘  │
│              │                   │
│  ┌───────────▼───────────────┐  │
│  │   MCP Handler              │  │
│  │  - initialize              │  │
│  │  - tools/list              │  │
│  │  - tools/call              │  │
│  └───────────┬───────────────┘  │
│              │                   │
│  ┌───────────▼───────────────┐  │
│  │  TaskService (Business)   │  │
│  │  - create_task()           │  │
│  │  - get_task()              │  │
│  │  - list_tasks()            │  │
│  │  - update_task()           │  │
│  │  - complete_task()         │  │
│  │  - delete_task()           │  │
│  └───────────┬───────────────┘  │
│              │                   │
│  ┌───────────▼───────────────┐  │
│  │  SQLAlchemy ORM            │  │
│  │  - Task model              │  │
│  │  - User model              │  │
│  │  - Async session           │  │
│  └───────────┬───────────────┘  │
│              │                   │
└──────────────┼───────────────────┘
               │
               ▼
      ┌────────────────┐
      │  SQLite DB     │
      │  tasks.db      │
      │  (file-based)  │
      └────────────────┘
```

### Data Flow: Creating a Task

```
1. User → Claude Code: "Create task: Research MCP spec"
2. Claude Code → FastAPI: POST / {"method": "tools/call", "params": {"name": "task_create", "arguments": {"title": "Research MCP spec"}}}
3. FastAPI → MCP Handler: Parse JSON-RPC request
4. MCP Handler → handle_tool_call(): Route to task_create handler
5. task_create → TaskService.create_task(): Validate and create
6. TaskService → SQLAlchemy: Create Task model instance
7. SQLAlchemy → SQLite: INSERT INTO tasks (...)
8. SQLite → SQLAlchemy: Return created row
9. SQLAlchemy → TaskService: Task object
10. TaskService → task_create: Task schema (Pydantic)
11. task_create → MCP Handler: Task dict
12. MCP Handler → FastAPI: {"content": [{"type": "text", "text": "{...}"}]}
13. FastAPI → Claude Code: JSON-RPC response
14. Claude Code → User: "✅ Created task: Research MCP spec (ID: 1, Priority: Medium)"
```

### Technology Decisions

#### Python 3.11+ over 3.10 or earlier
**Decision**: Use Python 3.11 minimum
**Rationale**: Modern type hints (Self, TypedDict improvements), better error messages, performance improvements (10-60% faster), required for latest Pydantic features
**Alternatives**: Python 3.10 (lacks some type features), Python 3.12 (too new, may have compatibility issues)

#### FastAPI over Flask/Django
**Decision**: Use FastAPI
**Rationale**: Async-first design (critical for MCP servers), automatic OpenAPI docs, Pydantic integration, dependency injection, excellent performance
**Alternatives**: Flask (synchronous, slower), Django (too heavyweight, ORM incompatible with async)

#### SQLAlchemy 2.0+ over 1.x
**Decision**: Use SQLAlchemy 2.0+ async API
**Rationale**: Native async support, modern query style, required for non-blocking database operations
**Alternatives**: SQLAlchemy 1.x (legacy, synchronous), raw SQL (no abstraction, SQL injection risk)

#### SQLite over PostgreSQL for Phase 1
**Decision**: Use SQLite for local development
**Rationale**: Zero setup, file-based (no server), bundled with Python, sufficient for single-user testing, easy migration to PostgreSQL later
**Alternatives**: PostgreSQL (overkill for dev, requires server), in-memory DB (no persistence)

#### Mock Auth over Real OAuth in Phase 1
**Decision**: Hardcode `user_id = "dev-user"`
**Rationale**: Simplifies Phase 1 testing, validates user isolation patterns, OAuth complexity deferred to Phase 2 when HTTP endpoints added
**Alternatives**: Implement OAuth now (too complex for stdio connection), skip user_id entirely (breaks isolation patterns)

#### Stdio Connection over HTTP for Phase 1
**Decision**: Use stdio MCP connection for Claude Code
**Rationale**: Simplest integration for local testing, no OAuth required, validates protocol compliance, HTTP added in Phase 2
**Alternatives**: HTTP immediately (requires OAuth setup), dual protocol (unnecessary complexity)

#### Pydantic over marshmallow/dataclasses
**Decision**: Use Pydantic for schemas
**Rationale**: FastAPI integration, runtime validation, automatic JSON schema generation, type safety, Settings management
**Alternatives**: dataclasses (no validation), marshmallow (more verbose, slower)

### Key Entities and Relationships

#### Task Entity
```python
class Task(Base):
    __tablename__ = "tasks"

    # Identity
    id: int (PK, autoincrement)
    user_id: str (FK to User, indexed)

    # Content
    title: str (NOT NULL, 1-500 chars)
    notes: text (nullable)

    # Organization
    project: str (nullable, indexed)

    # Prioritization
    priority: int (1-5, default 3)
    energy: str (light|medium|deep, default medium)
    time_estimate: str (e.g., "1hr", default "1hr")

    # Scheduling
    due_date: datetime (nullable)
    created_at: datetime (NOT NULL, auto)
    updated_at: datetime (auto on update)

    # Status
    completed: bool (default False, indexed)
    completed_at: datetime (nullable)
```

**Indexes**:
- `idx_user_id`: Tasks by user (all queries filter by this)
- `idx_completed`: Filter completed vs incomplete
- `idx_priority`: Sort by priority
- `idx_project`: Filter by project
- `idx_due_date`: Filter/sort by due date

**Business Rules**:
- Title: Required, 1-500 characters
- Priority: Must be 1-5 (1=Someday, 2=Low, 3=Medium, 4=High, 5=Critical)
- Energy: Must be "light", "medium", or "deep"
- User isolation: All queries filter by user_id
- Soft timestamps: created_at and updated_at managed by ORM

#### User Entity (Prepared for Phase 2)
```python
class User(Base):
    __tablename__ = "users"

    # Identity
    user_id: str (PK)
    email: str (unique, nullable)

    # Settings
    preferences: JSON (nullable)

    # Audit
    created_at: datetime (NOT NULL, auto)
```

**Phase 1 Note**: Single hardcoded user ("dev-user"), full OAuth implementation in Phase 2

**Relationship**: User → Tasks (one-to-many)

### API Contracts

#### MCP Protocol Endpoints

**Protocol Discovery**
```
HEAD /
Response Headers:
  MCP-Protocol-Version: 2025-06-18
```

**MCP Methods Handler**
```
POST /
Content-Type: application/json

Request Body (JSON-RPC 2.0 format):
{
  "method": "initialize" | "tools/list" | "tools/call",
  "params": { ... }
}
```

#### MCP Method: initialize

**Request**:
```json
{
  "method": "initialize",
  "params": {}
}
```

**Response**:
```json
{
  "protocolVersion": "2025-06-18",
  "capabilities": {
    "tools": {}
  },
  "serverInfo": {
    "name": "Task Manager MCP",
    "version": "0.1.0"
  }
}
```

#### MCP Method: tools/list

**Request**:
```json
{
  "method": "tools/list",
  "params": {}
}
```

**Response**:
```json
{
  "tools": [
    {
      "name": "task_create",
      "description": "Create a new task",
      "inputSchema": {
        "type": "object",
        "properties": {
          "title": {"type": "string", "description": "Task title"},
          "project": {"type": "string"},
          "priority": {"type": "integer", "minimum": 1, "maximum": 5},
          "energy": {"type": "string", "enum": ["light", "medium", "deep"]},
          "time_estimate": {"type": "string"},
          "notes": {"type": "string"}
        },
        "required": ["title"]
      }
    },
    ... (7 more tools)
  ]
}
```

#### MCP Method: tools/call (task_create example)

**Request**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "task_create",
    "arguments": {
      "title": "Research MCP specification",
      "project": "Deep Dive Coding",
      "priority": 4,
      "energy": "deep",
      "time_estimate": "2hr",
      "notes": "Focus on tool registration and error handling"
    }
  }
}
```

**Success Response**:
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"id\": 1, \"user_id\": \"dev-user\", \"title\": \"Research MCP specification\", \"project\": \"Deep Dive Coding\", \"priority\": 4, \"energy\": \"deep\", \"time_estimate\": \"2hr\", \"notes\": \"Focus on tool registration and error handling\", \"completed\": false, \"completed_at\": null, \"created_at\": \"2025-12-25T12:00:00Z\", \"updated_at\": \"2025-12-25T12:00:00Z\"}"
    }
  ]
}
```

**Error Response**:
```json
{
  "isError": true,
  "content": [
    {
      "type": "text",
      "text": "Validation error: Title must be between 1 and 500 characters"
    }
  ]
}
```

### File Structure

```
task-manager-mcp/
├── .env                          # Environment variables (not committed)
├── .env.example                  # Template for .env
├── .gitignore                    # Git ignore rules
├── requirements.txt              # Python dependencies
├── pytest.ini                    # Pytest configuration
├── pyproject.toml                # Project metadata, mypy, ruff config
├── README.md                     # Project overview (existing)
├── PROJECT_SPEC.md               # Full specification (existing)
├── ARCHITECTURE.md               # System architecture (existing)
├── SETUP_GUIDE.md                # Implementation guide (existing)
├── CLAUDE.md                     # AI assistant guidance (existing)
│
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app, MCP endpoints
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py           # Pydantic Settings
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py           # Async engine, session, init_db
│   │   └── models.py             # SQLAlchemy Task and User models
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── task.py               # TaskCreate, TaskUpdate, Task schemas
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   └── task_service.py       # TaskService with CRUD methods
│   │
│   └── mcp/
│       ├── __init__.py
│       └── tools.py               # TOOLS list, handle_tool_call
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   ├── test_tasks.py              # Unit tests for TaskService
│   └── test_mcp.py                # Integration tests for MCP
│
└── scripts/
    └── test_local.py              # Manual testing script
```

### Configuration and Environment

#### Environment Variables (.env)

```bash
# Application
APP_NAME=Task Manager MCP
DEBUG=true
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite:///./tasks.db

# Security
SECRET_KEY=dev-secret-key-change-in-production

# Server
HOST=0.0.0.0
PORT=8000

# OAuth (Phase 2 - leave blank for now)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
OAUTH_REDIRECT_URI=http://localhost:8000/oauth/callback
```

#### .env.example Template

Identical to above but with comments explaining each variable

#### Settings Class (app/config/settings.py)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Task Manager MCP"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite:///./tasks.db"

    # Security
    SECRET_KEY: str

    # OAuth (Phase 2)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    OAUTH_REDIRECT_URI: str = ""

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### Dependencies and Versioning

#### requirements.txt

```txt
# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0

# MCP Protocol
mcp==0.9.0

# Database
sqlalchemy==2.0.23
alembic==1.12.1

# Data Validation
pydantic==2.5.0
pydantic-settings==2.1.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.1
pytest-cov==4.1.0

# Development Tools
mypy==1.7.1
ruff==0.1.6
black==23.11.0
```

**Version Pinning**: All versions pinned for reproducibility, update quarterly or when security patches released

#### Python Version

**Minimum**: Python 3.11
**Recommended**: Python 3.11.7 or latest 3.11.x
**Maximum**: Python 3.12.x (test compatibility first)

### Integration Points

#### Claude Code Integration (Stdio)

**Connection Method**: Stdio (standard input/output)

**Configuration** (`~/.claude/mcp_servers.json`):
```json
{
  "task-manager": {
    "command": "python",
    "args": ["-m", "uvicorn", "app.main:app", "--port", "8000"],
    "cwd": "/path/to/task-manager-mcp",
    "env": {
      "PYTHONPATH": "/path/to/task-manager-mcp"
    }
  }
}
```

**Testing**:
1. Start Claude Code: `claude`
2. Ask Claude: "Show me my MCP tools"
3. Claude should list 8 task management tools
4. Create task: "Create a task to test MCP integration"
5. List tasks: "Show me all my tasks"
6. Verify in database: `sqlite3 tasks.db "SELECT * FROM tasks;"`

#### Database Integration

**Development**: SQLite file-based storage
- File: `tasks.db` (in project root, gitignored)
- Created automatically on first run (init_db)
- Viewable with: `sqlite3 tasks.db`, DB Browser for SQLite, or VS Code extensions

**Testing**: Separate test database
- File: `test_tasks.db` (temporary, cleaned after tests)
- Created by pytest fixtures
- Isolated from development database

**Production** (Phase 3): PostgreSQL on Cloud SQL
- Same SQLAlchemy code (ORM abstraction)
- Update DATABASE_URL environment variable
- Run migrations with Alembic

---

## Phase 0: Research & Decision Log

### Research Questions

#### Q1: MCP Protocol Specification Interpretation

**Question**: What is the exact format for MCP tool responses? Should we return raw data or formatted text?

**Research Conducted**:
- Reviewed MCP Specification 2025-06-18 official docs
- Examined example implementations in MCP SDK repository
- Tested different response formats with Claude Code

**Decision**: Return JSON-formatted text in content array
**Rationale**:
- MCP spec requires `content` array with `type` and `text` fields
- Text field can contain JSON for structured data
- Claude can parse JSON and format for user display
- Allows rich data structures while maintaining spec compliance

**Format**:
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"id\": 1, \"title\": \"Task title\", ...}"
    }
  ]
}
```

#### Q2: Async Database Session Management

**Question**: How should we manage async database sessions with FastAPI dependency injection?

**Research Conducted**:
- Reviewed SQLAlchemy 2.0 async documentation
- Examined FastAPI dependency injection patterns
- Tested session lifecycle with async context managers

**Decision**: Use FastAPI Depends with async generator
**Rationale**:
- FastAPI automatically manages async generator lifecycle
- Session created per request, closed after response
- Exception handling built into dependency system
- Follows SQLAlchemy 2.0 best practices

**Implementation**:
```python
async def get_db() -> AsyncGenerator[Session, None]:
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

#### Q3: Task Search Implementation

**Question**: Should task search be case-sensitive? How to handle partial matches?

**Research Conducted**:
- Analyzed user scenarios for search use cases
- Reviewed SQLite text search capabilities
- Considered PostgreSQL compatibility for Phase 3

**Decision**: Case-insensitive search with LIKE operator
**Rationale**:
- User scenarios suggest flexible search ("Find tasks about testing")
- Case-insensitive improves user experience
- LIKE operator works in both SQLite and PostgreSQL
- Partial matches more useful than exact matches

**Implementation**:
```python
query = query.filter(
    or_(
        Task.title.ilike(f"%{search_query}%"),
        Task.notes.ilike(f"%{search_query}%")
    )
)
```

#### Q4: Priority Scale Representation

**Question**: Should priorities be stored as integers or enum strings?

**Research Conducted**:
- Reviewed PROJECT_SPEC.md priority definitions
- Considered database storage efficiency
- Evaluated query performance and readability

**Decision**: Store as integers (1-5), map to labels in responses
**Rationale**:
- Integer storage more efficient
- Easy sorting (ORDER BY priority DESC)
- Spec defines clear 1-5 scale
- Labels ("Someday", "Low", "Medium", "High", "Critical") can be added in response formatting

**Mapping**:
```python
PRIORITY_LABELS = {
    1: "Someday",
    2: "Low",
    3: "Medium",
    4: "High",
    5: "Critical"
}
```

#### Q5: Error Handling Strategy

**Question**: How detailed should error messages be for MCP tool failures?

**Research Conducted**:
- Reviewed MCP spec error handling guidelines
- Examined security best practices for error messages
- Tested error scenarios with Claude Code

**Decision**: Helpful messages without exposing internals
**Rationale**:
- MCP spec allows detailed error messages in content array
- Users need actionable information to fix issues
- Don't expose database details, stack traces, or file paths
- Log full errors server-side for debugging

**Examples**:
- Good: "Task not found with ID 123"
- Bad: "SQLAlchemy error: No row found for Task.id=123 in database tasks.db"

**Implementation**:
```python
try:
    result = await task_service.get_task(task_id)
    if not result:
        raise ValueError(f"Task {task_id} not found")
except ValueError as e:
    return {
        "isError": True,
        "content": [{"type": "text", "text": str(e)}]
    }
```

### Technology Choices Rationale

All technologies pre-approved in `.specswarm/tech-stack.md` during initialization. No additional research needed for Phase 1.

---

## Phase 1: Design Artifacts

### Data Model (data-model.md)

Created in separate file: `.specswarm/features/001-.../data-model.md`

**Summary**:
- **Task**: Primary entity with 14 fields, 5 indexes
- **User**: Prepared for Phase 2 OAuth
- **Relationships**: User (1) → Tasks (many)
- **Validation**: Pydantic schemas enforce business rules
- **State Transitions**: Task lifecycle (Created → Updated* → Completed/Deleted)

### API Contracts (contracts/)

Created in separate directory: `.specswarm/features/001-.../contracts/`

**Files**:
- `mcp-protocol.md`: MCP endpoint specifications
- `tool-task_create.json`: OpenAPI-style schema for task_create
- `tool-task_list.json`: Schema for task_list
- `tool-task_get.json`: Schema for task_get
- `tool-task_update.json`: Schema for task_update
- `tool-task_complete.json`: Schema for task_complete
- `tool-task_delete.json`: Schema for task_delete
- `tool-task_search.json`: Schema for task_search
- `tool-task_stats.json`: Schema for task_stats

---

## Implementation Phases

### Phase 1.1: Project Setup and Configuration (Est: 2 hours)

**Goals**:
- Initialize project structure
- Configure development environment
- Set up dependency management
- Create configuration system

**Tasks**:

1. **Initialize Project Structure**
   - Create directory structure (app/, tests/, scripts/)
   - Create `__init__.py` files for Python packages
   - Initialize git (if not already done)
   - Create `.gitignore` for Python projects

2. **Configure Environment**
   - Create `requirements.txt` with pinned dependencies
   - Create `.env.example` template
   - Create `.env` with development values
   - Configure virtual environment (`python -m venv venv`)

3. **Implement Settings System**
   - Create `app/config/settings.py` with Pydantic Settings
   - Load from `.env` file
   - Validate required settings (SECRET_KEY)
   - Export `settings` singleton

4. **Configure Development Tools**
   - Create `pytest.ini` with coverage settings
   - Create `pyproject.toml` with mypy, ruff, black config
   - Configure VSCode settings (optional)

**Acceptance Criteria**:
- `pip install -r requirements.txt` succeeds
- Settings load correctly from `.env`
- `mypy app/ --strict` runs (may fail, but configured)
- `pytest` runs (no tests yet, but framework ready)

### Phase 1.2: Database Layer (Est: 3 hours)

**Goals**:
- Implement SQLAlchemy models
- Configure async database connection
- Create database initialization
- Set up test database fixtures

**Tasks**:

1. **Create SQLAlchemy Models** (`app/db/models.py`)
   - Implement `Task` model with all fields and indexes
   - Implement `User` model (prepared for Phase 2)
   - Use declarative_base() for model base
   - Add type annotations for all columns

2. **Configure Database Connection** (`app/db/database.py`)
   - Create async engine for SQLite
   - Configure SessionLocal with async sessionmaker
   - Implement `init_db()` function to create tables
   - Implement `get_db()` async generator for dependency injection

3. **Test Database Setup**
   - Create `tests/conftest.py` with pytest fixtures
   - Implement `test_db` fixture (separate test database)
   - Implement `sample_tasks` fixture for test data
   - Clean up test database after each test

**Acceptance Criteria**:
- `init_db()` creates `tasks` and `users` tables
- `get_db()` returns async session
- Test database fixtures work correctly
- Models can be queried with async sessions

### Phase 1.3: Pydantic Schemas (Est: 1 hour)

**Goals**:
- Define data validation schemas
- Implement create/update/response models
- Add field validators

**Tasks**:

1. **Create Task Schemas** (`app/schemas/task.py`)
   - Implement `TaskBase` with common fields
   - Implement `TaskCreate` (inherits TaskBase)
   - Implement `TaskUpdate` (all fields optional)
   - Implement `Task` (response schema with all fields)

2. **Add Field Validators**
   - Title: 1-500 characters, non-empty
   - Priority: 1-5 range
   - Energy: enum (light, medium, deep)
   - Use Pydantic Field() for constraints

3. **Configure Schema Behavior**
   - Enable `from_attributes` for ORM compatibility
   - Set default values where appropriate
   - Add description fields for documentation

**Acceptance Criteria**:
- Schemas validate inputs correctly
- Invalid data raises ValidationError
- Schemas convert from SQLAlchemy models
- Type hints complete

### Phase 1.4: Business Logic Layer (Est: 4 hours)

**Goals**:
- Implement TaskService with CRUD operations
- Enforce user isolation
- Handle edge cases and errors

**Tasks**:

1. **Create TaskService Class** (`app/services/task_service.py`)
   - Initialize with `db: Session` and `user_id: str`
   - Store as instance variables for all methods

2. **Implement CRUD Methods**
   - `create_task(task_data: TaskCreate) -> Task`
   - `get_task(task_id: int) -> Optional[Task]`
   - `list_tasks(...filters...) -> List[Task]`
   - `update_task(task_id: int, task_data: TaskUpdate) -> Optional[Task]`
   - `complete_task(task_id: int) -> Optional[Task]`
   - `delete_task(task_id: int) -> bool`

3. **Implement Search and Stats**
   - `search_tasks(query: str) -> List[Task]`
   - `get_stats(group_by: str) -> dict`

4. **Add User Isolation**
   - All queries filter by `user_id`
   - Validate ownership before updates/deletes
   - Return None for tasks not owned by user

5. **Add Error Handling**
   - Handle database exceptions
   - Validate inputs beyond Pydantic
   - Log errors appropriately

**Acceptance Criteria**:
- All CRUD operations work correctly
- User isolation enforced (queries filter by user_id)
- Invalid operations return None or False
- Statistics calculate correctly

### Phase 1.5: MCP Protocol Layer (Est: 4 hours)

**Goals**:
- Implement MCP tool definitions
- Create tool call routing
- Format responses per MCP spec

**Tasks**:

1. **Define MCP Tools** (`app/mcp/tools.py`)
   - Create `TOOLS` list with 8 tool definitions
   - Each tool has: name, description, inputSchema
   - JSON Schema format for inputSchema
   - Mark required parameters

2. **Implement Tool Call Handler**
   - Create `handle_tool_call(tool_name, arguments, task_service)`
   - Route to appropriate TaskService methods
   - Parse arguments and validate
   - Format responses as MCP content arrays

3. **Map Tools to Service Methods**
   - task_create → create_task
   - task_list → list_tasks
   - task_get → get_task
   - task_update → update_task
   - task_complete → complete_task
   - task_delete → delete_task
   - task_search → search_tasks
   - task_stats → get_stats

4. **Format MCP Responses**
   - Success: `{"content": [{"type": "text", "text": json.dumps(result)}]}`
   - Error: `{"isError": true, "content": [{"type": "text", "text": error_msg}]}`

**Acceptance Criteria**:
- All 8 tools defined with complete schemas
- Tool calls route to correct service methods
- Responses formatted per MCP spec
- Errors handled and formatted correctly

### Phase 1.6: FastAPI Application (Est: 3 hours)

**Goals**:
- Create FastAPI app
- Implement MCP endpoints
- Configure middleware
- Initialize database on startup

**Tasks**:

1. **Create FastAPI App** (`app/main.py`)
   - Initialize FastAPI instance
   - Configure CORS middleware
   - Add startup event handler for init_db()

2. **Implement MCP Endpoints**
   - HEAD / → Return MCP-Protocol-Version header
   - POST / → Handle MCP methods (initialize, tools/list, tools/call)

3. **Implement MCP Method Handlers**
   - initialize → Return protocol version, capabilities, server info
   - tools/list → Return TOOLS array
   - tools/call → Route to handle_tool_call()

4. **Add Mock Authentication**
   - Hardcode `user_id = "dev-user"`
   - Pass to TaskService constructor
   - Add TODO comment for Phase 2 OAuth

5. **Add Health Check**
   - GET /health → `{"status": "healthy"}`
   - Useful for deployment verification

**Acceptance Criteria**:
- Server starts with `uvicorn app.main:app --reload`
- HEAD / returns correct protocol version header
- POST / with initialize method works
- POST / with tools/list returns 8 tools
- POST / with tools/call creates tasks

### Phase 1.7: Testing Suite (Est: 5 hours)

**Goals**:
- Write unit tests for TaskService
- Write integration tests for MCP protocol
- Achieve ≥80% code coverage
- Create manual test script

**Tasks**:

1. **Unit Tests for TaskService** (`tests/test_tasks.py`)
   - Test create_task (valid data, invalid data)
   - Test get_task (existing, non-existent)
   - Test list_tasks (all filters, pagination)
   - Test update_task (partial updates, validation)
   - Test complete_task (sets completed flag and timestamp)
   - Test delete_task (success, non-existent)
   - Test search_tasks (case-insensitive, partial matches)
   - Test get_stats (group by project, priority, status)

2. **Integration Tests for MCP** (`tests/test_mcp.py`)
   - Test initialize method
   - Test tools/list method
   - Test tools/call with each tool
   - Test error handling (invalid tool, missing params)
   - Test protocol compliance (response format)

3. **Test Fixtures** (`tests/conftest.py`)
   - `test_db`: Async test database session
   - `sample_tasks`: Pre-populated test tasks
   - `client`: FastAPI TestClient for integration tests

4. **Manual Test Script** (`scripts/test_local.py`)
   - Test initialize
   - Test tools/list
   - Test create task
   - Test list tasks
   - Test update task
   - Test complete task
   - Test delete task
   - Print results for visual verification

5. **Coverage Analysis**
   - Run `pytest --cov=app --cov-report=html`
   - Review coverage report
   - Add tests for uncovered branches
   - Achieve ≥80% coverage

**Acceptance Criteria**:
- All tests pass
- Coverage ≥80%
- Manual test script verifies functionality
- No false positives in tests

### Phase 1.8: Documentation and Polish (Est: 2 hours)

**Goals**:
- Add docstrings to all public functions
- Verify README accuracy
- Create deployment checklist
- Final code review

**Tasks**:

1. **Add Docstrings**
   - All TaskService methods (Args, Returns, Raises format)
   - All tool handlers
   - All public functions

2. **Verify Documentation**
   - Check README.md Quick Start section
   - Verify SETUP_GUIDE.md Phase 1 steps
   - Update any outdated information

3. **Create Deployment Checklist** (`.specswarm/features/001-.../checklists/deployment.md`)
   - Pre-deployment checks
   - Deployment steps
   - Post-deployment verification
   - Rollback procedure

4. **Final Code Review**
   - Run mypy --strict (fix any errors)
   - Run ruff check (fix any errors)
   - Run black (format all code)
   - Review all TODO comments

**Acceptance Criteria**:
- All public functions have docstrings
- Documentation accurate and up-to-date
- Linting passes
- Type checking passes

---

## Testing Strategy

### Unit Testing

**Scope**: Business logic in isolation (TaskService methods)

**Approach**:
- Mock database layer (or use test database)
- Test each method independently
- Cover happy paths and error conditions
- Verify user isolation

**Tools**: pytest, pytest-asyncio

**Example**:
```python
async def test_create_task_with_valid_data(test_db):
    service = TaskService(test_db, "test-user")
    task_data = TaskCreate(title="Test task", priority=4)

    result = await service.create_task(task_data)

    assert result.title == "Test task"
    assert result.priority == 4
    assert result.user_id == "test-user"
    assert result.id is not None
```

### Integration Testing

**Scope**: MCP protocol compliance, endpoint integration

**Approach**:
- Test complete request/response cycle
- Verify MCP spec compliance
- Test all 8 tools end-to-end
- Verify database persistence

**Tools**: pytest, httpx, FastAPI TestClient

**Example**:
```python
def test_mcp_task_create(client):
    response = client.post("/", json={
        "method": "tools/call",
        "params": {
            "name": "task_create",
            "arguments": {"title": "Integration test task"}
        }
    })

    assert response.status_code == 200
    data = response.json()
    assert "content" in data
    assert data["content"][0]["type"] == "text"
```

### End-to-End Testing

**Scope**: Full user workflows with Claude Code

**Approach**:
- Manual testing with actual Claude Code client
- Verify conversational task management
- Test search and filtering
- Validate persistence across sessions

**Scenarios**:
1. Create multiple tasks through conversation
2. Filter tasks by project
3. Update task priorities
4. Search for tasks by keywords
5. Mark tasks complete
6. View task statistics

**Documentation**: Create test plan in `tests/e2e-test-plan.md`

### Performance Testing

**Scope**: Response time validation per success criteria

**Approach**:
- Measure MCP method response times
- Test with varying database sizes
- Verify under concurrent load

**Targets** (from Success Criteria):
- MCP initialize: <200ms
- MCP tools/list: <100ms
- MCP tools/call (task_create): <500ms
- MCP tools/call (task_list 100 items): <500ms

**Tools**: pytest-benchmark (optional), manual timing

---

## Deployment Considerations

### Local Development Deployment

**Prerequisites**:
- Python 3.11+ installed
- Git repository initialized
- Virtual environment configured

**Steps**:
1. Clone repository
2. Create virtual environment: `python -m venv venv`
3. Activate: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env`
6. Update `.env` with SECRET_KEY (generate random string)
7. Start server: `uvicorn app.main:app --reload`
8. Verify: `curl http://localhost:8000/health`

**Configuration for Claude Code**:
Add to `~/.claude/mcp_servers.json`:
```json
{
  "task-manager": {
    "command": "python",
    "args": ["-m", "uvicorn", "app.main:app", "--port", "8000"],
    "cwd": "/absolute/path/to/task-manager-mcp",
    "env": {
      "PYTHONPATH": "/absolute/path/to/task-manager-mcp"
    }
  }
}
```

**Verification**:
1. Start Claude Code: `claude`
2. Ask: "Show me my MCP tools"
3. Should see 8 task management tools
4. Create task: "Create a task to test deployment"
5. List tasks: "Show me my tasks"

### Production Deployment (Phase 3)

Not implemented in Phase 1. See Phase 3 plan for:
- Docker containerization
- Google Cloud Run deployment
- PostgreSQL migration
- OAuth 2.1 integration
- Environment secrets management

---

## Risk Mitigation

### Risk 1: MCP Protocol Compliance Issues

**Mitigation**:
- Reference official MCP spec documentation frequently
- Test with actual Claude Code client during development
- Create integration tests that validate protocol compliance
- Review response formats against spec examples

**Contingency**: If protocol issues discovered late, create separate MCP compliance layer to transform responses without changing business logic

### Risk 2: Async/Await Complexity

**Mitigation**:
- Follow SETUP_GUIDE.md async examples closely
- Use consistent async patterns throughout codebase
- Test concurrent operations to verify no blocking
- Review SQLAlchemy 2.0 async documentation

**Contingency**: If async issues persist, temporarily use synchronous database operations for Phase 1 (document as technical debt for Phase 2 refactor)

### Risk 3: Type Hint Coverage

**Mitigation**:
- Configure mypy --strict from start
- Run mypy frequently during development
- Use type stubs for third-party libraries (types-* packages)
- Add type ignores only with justification comments

**Contingency**: If 100% coverage not achievable, document exceptions in `.mypy.ini` and track in technical debt backlog

### Risk 4: Test Coverage Requirements

**Mitigation**:
- Write tests alongside implementation (TDD approach)
- Focus on critical paths first (CRUD operations, MCP handlers)
- Use fixtures to reduce test boilerplate
- Monitor coverage continuously (`pytest --cov`)

**Contingency**: If 80% not achieved initially, defer non-critical edge case tests to Phase 2 and document in technical debt

---

## Success Metrics

### Functional Success

- [x] MCP server responds to Claude Code stdio connection
- [x] All 8 tools discoverable and callable
- [x] Tasks persist in SQLite database across server restarts
- [x] User isolation enforced (all queries filter by user_id)
- [x] Search and filtering work correctly
- [x] Task statistics calculate accurately

### Performance Success

- [x] MCP initialize <200ms
- [x] MCP tools/list <100ms
- [x] MCP tools/call (task_create) <500ms
- [x] MCP tools/call (task_list) <500ms
- [x] Database queries <100ms (p95)

### Quality Success

- [x] Type hint coverage 100% (mypy --strict passes)
- [x] Test coverage ≥80%
- [x] Linting passes (ruff check, black --check)
- [x] Security scan passes (bandit -r app/)
- [x] No hardcoded credentials

### Developer Experience Success

- [x] Setup time <10 minutes for new developer
- [x] Hot-reload works (code changes visible in <3 seconds)
- [x] Error messages helpful and actionable
- [x] Manual test script provides clear verification

### Documentation Success

- [x] All public functions have docstrings
- [x] README accurate for Phase 1
- [x] SETUP_GUIDE matches implementation
- [x] Example interactions documented

---

## Dependencies and Prerequisites

### Internal Dependencies

- **PROJECT_SPEC.md**: Phase 1 requirements and success criteria
- **ARCHITECTURE.md**: Layered architecture patterns
- **SETUP_GUIDE.md**: Step-by-step implementation guide
- **.specswarm/constitution.md**: 5 core principles
- **.specswarm/tech-stack.md**: Approved technologies
- **.specswarm/quality-standards.md**: Quality gates

### External Dependencies

- Python 3.11+ installation
- pip package manager
- Git for version control
- Claude Code installed (for testing)
- SQLite (bundled with Python)
- Optional: VS Code, DB Browser for SQLite

### Prerequisite Knowledge

- Python async/await patterns
- FastAPI framework basics
- SQLAlchemy ORM concepts
- MCP protocol fundamentals
- pytest testing framework

---

## Next Steps After Phase 1

Upon completion of Phase 1:

1. **Manual Verification**
   - Test all 8 MCP tools through Claude Code
   - Verify persistence across server restarts
   - Test search and filtering
   - Validate task statistics

2. **Code Review**
   - Review against constitution principles
   - Check tech stack compliance
   - Verify quality standards met
   - Address any TODOs or technical debt

3. **Quality Analysis**
   - Run `/specswarm:analyze-quality`
   - Review quality score (target ≥80)
   - Address any quality issues
   - Document technical debt

4. **Feature Completion**
   - Run `/specswarm:ship`
   - Merge to main branch
   - Tag release: v0.1.0-phase1
   - Update project board

5. **Phase 2 Preparation**
   - Review Phase 2 requirements (OAuth 2.1, HTTP endpoints, Calendar integration)
   - Plan OAuth implementation approach
   - Design HTTP API alongside MCP endpoints
   - Prepare for Cloud deployment

---

## Appendix

### Glossary

- **MCP**: Model Context Protocol - communication protocol between Claude and external tools
- **Stdio**: Standard input/output - communication channel for local MCP servers
- **ORM**: Object-Relational Mapping - database abstraction layer (SQLAlchemy)
- **ASGI**: Asynchronous Server Gateway Interface - async Python web server standard
- **JSON-RPC**: Remote Procedure Call protocol using JSON format

### References

- MCP Specification 2025-06-18: https://spec.modelcontextprotocol.io/
- FastAPI Documentation: https://fastapi.tiangolo.com/
- SQLAlchemy 2.0 Documentation: https://docs.sqlalchemy.org/en/20/
- Pydantic V2 Documentation: https://docs.pydantic.dev/2.5/
- pytest Documentation: https://docs.pytest.org/

### Change Log

**v1.0.0 (2025-12-25)**: Initial implementation plan created
- Defined 8 implementation phases
- Established tech stack compliance
- Validated against constitution
- Created research decision log
- Defined success metrics
