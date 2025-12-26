---
parent_branch: main
feature_number: 001
status: In Progress
created_at: 2025-12-25T19:45:00-07:00
---

# Feature: Phase 1 Local Development with SQLite and Basic MCP Tools

## Overview

Implement the foundational infrastructure for the Task Manager MCP Server to enable local development and testing. This phase establishes the core architecture with a working MCP server that can be tested from Claude Code using stdio connection, providing basic task management capabilities through conversational interaction.

**Purpose**: Create a functional prototype that validates the MCP protocol integration, database operations, and business logic patterns before adding authentication and cloud deployment complexity.

**Value**: Enables rapid iteration on core features with immediate feedback, establishes architectural patterns that will scale through later phases, and provides a testable foundation for the complete system.

## User Scenarios

### Scenario 1: Developer Testing MCP Integration

**Actor**: Backend developer working on MCP server implementation

**Goal**: Verify that the MCP server correctly implements the protocol and can be accessed from Claude Code

**Flow**:
1. Developer starts the server locally using uvicorn
2. Developer configures Claude Code to connect via stdio
3. Developer asks Claude to "list my MCP tools"
4. Claude displays all 8 available task management tools
5. Developer creates a test task by telling Claude "Create a task to test the MCP server"
6. Claude confirms task creation with task details
7. Developer asks Claude to "show me all my tasks"
8. Claude lists the newly created task with all properties
9. Developer verifies task appears in SQLite database using database viewer

**Success Indicators**:
- MCP protocol handshake completes successfully
- All 8 tools are discoverable and callable
- Task data persists correctly in database
- Response times meet acceptable thresholds (<500ms for tool calls)

### Scenario 2: Conversational Task Management

**Actor**: Developer using Claude Code to manage development tasks

**Goal**: Manage project tasks through natural conversation without leaving the development environment

**Flow**:
1. Developer tells Claude "I need to implement user authentication and write unit tests"
2. Claude creates two tasks with appropriate priorities and time estimates
3. Developer asks "What should I work on now? I have about an hour"
4. Claude suggests tasks based on available time and priorities
5. Developer completes authentication work and tells Claude "Mark authentication task as complete"
6. Claude updates task status and shows completion confirmation
7. Developer asks "What's left on my list?"
8. Claude shows remaining incomplete tasks
9. Developer searches by telling Claude "Find tasks about testing"
10. Claude returns all tasks matching "testing" keywords

**Success Indicators**:
- Natural language interactions successfully translate to MCP tool calls
- Task suggestions are contextually appropriate
- Status updates persist across conversations
- Search functionality returns relevant results

### Scenario 3: Project Organization and Filtering

**Actor**: Instructor managing multiple teaching responsibilities

**Goal**: Organize tasks by project and view filtered lists for specific contexts

**Flow**:
1. Instructor creates tasks for different projects: "Deep Dive Coding", "Custom Cult", "Personal"
2. Instructor asks Claude "Show me my Custom Cult tasks"
3. Claude filters and displays only Custom Cult project tasks
4. Instructor asks "What are my high priority teaching tasks?"
5. Claude filters by both project (Deep Dive Coding) and priority (High/Critical)
6. Instructor reviews task list and updates priorities as needed
7. Instructor asks "Show me task statistics"
8. Claude displays counts by project and priority, plus completion rate

**Success Indicators**:
- Project-based filtering works accurately
- Combined filters (project + priority) function correctly
- Task statistics provide meaningful insights
- Multiple simultaneous filters can be applied

## Functional Requirements

### FR1: MCP Protocol Implementation

**Requirement**: Server must implement MCP Specification 2025-06-18 with all required endpoints and methods

**Details**:
- Implement HEAD / endpoint for protocol discovery (returns MCP-Protocol-Version header)
- Implement POST / endpoint for all MCP methods (initialize, tools/list, tools/call)
- Support initialize method that returns protocol version, capabilities, and server info
- Support tools/list method that returns all 8 tool definitions with complete schemas
- Support tools/call method that executes tool handlers and returns formatted responses
- Use correct MCP error codes for failures (-32600, -32601, -32602, -32603)
- Format all responses according to MCP spec (content array with type and text fields)

**Acceptance Criteria**:
- MCP protocol handshake completes successfully from Claude Code
- All 8 tools appear in Claude's tool list
- Tool calls execute without protocol errors
- Error responses use correct MCP error codes
- Response format validates against MCP spec

### FR2: Database Layer with SQLAlchemy

**Requirement**: Establish database infrastructure using SQLAlchemy 2.0+ ORM with SQLite for local development

**Details**:
- Create Task model with all fields from PROJECT_SPEC.md schema (id, user_id, title, project, priority, energy, time_estimate, notes, due_date, completed, completed_at, created_at, updated_at)
- Create User model for future OAuth integration (user_id, email, preferences, created_at)
- Implement database initialization function (init_db) that creates tables on startup
- Configure async database operations using SQLAlchemy 2.0+ async session
- Create database connection dependency for FastAPI (get_db)
- Use SQLite file storage (tasks.db) for persistence

**Acceptance Criteria**:
- Database tables created automatically on first run
- Task model supports all required fields with correct types
- Database operations are asynchronous (non-blocking)
- Connection pooling configured appropriately for SQLite
- Database file persists across server restarts

### FR3: Task CRUD Operations

**Requirement**: Implement complete Create, Read, Update, Delete operations for tasks through TaskService

**Details**:
- **Create**: Accept TaskCreate schema, validate inputs, assign user_id, persist to database, return created task
- **Get**: Retrieve single task by ID, filter by user_id for isolation, return Task schema or None
- **List**: Query tasks with optional filters (project, priority, completed status), support pagination (limit/offset), default sort by priority desc then created_at, filter by user_id
- **Update**: Accept task_id and TaskUpdate schema with partial updates, validate ownership, apply changes, return updated task
- **Complete**: Mark task as completed, set completed_at timestamp, persist changes
- **Delete**: Remove task from database (hard delete for Phase 1), validate ownership

**Acceptance Criteria**:
- All CRUD operations work correctly through MCP tools
- Created tasks persist and are retrievable
- Updates modify only specified fields
- Deletes remove tasks from database
- All operations enforce user isolation (filter by user_id)

### FR4: Eight MCP Tools

**Requirement**: Expose 8 MCP tools for task management as defined in PROJECT_SPEC.md

**Tool Definitions**:

1. **task_create**
   - Parameters: title (required), project, priority (1-5), energy (light/medium/deep), time_estimate, notes, due_date
   - Returns: Created task object with all fields
   - Validation: Title 1-500 chars, priority 1-5, energy enum

2. **task_list**
   - Parameters: project, priority, show_completed (default false), limit (default 100), offset (default 0)
   - Returns: Array of task objects matching filters
   - Behavior: Sorts by priority desc, created_at asc

3. **task_get**
   - Parameters: task_id (required)
   - Returns: Single task object or error if not found

4. **task_update**
   - Parameters: task_id (required), any task fields to update
   - Returns: Updated task object
   - Behavior: Partial updates (only specified fields change)

5. **task_complete**
   - Parameters: task_id (required)
   - Returns: Updated task object with completed=true and completed_at timestamp

6. **task_delete**
   - Parameters: task_id (required)
   - Returns: Success confirmation with task_id

7. **task_search**
   - Parameters: query (required), fields (default both title and notes)
   - Returns: Array of tasks matching search query

8. **task_stats**
   - Parameters: group_by (project, priority, or status)
   - Returns: Analytics object with counts and percentages

**Acceptance Criteria**:
- All 8 tools registered in MCP server
- Tool schemas validate inputs correctly
- Tools execute business logic through TaskService
- Response format matches MCP specification
- Error handling provides helpful messages

### FR5: Configuration and Environment Management

**Requirement**: Support environment-based configuration using .env files and Pydantic settings

**Details**:
- Create Settings class using pydantic-settings BaseSettings
- Load configuration from .env file (never commit to git)
- Provide .env.example template with documentation
- Support these configuration options:
  - APP_NAME (default "Task Manager MCP")
  - DEBUG (default false)
  - LOG_LEVEL (default INFO)
  - DATABASE_URL (default sqlite:///./tasks.db)
  - SECRET_KEY (required, generate random for dev)
  - HOST (default 0.0.0.0)
  - PORT (default 8000)
- Export settings as singleton (from app.config.settings import settings)

**Acceptance Criteria**:
- Settings load from .env file correctly
- Missing .env file uses defaults where appropriate
- Required settings (SECRET_KEY) cause startup failure if missing
- Settings accessible throughout application
- .env.example exists and documents all options

### FR6: Mock Authentication

**Requirement**: Use mock user_id ("dev-user") for Phase 1 to enable testing without OAuth complexity

**Details**:
- Hardcode user_id = "dev-user" in MCP handler
- All database queries filter by this user_id
- Document this as temporary Phase 1 shortcut
- Add TODO comment for Phase 2 OAuth replacement
- Ensure user isolation patterns are correct (ready for real auth)

**Acceptance Criteria**:
- All tasks created with user_id = "dev-user"
- Database queries filter by user_id correctly
- Code comment indicates Phase 2 replacement needed
- User isolation logic is sound (no cross-user data access possible)

### FR7: Testing Infrastructure

**Requirement**: Establish pytest-based testing framework with fixtures for database and MCP protocol testing

**Details**:
- Configure pytest with pytest-asyncio for async test support
- Create test database fixture (separate from development database)
- Create test fixtures for common scenarios (create task, sample tasks, etc.)
- Write unit tests for TaskService methods (minimum 80% coverage)
- Write integration tests for MCP protocol compliance
- Create test script for manual API testing (scripts/test_local.py)
- Configure pytest.ini or pyproject.toml with test settings

**Acceptance Criteria**:
- pytest runs and discovers all tests
- Test coverage meets 80% minimum requirement
- Async tests execute correctly
- Test database isolated from development database
- Tests clean up after themselves (no persistent state)

### FR8: Local Development Setup

**Requirement**: Provide streamlined local development experience with clear setup instructions

**Details**:
- Document complete setup process in SETUP_GUIDE.md (already exists, reference it)
- Create requirements.txt with all dependencies pinned to specific versions
- Support virtual environment workflow (venv)
- Enable hot-reload development mode (uvicorn --reload)
- Provide test script for manual verification (scripts/test_local.py)
- Create .gitignore to exclude generated files (*.pyc, __pycache__, .env, *.db, venv)

**Acceptance Criteria**:
- Developer can set up from scratch in under 10 minutes
- All dependencies install without conflicts
- Hot-reload works (code changes apply without restart)
- Test script verifies basic functionality
- No generated files committed to git

## Success Criteria

### SC1: MCP Protocol Compliance
- Server successfully completes MCP handshake with Claude Code
- All 8 tools appear in Claude's tool discovery
- Tool calls execute and return valid MCP-formatted responses
- Error conditions return proper MCP error codes
- Protocol version header (2025-06-18) correctly advertised

### SC2: Task Management Functionality
- Users can create tasks through conversation with Claude
- Users can list tasks with various filters (project, priority, completion status)
- Users can update task properties without data loss
- Users can mark tasks complete with automatic timestamp
- Users can delete tasks permanently
- Users can search tasks by keywords in title or notes
- Users can view task statistics grouped by project, priority, or status

### SC3: Data Persistence and Isolation
- Tasks persist across server restarts (SQLite file storage)
- All tasks correctly associated with user_id "dev-user"
- Database queries properly filter by user_id (no data leakage)
- Database indexes support efficient queries
- Task counts and statistics accurate

### SC4: Performance Benchmarks
- MCP initialize call completes in under 200ms
- MCP tools/list call completes in under 100ms
- MCP tools/call for task_create completes in under 500ms
- MCP tools/call for task_list (100 items) completes in under 500ms
- Database query time for filtered list under 100ms (p95)

### SC5: Code Quality Standards
- Type hint coverage reaches 100% (mypy --strict passes)
- Test coverage reaches minimum 80%
- Linting passes without errors (ruff check, black --check)
- Security scan passes (bandit -r app/)
- No hardcoded credentials in code

### SC6: Developer Experience
- Complete setup process takes under 10 minutes for new developer
- Hot-reload enables rapid iteration (code changes visible in <3 seconds)
- Error messages are helpful and actionable
- Test script provides clear verification steps
- Documentation guides developer through all setup steps

### SC7: Production Readiness Foundations
- Layered architecture established (API, MCP, Service, Data layers)
- User isolation patterns implemented correctly
- Configuration externalized (environment variables)
- Logging configured with appropriate levels
- Error handling comprehensive

## Key Entities

### Task
- **Purpose**: Represents a single item to be completed
- **Lifecycle**: Created → (Updated*) → Completed or Deleted
- **Key Attributes**:
  - Identity: id (unique), user_id (owner)
  - Content: title, notes
  - Organization: project (category)
  - Prioritization: priority (1-5), energy (light/medium/deep), time_estimate
  - Scheduling: due_date, created_at, updated_at
  - Status: completed (boolean), completed_at (timestamp)
- **Relationships**: Belongs to User (via user_id)

### User
- **Purpose**: Represents system user (prepared for Phase 2 OAuth)
- **Key Attributes**:
  - Identity: user_id (primary key)
  - Profile: email
  - Settings: preferences (JSON)
  - Audit: created_at
- **Relationships**: Has many Tasks
- **Phase 1 Note**: Single hardcoded user ("dev-user"), full implementation in Phase 2

## Technical Constraints

### Must Use Approved Technologies
- Python 3.11+ (modern type hints, performance improvements)
- FastAPI (async web framework)
- SQLAlchemy 2.0+ (async ORM, modern query style)
- MCP Python SDK 0.9.0+ (official protocol implementation)
- SQLite 3.x (development database)
- pytest + pytest-asyncio (testing framework)
- Uvicorn with standard extras (ASGI server)

### Must Follow Architecture Patterns
- Layered architecture per ARCHITECTURE.md (API → MCP → Service → Data)
- Async operations throughout (no blocking I/O)
- Dependency injection for database sessions
- Pydantic schemas for all data validation
- User isolation enforced at service layer
- No direct SQL queries (ORM only)

### Must Meet Quality Standards
- Type hints: 100% coverage (mypy --strict)
- Test coverage: ≥80% (pytest --cov)
- Linting: Pass ruff and black
- Security: Pass bandit scan
- No hardcoded secrets

## Assumptions

1. **Single User for Phase 1**: All tasks belong to hardcoded "dev-user", real authentication deferred to Phase 2
2. **SQLite Sufficient for Development**: File-based database adequate for local testing, PostgreSQL migration planned for Phase 3 production deployment
3. **No Calendar Integration Yet**: Calendar linking deferred to Phase 2 per PROJECT_SPEC.md roadmap
4. **Stdio Connection Only**: Phase 1 supports local Claude Code connection via stdio, HTTP+OAuth added in Phase 2
5. **Hard Delete Acceptable**: Permanent task deletion (no soft delete/archive) acceptable for Phase 1 simplicity
6. **No Subtasks or Dependencies**: Tasks are independent, no parent-child relationships in Phase 1
7. **English Only**: No internationalization, all text in English
8. **No Rate Limiting**: Local development doesn't require rate limiting, added in Phase 2/3
9. **Basic Error Handling**: Comprehensive error handling and recovery deferred to Phase 4
10. **Standard Task Fields**: Time estimates use string format (e.g., "1hr", "30min") without strict validation, can be refined based on Phase 1 usage patterns
11. **Default Sorting**: Tasks sorted by priority (descending) then creation date (ascending) unless specified otherwise
12. **Reasonable Pagination**: Default limit of 100 tasks per query, maximum 1000 to prevent performance issues
13. **Search is Case-Insensitive**: Keyword search ignores case for better user experience
14. **Priority Scale Interpretation**: 1=Someday, 2=Low, 3=Medium, 4=High, 5=Critical (per PROJECT_SPEC.md)
15. **Energy Levels Fixed**: Three levels (light, medium, deep) sufficient for Phase 1, no custom energy levels

## Dependencies

### Internal Dependencies
- Must reference existing documentation (PROJECT_SPEC.md, ARCHITECTURE.md, SETUP_GUIDE.md)
- Must comply with .specswarm/constitution.md principles
- Must use technologies from .specswarm/tech-stack.md
- Must meet quality standards from .specswarm/quality-standards.md

### External Dependencies
- Python 3.11+ installation
- pip package manager
- Git (for version control)
- Claude Code installation (for testing)
- SQLite (bundled with Python, no separate install)

### Future Phase Dependencies
- Phase 2 depends on Phase 1 completion (OAuth integration builds on working MCP server)
- Phase 3 depends on Phase 2 (Cloud deployment requires OAuth for security)
- Phase 4 depends on Phase 3 (Production polish requires deployed system)
- Phase 5 depends on Phase 4 (Dashboard requires stable production API)

## Risks and Mitigations

### Risk 1: MCP Spec Interpretation
**Risk**: Incorrect interpretation of MCP protocol specification could cause incompatibility with Claude clients
**Likelihood**: Medium
**Impact**: High (breaks primary use case)
**Mitigation**: Reference official MCP spec (2025-06-18), test with actual Claude Code client, validate response formats against spec examples

### Risk 2: SQLAlchemy Async Complexity
**Risk**: SQLAlchemy 2.0+ async patterns may be unfamiliar, leading to blocking operations or connection leaks
**Likelihood**: Medium
**Impact**: Medium (degrades performance)
**Mitigation**: Follow SETUP_GUIDE.md examples, use async session consistently, test with multiple concurrent requests

### Risk 3: Type Safety Coverage
**Risk**: Achieving 100% type hint coverage with mypy --strict may be challenging with third-party libraries
**Likelihood**: Low
**Impact**: Medium (quality gate failure)
**Mitigation**: Use type stubs for libraries (types-* packages), leverage Pydantic for runtime validation, configure mypy exceptions only where necessary

### Risk 4: Test Coverage Requirements
**Risk**: Reaching 80% test coverage may be time-consuming for first iteration
**Likelihood**: Low
**Impact**: Low (can iterate)
**Mitigation**: Focus on testing critical paths (TaskService methods, MCP protocol compliance), use fixtures to reduce test boilerplate, defer edge case testing to Phase 2

## Out of Scope

The following are explicitly NOT included in Phase 1:

- **Authentication and Authorization**: No OAuth 2.1, no real user management (hardcoded "dev-user")
- **HTTP Endpoints**: No REST API, only MCP protocol endpoints
- **Calendar Integration**: No Google Calendar linking
- **Cloud Deployment**: No Docker, no Cloud Run deployment
- **Production Monitoring**: No logging infrastructure, no metrics collection
- **Advanced Features**: No recurring tasks, no subtasks, no task dependencies, no task templates
- **Team Features**: No shared tasks, no collaboration, no permissions
- **Performance Optimization**: No caching, no read replicas, no connection pooling optimizations
- **Comprehensive Error Recovery**: Basic error handling only, detailed recovery in Phase 4
- **Email Notifications**: No email integration
- **Task Analytics**: No advanced analytics beyond basic counts/stats
- **File Attachments**: No file upload or storage
- **Time Tracking**: No actual time tracking (only estimates)
- **Natural Language Date Parsing**: Due dates must be ISO format, no "next Tuesday" parsing
- **UI/Dashboard**: No web interface (Phase 5)

## Notes

- This specification is based on existing PROJECT_SPEC.md, ARCHITECTURE.md, and SETUP_GUIDE.md documentation
- Implementation should follow the detailed code examples in SETUP_GUIDE.md
- Architecture must conform to patterns defined in ARCHITECTURE.md
- All development aligned with .specswarm/constitution.md principles
- Phase 1 is intentionally simplified to establish working foundation before adding OAuth, deployment, and production features
- Mock authentication ("dev-user") must be replaced in Phase 2 with real OAuth 2.1
- Success criteria for Phase 1 measured against local development environment, not production
