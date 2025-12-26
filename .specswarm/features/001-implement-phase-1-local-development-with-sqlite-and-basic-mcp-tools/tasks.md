# Tasks: Phase 1 Local Development with SQLite and Basic MCP Tools

**Feature**: 001-implement-phase-1-local-development-with-sqlite-and-basic-mcp-tools
**Created**: 2025-12-25
**Status**: Ready for Implementation

<!-- Tech Stack Validation: PASSED -->
<!-- Validated against: .specswarm/tech-stack.md v1.0.0 -->
<!-- No prohibited technologies found -->
<!-- All technologies pre-approved -->

---

## Overview

This task breakdown implements Phase 1 of the Task Manager MCP Server through 8 sequential phases, organized by logical dependencies and implementation order. The tasks build from foundational infrastructure through complete MCP protocol integration with comprehensive testing.

**Total Tasks**: 43 tasks across 8 phases
**Estimated Timeline**: 20-24 hours of focused development
**Test Coverage Target**: ≥80%
**Type Safety Target**: 100% (mypy --strict)

**Organization Strategy**:
- Phase 1: Project Setup (Tasks T001-T004) - 2 hours
- Phase 2: Database Layer (Tasks T005-T007) - 3 hours
- Phase 3: Data Validation (Tasks T008-T009) - 1 hour
- Phase 4: Business Logic (Tasks T010-T017) - 4 hours
- Phase 5: MCP Protocol (Tasks T018-T025) - 4 hours
- Phase 6: Application Integration (Tasks T026-T030) - 3 hours
- Phase 7: Testing Suite (Tasks T031-T042) - 5 hours
- Phase 8: Documentation & Polish (Tasks T043) - 2 hours

---

## Phase 1: Project Setup & Configuration

**Goal**: Initialize project structure, configure development environment, establish settings system

**Dependencies**: None (entry point)

**Test Criteria**:
- Virtual environment activates successfully
- All dependencies install without conflicts
- Settings load from .env file correctly
- Development tools (mypy, ruff, black, pytest) configured and runnable

### T001: Initialize Project Structure [P]
**Description**: Create complete directory structure and Python package files

**Files to Create**:
- `app/__init__.py`
- `app/config/__init__.py`
- `app/db/__init__.py`
- `app/schemas/__init__.py`
- `app/services/__init__.py`
- `app/mcp/__init__.py`
- `tests/__init__.py`
- `scripts/` (directory)

**Acceptance Criteria**:
- All directories and `__init__.py` files created
- Python can import from `app` package
- Structure matches ARCHITECTURE.md layout

**Estimated Time**: 15 minutes

---

### T002: Configure Development Environment [P]
**Description**: Set up virtual environment and install all Phase 1 dependencies

**Files to Create**:
- `requirements.txt`
- `.gitignore`

**Dependencies Content** (requirements.txt):
```
# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0

# MCP Protocol
mcp==0.9.0

# Database
sqlalchemy==2.0.23

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

**Commands to Run**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

**Acceptance Criteria**:
- Virtual environment created successfully
- All packages install without conflicts
- `pip list` shows all required packages with correct versions

**Estimated Time**: 20 minutes

---

### T003: Create Environment Configuration System
**Description**: Implement Pydantic Settings for environment-based configuration

**Files to Create**:
- `app/config/settings.py`
- `.env.example`
- `.env` (not committed, developer creates from example)

**Implementation** (app/config/settings.py):
```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Task Manager MCP"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite:///./tasks.db"

    # Security
    SECRET_KEY: str

    # OAuth (Phase 2 - leave blank for now)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    OAUTH_REDIRECT_URI: str = ""

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    ALLOWED_ORIGINS: str = "*"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

**Acceptance Criteria**:
- Settings class loads from .env file
- Missing .env file uses defaults where appropriate
- Required settings (SECRET_KEY) raise error if missing
- Settings accessible via `from app.config.settings import settings`

**Estimated Time**: 30 minutes

---

### T004: Configure Development Tools
**Description**: Set up mypy, ruff, black, and pytest configuration files

**Files to Create**:
- `pyproject.toml`
- `pytest.ini`

**Implementation** (pyproject.toml):
```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]  # Line too long (handled by black)

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = [
    "--strict-markers",
    "--cov=app",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-fail-under=80",
]
asyncio_mode = "auto"
```

**Acceptance Criteria**:
- `mypy app/ --strict` runs (may have errors, but command works)
- `ruff check app/` runs
- `black --check app/` runs
- `pytest` discovers test directory

**Estimated Time**: 15 minutes

**Phase 1 Checkpoint**: ✅ Project structure initialized, dependencies installed, configuration system ready

---

## Phase 2: Database Layer

**Goal**: Implement SQLAlchemy models, database connection, initialization

**Dependencies**: Phase 1 (settings system)

**Test Criteria**:
- `init_db()` creates tasks and users tables
- `get_db()` returns async database session
- Models can be queried with async operations
- Test database fixtures work independently

### T005: Create SQLAlchemy Models
**Description**: Implement Task and User models with proper typing and indexes

**File to Create**: `app/db/models.py`

**Implementation**:
```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"

    # Identity
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)

    # Content
    title = Column(String, nullable=False)
    notes = Column(Text)

    # Organization
    project = Column(String, index=True)

    # Prioritization
    priority = Column(Integer, default=3)
    energy = Column(String, default="medium")
    time_estimate = Column(String, default="1hr")

    # Scheduling
    due_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Status
    completed = Column(Boolean, default=False, index=True)
    completed_at = Column(DateTime)

class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True)
    email = Column(String, unique=True)
    preferences = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

**Acceptance Criteria**:
- Task model has all 14 fields from data-model.md
- User model prepared for Phase 2 OAuth
- All indexes defined correctly
- Type annotations complete

**Estimated Time**: 45 minutes

---

### T006: Implement Database Connection and Initialization
**Description**: Configure async SQLAlchemy engine, session, and table creation

**File to Create**: `app/db/database.py`

**Implementation**:
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session
from typing import AsyncGenerator
from .models import Base
from ..config.settings import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://"),
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG
)

# Create async session factory
SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db() -> None:
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session"""
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

**Acceptance Criteria**:
- Async engine created correctly
- `init_db()` creates tables on first run
- `get_db()` yields async session
- Session closes properly after use

**Estimated Time**: 1 hour

---

### T007: Create Test Database Fixtures
**Description**: Set up pytest fixtures for test database and sample data

**File to Create**: `tests/conftest.py`

**Implementation**:
```python
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.db.models import Base, Task
from datetime import datetime

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def test_db():
    """Create test database with tables"""
    engine = create_async_engine(TEST_DATABASE_URL)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def sample_tasks(test_db):
    """Create sample tasks for testing"""
    tasks = [
        Task(user_id="test-user", title="Test task 1", priority=4),
        Task(user_id="test-user", title="Test task 2", project="Testing", completed=True),
        Task(user_id="other-user", title="Other user task", priority=5)
    ]

    for task in tasks:
        test_db.add(task)

    await test_db.commit()

    return tasks
```

**Acceptance Criteria**:
- Test database uses in-memory SQLite
- Fixtures create and clean up database correctly
- Sample tasks available for test isolation
- Tests don't interfere with development database

**Estimated Time**: 1 hour 15 minutes

**Phase 2 Checkpoint**: ✅ Database layer complete, models defined, async operations working

---

## Phase 3: Data Validation Schemas

**Goal**: Implement Pydantic schemas for request validation and response serialization

**Dependencies**: Phase 2 (models exist for reference)

**Test Criteria**:
- Schemas validate inputs correctly
- Invalid data raises ValidationError with helpful messages
- Schemas convert from SQLAlchemy models
- Type hints complete for all fields

### T008: Create Task Pydantic Schemas
**Description**: Implement TaskBase, TaskCreate, TaskUpdate, and Task response schemas

**File to Create**: `app/schemas/task.py`

**Implementation**:
```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500, description="Task title")
    project: Optional[str] = Field(None, description="Project category")
    priority: int = Field(default=3, ge=1, le=5, description="Priority (1-5)")
    energy: str = Field(default="medium", pattern="^(light|medium|deep)$")
    time_estimate: str = Field(default="1hr", description="Time estimate")
    notes: Optional[str] = None
    due_date: Optional[datetime] = None

class TaskCreate(TaskBase):
    """Schema for creating a new task"""
    pass

class TaskUpdate(BaseModel):
    """Schema for updating a task (all fields optional)"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    project: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    energy: Optional[str] = Field(None, pattern="^(light|medium|deep)$")
    time_estimate: Optional[str] = None
    notes: Optional[str] = None
    due_date: Optional[datetime] = None
    completed: Optional[bool] = None

class Task(TaskBase):
    """Schema for task response"""
    id: int
    user_id: str
    completed: bool
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

**Acceptance Criteria**:
- TaskCreate validates required fields (title)
- TaskUpdate allows partial updates (all optional)
- Task schema includes all database fields
- Field validators enforce business rules (priority 1-5, energy enum)
- `from_attributes = True` enables ORM model conversion

**Estimated Time**: 45 minutes

---

### T009: Add Schema Unit Tests [P]
**Description**: Test Pydantic schema validation rules

**File to Create**: `tests/test_schemas.py`

**Test Cases**:
- Valid TaskCreate data passes validation
- Empty title fails validation
- Priority outside 1-5 range fails
- Invalid energy value fails
- TaskUpdate with partial data validates
- Task schema converts from ORM model

**Acceptance Criteria**:
- All validation rules tested
- Error messages helpful
- Tests cover edge cases

**Estimated Time**: 30 minutes

**Phase 3 Checkpoint**: ✅ Data validation schemas complete, validation rules enforced

---

## Phase 4: Business Logic Layer

**Goal**: Implement TaskService with all CRUD operations, search, and statistics

**Dependencies**: Phase 2 (models), Phase 3 (schemas)

**Test Criteria**:
- All CRUD operations work correctly
- User isolation enforced (queries filter by user_id)
- Edge cases handled (not found, invalid data)
- Statistics calculate accurately

### T010: Create TaskService Class Structure
**Description**: Initialize TaskService with database session and user_id

**File to Create**: `app/services/task_service.py`

**Implementation** (class structure only):
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, or_, func
from typing import List, Optional
from datetime import datetime
from ..db.models import Task as TaskModel
from ..schemas.task import TaskCreate, TaskUpdate, Task

class TaskService:
    """Service for task CRUD operations with user isolation"""

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
```

**Acceptance Criteria**:
- Class initialized with db session and user_id
- Type hints for constructor parameters

**Estimated Time**: 10 minutes

---

### T011: Implement create_task Method
**Description**: Create new task with validation and user association

**Add to**: `app/services/task_service.py`

**Implementation**:
```python
async def create_task(self, task_data: TaskCreate) -> Task:
    """Create a new task

    Args:
        task_data: Task creation data

    Returns:
        Created task with ID
    """
    task = TaskModel(
        user_id=self.user_id,
        **task_data.model_dump()
    )
    self.db.add(task)
    await self.db.commit()
    await self.db.refresh(task)
    return Task.model_validate(task)
```

**Acceptance Criteria**:
- Task created with user_id
- Database persists task
- Returns Task schema
- Timestamps auto-generated

**Estimated Time**: 20 minutes

---

### T012: Implement get_task Method
**Description**: Retrieve single task by ID with user isolation

**Add to**: `app/services/task_service.py`

**Implementation**:
```python
async def get_task(self, task_id: int) -> Optional[Task]:
    """Get task by ID (with user isolation)

    Args:
        task_id: Task ID to retrieve

    Returns:
        Task if found and owned by user, None otherwise
    """
    result = await self.db.execute(
        select(TaskModel).filter(
            TaskModel.id == task_id,
            TaskModel.user_id == self.user_id
        )
    )
    task = result.scalar_one_or_none()
    return Task.model_validate(task) if task else None
```

**Acceptance Criteria**:
- Returns task if found and owned by user
- Returns None if not found or owned by different user
- User isolation enforced

**Estimated Time**: 20 minutes

---

### T013: Implement list_tasks Method
**Description**: List tasks with filters, sorting, and pagination

**Add to**: `app/services/task_service.py`

**Implementation**:
```python
async def list_tasks(
    self,
    project: Optional[str] = None,
    priority: Optional[int] = None,
    show_completed: bool = False,
    limit: int = 100,
    offset: int = 0
) -> List[Task]:
    """List tasks with filters

    Args:
        project: Filter by project
        priority: Filter by priority
        show_completed: Include completed tasks
        limit: Maximum results (default 100)
        offset: Pagination offset

    Returns:
        List of tasks matching filters
    """
    query = select(TaskModel).filter(TaskModel.user_id == self.user_id)

    if not show_completed:
        query = query.filter(TaskModel.completed == False)

    if project:
        query = query.filter(TaskModel.project == project)

    if priority:
        query = query.filter(TaskModel.priority == priority)

    query = query.order_by(
        TaskModel.priority.desc(),
        TaskModel.created_at
    ).offset(offset).limit(limit)

    result = await self.db.execute(query)
    tasks = result.scalars().all()
    return [Task.model_validate(t) for t in tasks]
```

**Acceptance Criteria**:
- Filters work correctly (project, priority, completed)
- Sorting by priority desc, then created_at
- Pagination with limit and offset
- User isolation enforced

**Estimated Time**: 30 minutes

---

### T014: Implement update_task and complete_task Methods
**Description**: Update task fields and mark tasks complete

**Add to**: `app/services/task_service.py`

**Implementation**:
```python
async def update_task(self, task_id: int, task_data: TaskUpdate) -> Optional[Task]:
    """Update a task (partial updates supported)

    Args:
        task_id: Task ID to update
        task_data: Fields to update

    Returns:
        Updated task if found, None otherwise
    """
    result = await self.db.execute(
        select(TaskModel).filter(
            TaskModel.id == task_id,
            TaskModel.user_id == self.user_id
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        return None

    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    await self.db.commit()
    await self.db.refresh(task)
    return Task.model_validate(task)

async def complete_task(self, task_id: int) -> Optional[Task]:
    """Mark task as complete

    Args:
        task_id: Task ID to complete

    Returns:
        Updated task if found, None otherwise
    """
    result = await self.db.execute(
        select(TaskModel).filter(
            TaskModel.id == task_id,
            TaskModel.user_id == self.user_id
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        return None

    task.completed = True
    task.completed_at = datetime.utcnow()
    await self.db.commit()
    await self.db.refresh(task)
    return Task.model_validate(task)
```

**Acceptance Criteria**:
- Update modifies only specified fields
- Complete sets completed flag and timestamp
- User isolation enforced
- Returns None if task not found or not owned

**Estimated Time**: 30 minutes

---

### T015: Implement delete_task Method
**Description**: Delete task with user isolation

**Add to**: `app/services/task_service.py`

**Implementation**:
```python
async def delete_task(self, task_id: int) -> bool:
    """Delete a task

    Args:
        task_id: Task ID to delete

    Returns:
        True if deleted, False if not found
    """
    result = await self.db.execute(
        delete(TaskModel).filter(
            TaskModel.id == task_id,
            TaskModel.user_id == self.user_id
        )
    )
    await self.db.commit()
    return result.rowcount > 0
```

**Acceptance Criteria**:
- Task deleted from database
- Returns True if deleted, False if not found
- User isolation enforced

**Estimated Time**: 15 minutes

---

### T016: Implement search_tasks Method
**Description**: Search tasks by keywords in title and notes

**Add to**: `app/services/task_service.py`

**Implementation**:
```python
async def search_tasks(self, query: str, fields: str = "both") -> List[Task]:
    """Search tasks by keywords

    Args:
        query: Search keywords
        fields: Fields to search (title, notes, or both)

    Returns:
        List of matching tasks
    """
    search_filter = []

    if fields in ["title", "both"]:
        search_filter.append(TaskModel.title.ilike(f"%{query}%"))

    if fields in ["notes", "both"]:
        search_filter.append(TaskModel.notes.ilike(f"%{query}%"))

    result = await self.db.execute(
        select(TaskModel).filter(
            TaskModel.user_id == self.user_id,
            or_(*search_filter)
        ).order_by(TaskModel.priority.desc(), TaskModel.created_at)
    )

    tasks = result.scalars().all()
    return [Task.model_validate(t) for t in tasks]
```

**Acceptance Criteria**:
- Case-insensitive search
- Searches title, notes, or both
- Returns tasks matching query
- User isolation enforced

**Estimated Time**: 25 minutes

---

### T017: Implement get_stats Method
**Description**: Calculate task statistics grouped by project, priority, or status

**Add to**: `app/services/task_service.py`

**Implementation**:
```python
async def get_stats(self, group_by: Optional[str] = None) -> dict:
    """Get task statistics

    Args:
        group_by: Group by project, priority, or status

    Returns:
        Statistics dict
    """
    # Total and completion stats
    total_result = await self.db.execute(
        select(
            func.count(TaskModel.id).label("total"),
            func.sum(func.cast(TaskModel.completed, Integer)).label("completed")
        ).filter(TaskModel.user_id == self.user_id)
    )
    totals = total_result.first()

    stats = {
        "total": totals.total or 0,
        "completed": totals.completed or 0,
        "completion_rate": round((totals.completed or 0) * 100.0 / (totals.total or 1), 2)
    }

    # Group by specified field
    if group_by == "project":
        result = await self.db.execute(
            select(
                TaskModel.project,
                func.count(TaskModel.id).label("count")
            ).filter(
                TaskModel.user_id == self.user_id,
                TaskModel.completed == False
            ).group_by(TaskModel.project)
        )
        stats["by_project"] = {row.project or "None": row.count for row in result}

    elif group_by == "priority":
        result = await self.db.execute(
            select(
                TaskModel.priority,
                func.count(TaskModel.id).label("count")
            ).filter(
                TaskModel.user_id == self.user_id,
                TaskModel.completed == False
            ).group_by(TaskModel.priority)
        )
        stats["by_priority"] = {row.priority: row.count for row in result}

    return stats
```

**Acceptance Criteria**:
- Returns total, completed, and completion_rate
- Groups by project, priority, or status when requested
- User isolation enforced
- Handles empty database gracefully

**Estimated Time**: 40 minutes

**Phase 4 Checkpoint**: ✅ Business logic complete, all CRUD operations implemented

---

## Phase 5: MCP Protocol Layer

**Goal**: Implement MCP tool definitions and tool call routing per MCP Specification 2025-06-18

**Dependencies**: Phase 4 (TaskService exists)

**Test Criteria**:
- All 8 tools defined with complete JSON schemas
- Tool calls route to correct service methods
- Responses formatted per MCP spec
- Errors handled and formatted correctly

### T018: Define MCP Tool Schemas
**Description**: Create TOOLS list with 8 tool definitions and JSON schemas

**File to Create**: `app/mcp/tools.py`

**Implementation** (partial, showing structure):
```python
from typing import Dict, Any, List

TOOLS = [
    {
        "name": "task_create",
        "description": "Create a new task",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Task title (1-500 chars)"},
                "project": {"type": "string", "description": "Project category"},
                "priority": {"type": "integer", "minimum": 1, "maximum": 5, "description": "Priority (1=Someday, 5=Critical, default=3)"},
                "energy": {"type": "string", "enum": ["light", "medium", "deep"], "description": "Energy level (default=medium)"},
                "time_estimate": {"type": "string", "description": "Time estimate (default='1hr')"},
                "notes": {"type": "string", "description": "Additional notes"}
            },
            "required": ["title"]
        }
    },
    {
        "name": "task_list",
        "description": "List tasks with optional filters",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "priority": {"type": "integer", "minimum": 1, "maximum": 5},
                "show_completed": {"type": "boolean", "default": False},
                "limit": {"type": "integer", "default": 100},
                "offset": {"type": "integer", "default": 0}
            }
        }
    },
    # ... (6 more tools: task_get, task_update, task_complete, task_delete, task_search, task_stats)
]
```

**Acceptance Criteria**:
- All 8 tools defined
- Each tool has name, description, inputSchema
- inputSchema follows JSON Schema format
- Required parameters marked in schema

**Estimated Time**: 1 hour

---

### T019: Implement task_create Tool Handler
**Description**: Route task_create calls to TaskService.create_task

**Add to**: `app/mcp/tools.py`

**Implementation**:
```python
from ..services.task_service import TaskService
from ..schemas.task import TaskCreate

async def handle_tool_call(tool_name: str, arguments: Dict[str, Any], task_service: TaskService) -> Any:
    """Route tool calls to appropriate handlers"""

    if tool_name == "task_create":
        task_data = TaskCreate(**arguments)
        result = await task_service.create_task(task_data)
        return result.model_dump()
```

**Acceptance Criteria**:
- Arguments validated via TaskCreate schema
- TaskService.create_task called
- Result converted to dict
- ValidationError raised if arguments invalid

**Estimated Time**: 20 minutes

---

### T020: Implement task_list and task_get Tool Handlers
**Description**: Route list and get calls to TaskService methods

**Add to**: `app/mcp/tools.py`

**Implementation**:
```python
elif tool_name == "task_list":
    tasks = await task_service.list_tasks(**arguments)
    return [t.model_dump() for t in tasks]

elif tool_name == "task_get":
    task = await task_service.get_task(arguments["task_id"])
    if not task:
        raise ValueError(f"Task {arguments['task_id']} not found")
    return task.model_dump()
```

**Acceptance Criteria**:
- task_list returns array of task dicts
- task_get returns single task dict or raises ValueError
- Filters passed correctly to service layer

**Estimated Time**: 20 minutes

---

### T021: Implement task_update and task_complete Tool Handlers
**Description**: Route update and complete calls to TaskService

**Add to**: `app/mcp/tools.py`

**Implementation**:
```python
elif tool_name == "task_update":
    task_id = arguments.pop("task_id")
    from ..schemas.task import TaskUpdate
    task_data = TaskUpdate(**arguments)
    task = await task_service.update_task(task_id, task_data)
    if not task:
        raise ValueError(f"Task {task_id} not found")
    return task.model_dump()

elif tool_name == "task_complete":
    task = await task_service.complete_task(arguments["task_id"])
    if not task:
        raise ValueError(f"Task {arguments['task_id']} not found")
    return task.model_dump()
```

**Acceptance Criteria**:
- task_update handles partial updates
- task_complete sets completed flag
- Raises ValueError if task not found

**Estimated Time**: 20 minutes

---

### T022: Implement task_delete, task_search, task_stats Tool Handlers
**Description**: Route remaining tools to TaskService methods

**Add to**: `app/mcp/tools.py`

**Implementation**:
```python
elif tool_name == "task_delete":
    success = await task_service.delete_task(arguments["task_id"])
    if not success:
        raise ValueError(f"Task {arguments['task_id']} not found")
    return {"success": True, "task_id": arguments["task_id"]}

elif tool_name == "task_search":
    query = arguments["query"]
    fields = arguments.get("fields", "both")
    tasks = await task_service.search_tasks(query, fields)
    return [t.model_dump() for t in tasks]

elif tool_name == "task_stats":
    group_by = arguments.get("group_by")
    stats = await task_service.get_stats(group_by)
    return stats

else:
    raise ValueError(f"Unknown tool: {tool_name}")
```

**Acceptance Criteria**:
- All 8 tools routed correctly
- Unknown tools raise ValueError
- Results formatted as dicts/arrays

**Estimated Time**: 25 minutes

---

### T023: Add Type Hints to Tool Handler [P]
**Description**: Complete type annotations for handle_tool_call function

**Modify**: `app/mcp/tools.py`

**Type Hints**:
```python
from typing import Dict, Any, Union, List

async def handle_tool_call(
    tool_name: str,
    arguments: Dict[str, Any],
    task_service: TaskService
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
```

**Acceptance Criteria**:
- All parameters typed
- Return type specifies dict or list of dicts
- mypy --strict passes

**Estimated Time**: 15 minutes

---

### T024: Add Tool Handler Docstrings [P]
**Description**: Document each tool handler section with purpose and examples

**Modify**: `app/mcp/tools.py`

**Acceptance Criteria**:
- Main function has docstring with Args, Returns, Raises
- Each tool case has inline comment explaining behavior
- Examples provided for complex tools

**Estimated Time**: 20 minutes

---

### T025: Create MCP Tool Handler Unit Tests [P]
**Description**: Test each tool handler in isolation

**File to Create**: `tests/test_tools.py`

**Test Cases**:
- handle_tool_call with task_create (valid and invalid args)
- handle_tool_call with task_list (with filters)
- handle_tool_call with task_get (found and not found)
- handle_tool_call with task_update (partial updates)
- handle_tool_call with task_complete
- handle_tool_call with task_delete
- handle_tool_call with task_search
- handle_tool_call with task_stats
- handle_tool_call with unknown tool (raises ValueError)

**Acceptance Criteria**:
- All 8 tools tested
- Error cases covered
- Mock TaskService for unit testing

**Estimated Time**: 1 hour 30 minutes

**Phase 5 Checkpoint**: ✅ MCP protocol layer complete, all tools implemented

---

## Phase 6: FastAPI Application Integration

**Goal**: Create FastAPI app, implement MCP endpoints, integrate all layers

**Dependencies**: All previous phases

**Test Criteria**:
- Server starts with `uvicorn app.main:app --reload`
- HEAD / returns correct MCP protocol version header
- POST / handles initialize, tools/list, tools/call methods
- Mock authentication works correctly
- Health check endpoint responds

### T026: Create FastAPI Application Structure
**Description**: Initialize FastAPI app with middleware and startup events

**File to Create**: `app/main.py`

**Implementation**:
```python
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
import json

from .config.settings import settings
from .db.database import get_db, init_db
from .services.task_service import TaskService
from .mcp.tools import TOOLS, handle_tool_call

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup():
    await init_db()

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "0.1.0"}
```

**Acceptance Criteria**:
- FastAPI app initialized
- CORS configured
- Database initializes on startup
- Health check responds

**Estimated Time**: 30 minutes

---

### T027: Implement MCP Protocol Discovery Endpoint
**Description**: Add HEAD / endpoint that returns MCP protocol version header

**Add to**: `app/main.py`

**Implementation**:
```python
from fastapi import Response

@app.head("/")
def mcp_discovery():
    """MCP protocol discovery endpoint"""
    return Response(
        headers={"MCP-Protocol-Version": "2025-06-18"}
    )
```

**Acceptance Criteria**:
- HEAD / returns 200 status
- Response includes MCP-Protocol-Version header with value "2025-06-18"

**Estimated Time**: 10 minutes

---

### T028: Implement MCP Initialize Method Handler
**Description**: Handle MCP initialize method in POST / endpoint

**Add to**: `app/main.py`

**Implementation**:
```python
@app.post("/")
async def mcp_handler(request: Request, db: AsyncSession = Depends(get_db)):
    """MCP message handler"""
    body = await request.json()
    method = body.get("method")

    # Mock authentication for Phase 1
    # TODO: Replace with OAuth 2.1 in Phase 2
    user_id = "dev-user"

    if method == "initialize":
        return {
            "protocolVersion": "2025-06-18",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": settings.APP_NAME,
                "version": "0.1.0"
            }
        }
```

**Acceptance Criteria**:
- initialize method returns correct protocol version
- capabilities and serverInfo included
- Mock user_id set to "dev-user"

**Estimated Time**: 20 minutes

---

### T029: Implement MCP tools/list Method Handler
**Description**: Return list of all 8 tools when tools/list method called

**Add to**: `app/main.py`

**Implementation**:
```python
elif method == "tools/list":
    return {"tools": TOOLS}
```

**Acceptance Criteria**:
- tools/list returns TOOLS array
- All 8 tools included in response

**Estimated Time**: 5 minutes

---

### T030: Implement MCP tools/call Method Handler
**Description**: Execute tool calls and format responses per MCP spec

**Add to**: `app/main.py`

**Implementation**:
```python
elif method == "tools/call":
    tool_name = body["params"]["name"]
    arguments = body["params"].get("arguments", {})

    try:
        task_service = TaskService(db, user_id)
        result = await handle_tool_call(tool_name, arguments, task_service)

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2, default=str)
                }
            ]
        }
    except Exception as e:
        return {
            "isError": True,
            "content": [
                {
                    "type": "text",
                    "text": str(e)
                }
            ]
        }

else:
    return {"error": f"Unknown method: {method}"}
```

**Acceptance Criteria**:
- tools/call executes tool handlers
- Success responses use MCP content array format
- Errors use isError flag and content array
- datetime objects serialized correctly (default=str)

**Estimated Time**: 30 minutes

**Phase 6 Checkpoint**: ✅ FastAPI app complete, MCP endpoints integrated

---

## Phase 7: Comprehensive Testing Suite

**Goal**: Implement unit, integration, and E2E tests to achieve ≥80% coverage

**Dependencies**: All implementation phases

**Test Criteria**:
- All tests pass
- Coverage ≥80% (measured with pytest --cov)
- Manual test script verifies functionality
- Type checking passes (mypy --strict)

### T031: Write TaskService Unit Tests - Create and Get [P]
**Description**: Test create_task and get_task methods

**File to Create**: `tests/test_task_service.py`

**Test Cases**:
- `test_create_task_with_valid_data`: Creates task successfully
- `test_create_task_sets_user_id`: Verifies user_id assignment
- `test_create_task_with_defaults`: Tests default values
- `test_get_task_existing`: Retrieves existing task
- `test_get_task_not_found`: Returns None for non-existent task
- `test_get_task_wrong_user`: Returns None for task owned by different user

**Acceptance Criteria**:
- Uses test_db fixture
- Tests user isolation
- Covers happy path and edge cases

**Estimated Time**: 45 minutes

---

### T032: Write TaskService Unit Tests - List and Filters [P]
**Description**: Test list_tasks with various filters

**Add to**: `tests/test_task_service.py`

**Test Cases**:
- `test_list_tasks_all`: Lists all user's tasks
- `test_list_tasks_filter_project`: Filters by project correctly
- `test_list_tasks_filter_priority`: Filters by priority
- `test_list_tasks_exclude_completed`: Excludes completed tasks by default
- `test_list_tasks_include_completed`: Includes completed when requested
- `test_list_tasks_pagination`: Tests limit and offset
- `test_list_tasks_sorting`: Verifies priority desc, created_at asc order

**Acceptance Criteria**:
- All filter combinations tested
- User isolation verified
- Sorting validated

**Estimated Time**: 1 hour

---

### T033: Write TaskService Unit Tests - Update, Complete, Delete [P]
**Description**: Test task modification methods

**Add to**: `tests/test_task_service.py`

**Test Cases**:
- `test_update_task_partial`: Updates only specified fields
- `test_update_task_not_found`: Returns None for non-existent task
- `test_update_task_wrong_user`: Returns None for task owned by different user
- `test_complete_task_sets_flags`: Sets completed and completed_at
- `test_complete_task_not_found`: Returns None for non-existent task
- `test_delete_task_success`: Deletes task and returns True
- `test_delete_task_not_found`: Returns False for non-existent task

**Acceptance Criteria**:
- User isolation enforced
- Edge cases covered
- Timestamps validated

**Estimated Time**: 1 hour

---

### T034: Write TaskService Unit Tests - Search and Stats [P]
**Description**: Test search_tasks and get_stats methods

**Add to**: `tests/test_task_service.py`

**Test Cases**:
- `test_search_tasks_title`: Searches in title field
- `test_search_tasks_notes`: Searches in notes field
- `test_search_tasks_both`: Searches both fields
- `test_search_tasks_case_insensitive`: Verifies case-insensitive search
- `test_get_stats_totals`: Calculates total and completed counts
- `test_get_stats_by_project`: Groups by project correctly
- `test_get_stats_by_priority`: Groups by priority correctly
- `test_get_stats_empty_database`: Handles empty database gracefully

**Acceptance Criteria**:
- Search functionality tested thoroughly
- Statistics calculations validated
- Edge cases covered

**Estimated Time**: 1 hour

---

### T035: Write MCP Protocol Integration Tests [P]
**Description**: Test MCP endpoints for protocol compliance

**File to Create**: `tests/test_mcp_protocol.py`

**Test Cases**:
- `test_protocol_discovery`: HEAD / returns MCP-Protocol-Version header
- `test_initialize_method`: Returns protocol version and capabilities
- `test_tools_list_method`: Returns all 8 tools with schemas
- `test_tools_call_task_create`: Creates task via MCP
- `test_tools_call_task_list`: Lists tasks via MCP
- `test_tools_call_error_handling`: Returns isError for failures
- `test_response_format_compliance`: Validates MCP response format

**Acceptance Criteria**:
- Uses FastAPI TestClient
- All MCP methods tested
- Response format validated

**Estimated Time**: 1 hour 15 minutes

---

### T036: Write Tool Handler Integration Tests [P]
**Description**: Test each of the 8 tools end-to-end

**File to Create**: `tests/test_mcp_tools.py`

**Test Cases**:
- `test_tool_task_create`: Full create workflow
- `test_tool_task_list`: List with filters
- `test_tool_task_get`: Get specific task
- `test_tool_task_update`: Update task fields
- `test_tool_task_complete`: Mark task complete
- `test_tool_task_delete`: Delete task
- `test_tool_task_search`: Search by keywords
- `test_tool_task_stats`: Get statistics
- `test_tool_unknown`: Error for unknown tool

**Acceptance Criteria**:
- All 8 tools tested via tools/call
- Success and error cases covered
- Response format validated

**Estimated Time**: 1 hour 30 minutes

---

### T037: Create Manual Test Script
**Description**: Python script for manual API testing and verification

**File to Create**: `scripts/test_local.py`

**Implementation**:
```python
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")

def test_initialize():
    print("\nTesting initialize...")
    response = requests.post(BASE_URL, json={"method": "initialize"})
    print(f"  Response: {json.dumps(response.json(), indent=2)}")

def test_tools_list():
    print("\nTesting tools/list...")
    response = requests.post(BASE_URL, json={"method": "tools/list"})
    tools = response.json()["tools"]
    print(f"  Found {len(tools)} tools:")
    for tool in tools:
        print(f"    - {tool['name']}: {tool['description']}")

def test_create_task():
    print("\nTesting task_create...")
    response = requests.post(BASE_URL, json={
        "method": "tools/call",
        "params": {
            "name": "task_create",
            "arguments": {
                "title": "Test task from script",
                "project": "Testing",
                "priority": 4
            }
        }
    })
    print(f"  Response: {json.dumps(response.json(), indent=2)}")

def test_list_tasks():
    print("\nTesting task_list...")
    response = requests.post(BASE_URL, json={
        "method": "tools/call",
        "params": {
            "name": "task_list",
            "arguments": {}
        }
    })
    print(f"  Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    print("=" * 60)
    print("Task Manager MCP Server - Manual Test Script")
    print("=" * 60)
    test_health()
    test_initialize()
    test_tools_list()
    test_create_task()
    test_list_tasks()
    print("\n" + "=" * 60)
    print("Manual testing complete!")
    print("=" * 60)
```

**Acceptance Criteria**:
- Tests all major functionality
- Clear output for verification
- Runs against local server

**Estimated Time**: 45 minutes

---

### T038: Run Coverage Analysis and Fill Gaps [P]
**Description**: Measure coverage and add tests for uncovered lines

**Commands**:
```bash
pytest --cov=app --cov-report=html --cov-report=term-missing
open htmlcov/index.html  # Review coverage report
```

**Tasks**:
- Identify uncovered branches
- Add tests for error conditions
- Test edge cases
- Achieve ≥80% coverage

**Acceptance Criteria**:
- `pytest --cov=app --cov-fail-under=80` passes
- All critical paths covered
- Edge cases tested

**Estimated Time**: 1 hour

---

### T039: Run Type Checking and Fix Issues
**Description**: Ensure 100% type hint coverage with mypy --strict

**Commands**:
```bash
mypy app/ --strict
```

**Tasks**:
- Add missing type hints
- Fix any type errors
- Add type ignores with justification only where necessary
- Ensure all functions have return type annotations

**Acceptance Criteria**:
- `mypy app/ --strict` passes with no errors
- All public functions have complete type annotations
- Type ignores documented with reasons

**Estimated Time**: 1 hour

---

### T040: Run Linting and Code Formatting
**Description**: Ensure code follows style guidelines

**Commands**:
```bash
ruff check app/ tests/
black app/ tests/
```

**Tasks**:
- Fix any ruff linting errors
- Format all code with black
- Fix import ordering
- Remove unused imports

**Acceptance Criteria**:
- `ruff check app/ tests/` passes with no errors
- `black --check app/ tests/` shows all files formatted
- Code follows PEP 8 style guide

**Estimated Time**: 30 minutes

---

### T041: Run Security Scan [P]
**Description**: Check for security vulnerabilities with bandit

**Commands**:
```bash
bandit -r app/ -ll  # Low and high severity only
```

**Tasks**:
- Review bandit output
- Fix any high or medium severity issues
- Document why any issues are false positives

**Acceptance Criteria**:
- No high severity issues
- Medium issues reviewed and justified
- No hardcoded credentials found

**Estimated Time**: 30 minutes

---

### T042: Execute All Tests and Verify Quality Gates
**Description**: Run complete test suite and verify all quality standards met

**Commands**:
```bash
pytest --cov=app --cov-fail-under=80 -v
mypy app/ --strict
ruff check app/ tests/
black --check app/ tests/
bandit -r app/ -ll
```

**Acceptance Criteria**:
- All tests pass
- Coverage ≥80%
- Type checking passes
- Linting passes
- Security scan passes
- Manual test script works

**Estimated Time**: 30 minutes

**Phase 7 Checkpoint**: ✅ Testing complete, quality gates met

---

## Phase 8: Documentation & Polish

**Goal**: Add docstrings, verify documentation accuracy, final review

**Dependencies**: All implementation complete

**Test Criteria**:
- All public functions have docstrings
- README.md Quick Start section accurate
- Code passes final review

### T043: Add Docstrings and Final Documentation Review
**Description**: Complete docstrings for all public functions and verify docs

**Tasks**:
1. Add Google-style docstrings to all TaskService methods (Args, Returns, Raises)
2. Add docstrings to MCP tool handlers
3. Add docstrings to database functions
4. Verify README.md Quick Start instructions
5. Verify SETUP_GUIDE.md Phase 1 section
6. Create deployment checklist in `.specswarm/features/001-.../checklists/deployment.md`

**Docstring Format**:
```python
def method_name(arg1: Type1, arg2: Type2) -> ReturnType:
    """Brief description of method

    More detailed description if needed.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2

    Returns:
        Description of return value

    Raises:
        ValueError: When and why this is raised
    """
```

**Acceptance Criteria**:
- All public methods have complete docstrings
- Documentation matches implementation
- Deployment checklist created
- README Quick Start verified

**Estimated Time**: 2 hours

**Phase 8 Checkpoint**: ✅ **PHASE 1 COMPLETE** - All tasks finished, ready for deployment

---

## Task Dependencies

### Critical Path (Must Complete Sequentially)

```
T001-T004 (Setup) → T005-T007 (Database) → T008-T009 (Schemas) →
T010-T017 (Services) → T018-T025 (MCP) → T026-T030 (FastAPI) →
T031-T042 (Testing) → T043 (Docs)
```

### Parallel Opportunities

**Within Phase 1** (after T001 completes):
- [P] T002, T003, T004 can run concurrently (different files)

**Within Phase 3**:
- [P] T009 (schema tests) can start immediately after T008

**Within Phase 5**:
- [P] T023 (type hints), T024 (docstrings), T025 (tests) can run concurrently after T018-T022

**Within Phase 7** (all test writing):
- [P] T031-T036, T037, T039, T041 can all run in parallel (different test files)

**Example Parallel Execution**:
```
Sequential:  T001 → [T002, T003, T004] → T005 → T006 → T007 → T008 → [T009] → ...
Timeline:    15min    65min total        45min   1h      1h15   45min   30min
```

---

## Implementation Strategy

### MVP First Approach

**Minimum Viable Product** (First Deliverable):
- Phases 1-6: Core functionality (T001-T030)
- Basic manual testing
- Demonstrates MCP protocol working

**Then Add**:
- Phase 7: Comprehensive testing (T031-T042)
- Phase 8: Polish and documentation (T043)

### Incremental Testing

- Test each phase before moving to next
- Phase 1: Settings load correctly
- Phase 2: Database tables created
- Phase 3: Schemas validate
- Phase 4: Service methods work
- Phase 5: Tools route correctly
- Phase 6: Server responds to MCP calls

### Quality Checkpoints

After each phase:
- Run relevant tests
- Check type hints
- Verify functionality works

Final checkpoint (all phases):
- All 42 tests pass
- Coverage ≥80%
- Type checking passes
- Manual script works

---

## Execution Notes

### Time Estimates

- **Setup & Config** (Phase 1): 2 hours
- **Database Layer** (Phase 2): 3 hours
- **Data Validation** (Phase 3): 1 hour
- **Business Logic** (Phase 4): 4 hours
- **MCP Protocol** (Phase 5): 4 hours
- **FastAPI Integration** (Phase 6): 3 hours
- **Testing Suite** (Phase 7): 5 hours
- **Documentation** (Phase 8): 2 hours

**Total**: 24 hours (3 days of 8-hour work)

### Success Metrics

All Phase 1 success criteria from spec.md must be met:
- ✅ MCP server responds to Claude Code
- ✅ All 8 tools discoverable and callable
- ✅ Tasks persist in SQLite across restarts
- ✅ User isolation enforced
- ✅ Search and filtering work
- ✅ Performance benchmarks met (<500ms tool calls)
- ✅ Test coverage ≥80%
- ✅ Type hint coverage 100%

### Next Steps After Completion

1. Manual verification with Claude Code
2. Code review against constitution
3. Run `/specswarm:analyze-quality`
4. Address any quality issues
5. Run `/specswarm:ship` to merge
6. Tag release: v0.1.0-phase1
7. Begin Phase 2 planning (OAuth 2.1)

---

## Appendix

### Task Summary by File

**Configuration**: T001-T004 (4 tasks)
**Database**: T005-T007 (3 tasks)
**Schemas**: T008-T009 (2 tasks)
**Services**: T010-T017 (8 tasks)
**MCP**: T018-T025 (8 tasks)
**FastAPI**: T026-T030 (5 tasks)
**Testing**: T031-T042 (12 tasks)
**Documentation**: T043 (1 task)

**Total**: 43 tasks

### File Creation Order

1. Project structure (T001)
2. requirements.txt, .gitignore (T002)
3. app/config/settings.py (T003)
4. pyproject.toml, pytest.ini (T004)
5. app/db/models.py (T005)
6. app/db/database.py (T006)
7. tests/conftest.py (T007)
8. app/schemas/task.py (T008)
9. tests/test_schemas.py (T009)
10. app/services/task_service.py (T010-T017)
11. app/mcp/tools.py (T018-T024)
12. tests/test_tools.py (T025)
13. app/main.py (T026-T030)
14. tests/test_task_service.py (T031-T034)
15. tests/test_mcp_protocol.py (T035)
16. tests/test_mcp_tools.py (T036)
17. scripts/test_local.py (T037)
18. Coverage/quality analysis (T038-T042)
19. Documentation (T043)

### Technologies Used

All approved in `.specswarm/tech-stack.md`:
- Python 3.11+
- FastAPI + Uvicorn
- MCP Python SDK 0.9.0+
- SQLAlchemy 2.0+ (async)
- SQLite 3.x
- Pydantic 2.5.0+
- pytest + pytest-asyncio
- mypy, ruff, black

**Compliance**: ✅ 100% approved, no violations
