# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

**This is a specification-only repository**. It contains comprehensive planning documents but no implementation code yet. The project is designed to be built using SpecSwarm multi-agent orchestration.

## Documentation Structure

The repository contains four key planning documents that define the entire system:

1. **README.md** - Project overview, quick start guide, and general information
2. **PROJECT_SPEC.md** - Detailed technical specification including features, database schema, API design, and success criteria
3. **ARCHITECTURE.md** - System architecture, component breakdown, data flow, and deployment strategy
4. **SETUP_GUIDE.md** - Step-by-step implementation guide with complete code examples

## Intended Build Workflow

### Using SpecSwarm (Recommended)

This project is designed for SpecSwarm orchestration:

```bash
# Initialize SpecSwarm in this directory
specswarm init

# SpecSwarm will automatically:
# - Read all .md specification files
# - Create work breakdown from specs
# - Coordinate specialist agents
# - Build the complete system
```

### Manual Implementation

If building manually, follow the implementation order defined in SETUP_GUIDE.md:

**Phase 1: Local Development**
1. Create virtual environment: `python -m venv venv && source venv/bin/activate`
2. Install dependencies from SETUP_GUIDE.md Step 2
3. Set up environment variables (`.env`)
4. Implement database models (`app/db/models.py`, `app/db/database.py`)
5. Create configuration (`app/config/settings.py`)
6. Build Pydantic schemas (`app/schemas/task.py`)
7. Implement business logic (`app/services/task_service.py`)
8. Create MCP tools (`app/mcp/tools.py`)
9. Build FastAPI app (`app/main.py`)
10. Test locally with `scripts/test_local.py`

**Phase 2: HTTP + OAuth**
- Implement OAuth 2.1 with Dynamic Client Registration
- Add session management
- Implement calendar integration

**Phase 3: Cloud Deployment**
- Containerize with Docker
- Deploy to Google Cloud Run
- Configure OAuth callbacks

**Phase 4: Production Polish**
- Add comprehensive error handling
- Implement monitoring and logging
- Performance optimization

**Phase 5: Birds Eye Dashboard**
- Build React-based dashboard
- Implement analytics visualizations
- Create Kanban board view

## Project Structure (Planned)

```
task-manager-mcp/
├── app/
│   ├── main.py                 # FastAPI entry point
│   ├── api/                    # HTTP routes & middleware
│   ├── mcp/                    # MCP server implementation
│   ├── services/               # Business logic (TaskService, etc.)
│   ├── db/                     # SQLAlchemy models & database
│   ├── auth/                   # OAuth 2.1 implementation
│   ├── config/                 # Settings and configuration
│   └── schemas/                # Pydantic schemas
├── tests/                      # Test suite
└── scripts/                    # Utility scripts
```

## Key Technical Decisions

**MCP Protocol**: Specification version 2025-06-18 with OAuth 2.1 authentication

**Tech Stack**:
- FastAPI (async web framework)
- MCP Python SDK (official MCP library)
- SQLAlchemy ORM with SQLite (dev) / PostgreSQL (prod)
- Google OAuth 2.1 for authentication
- Google Cloud Run for deployment

**Database Schema**: See PROJECT_SPEC.md lines 103-149 for complete schema definitions including tasks, users, and analytics tables

**MCP Tools** (8 total):
- `task_create` - Create tasks with title, project, priority, energy level, time estimate
- `task_list` - List with filters (project, priority, completion status)
- `task_get` - Get specific task by ID
- `task_update` - Update any task fields
- `task_complete` - Mark as complete
- `task_delete` - Delete task
- `task_search` - Search by keywords
- `task_stats` - Analytics (counts by project, priority, completion rate)

## Development Commands (Post-Implementation)

### Local Development
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from app.db.database import init_db; init_db()"

# Run development server
uvicorn app.main:app --reload

# Run tests
pytest

# Test specific file
pytest tests/test_tasks.py

# Test with coverage
pytest --cov=app tests/
```

### Testing MCP Server
```bash
# Terminal 1: Run server
uvicorn app.main:app --reload

# Terminal 2: Test with script
python scripts/test_local.py
```

### Claude Code Integration
Add to `~/.claude/mcp_servers.json`:
```json
{
  "task-manager": {
    "command": "python",
    "args": ["-m", "uvicorn", "app.main:app", "--port", "8000"],
    "cwd": "/path/to/task-manager-mcp"
  }
}
```

### Deployment
```bash
# Build Docker image
docker build -t task-manager-mcp .

# Run container locally
docker run -p 8000:8000 --env-file .env task-manager-mcp

# Deploy to Cloud Run
gcloud run deploy task-manager-mcp \
  --image gcr.io/PROJECT_ID/task-manager-mcp \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Architecture Highlights

**Layered Architecture**:
1. API Layer (FastAPI) - HTTP handling, routing, middleware
2. MCP Layer - Protocol compliance, tool registration, method dispatch
3. Business Logic Layer - Task operations, validation, user context
4. Data Layer - SQLAlchemy ORM, database connections
5. Auth Layer - OAuth 2.1, token validation
6. Config Layer - Environment-based settings

**Data Flow** (Creating a Task):
```
User → Claude.ai → HTTP POST → FastAPI → Auth Middleware →
MCP Handler → TaskService → SQLAlchemy → Database → Response
```

**Authentication Flow**: OAuth 2.1 with Google, Dynamic Client Registration for mobile clients, token validation on every MCP tool call (except initialize)

## Important Implementation Notes

**Mock Authentication in Phase 1**: The SETUP_GUIDE shows `user_id = "dev-user"` as a placeholder in `app/main.py:539`. Replace this with proper OAuth token extraction in Phase 2.

**MCP Response Format**: Tool call responses must follow MCP spec format:
```python
{
  "content": [
    {"type": "text", "text": json.dumps(result, indent=2)}
  ]
}
```

**Error Handling**: Use MCP error codes (INVALID_REQUEST: -32600, METHOD_NOT_FOUND: -32601, etc.) and wrap errors in proper response format.

**Database Indexes**: Critical indexes defined in PROJECT_SPEC.md:122-126 for user_id, completed, priority, due_date, and project fields.

**User Isolation**: All database queries MUST filter by `user_id` to prevent data leakage between users.

## Security Requirements

- OAuth 2.1 authentication (no API keys)
- User data isolation enforced at service layer
- Parameterized SQL queries (SQLAlchemy ORM)
- Input validation via Pydantic schemas
- HTTPS only in production
- Rate limiting per user
- No task content in logs

## Testing Strategy

**Unit Tests**: Test service methods with mocked database
**Integration Tests**: Test MCP protocol compliance and OAuth flow
**E2E Tests**: Test complete workflows from Claude Code

## Reference Documentation

Read these files in order when implementing:
1. README.md - Understand the vision and use cases
2. PROJECT_SPEC.md - Learn exact requirements and constraints
3. ARCHITECTURE.md - Understand system design and data flow
4. SETUP_GUIDE.md - Follow step-by-step implementation

All specification documents are comprehensive and authoritative. When in doubt about implementation details, refer to these documents rather than making assumptions.
