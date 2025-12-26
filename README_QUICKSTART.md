# Task Manager MCP Server - Quick Start Guide

**Phase 1: Local Development with SQLite**

This guide will help you get the Task Manager MCP Server running on your local machine in under 5 minutes.

## Prerequisites

- Python 3.11 or higher
- Virtual environment tool (venv)
- Git (optional)

## Quick Setup (5 minutes)

### 1. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialize Database

```bash
# Create tables and seed sample data
python scripts/init_db.py --seed
```

### 4. Start Server

```bash
# Run the MCP server
python scripts/run_server.py
```

The server will start on `http://localhost:8000`

## Verify Installation

### Test MCP Tools (Interactive)

```bash
python scripts/test_mcp_tools.py
```

Choose option 1 for automated testing or option 2 for interactive mode.

### Test via HTTP (curl)

```bash
# Get server info
curl http://localhost:8000/

# List available MCP tools
curl -X POST http://localhost:8000/mcp/tools/list

# Create a task
curl -X POST http://localhost:8000/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "task_create",
    "params": {
      "title": "Test Task",
      "priority": 4,
      "project": "Testing"
    }
  }'

# List tasks
curl -X POST http://localhost:8000/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "task_list",
    "params": {}
  }'
```

## Available MCP Tools

### 1. task_create
Create a new task with title, priority, project, and other details.

### 2. task_list
List tasks with optional filters (project, priority, completion status).

### 3. task_get
Get a specific task by ID.

### 4. task_update
Update an existing task (partial updates supported).

### 5. task_complete
Mark a task as complete.

### 6. task_delete
Permanently delete a task.

### 7. task_search
Search tasks by keywords in title or notes.

### 8. task_stats
Get task statistics (totals, completion rate, breakdowns).

## Project Structure

```
task-manager-mcp/
├── app/
│   ├── config/       # Settings and auth
│   ├── db/           # Database models and session
│   ├── mcp/          # MCP tools and handlers
│   ├── schemas/      # Pydantic validation schemas
│   ├── services/     # Business logic
│   └── main.py       # FastAPI application
├── scripts/
│   ├── init_db.py    # Database initialization
│   ├── run_server.py # Server runner
│   └── test_mcp_tools.py # Tool testing CLI
├── tests/            # Test suite (Phase 7)
├── .env              # Environment configuration
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

## Configuration

Edit `.env` file to customize settings:

```env
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite+aiosqlite:///./tasks.db
MOCK_USER_ID=dev-user
```

## Development Workflow

### 1. Make Code Changes

Edit files in the `app/` directory. The server will auto-reload in DEBUG mode.

### 2. Test Changes

```bash
# Option 1: Interactive testing
python scripts/test_mcp_tools.py

# Option 2: Unit tests (after Phase 7)
pytest

# Option 3: Manual HTTP requests
curl -X POST http://localhost:8000/mcp/tools/call ...
```

### 3. Reset Database (if needed)

```bash
python scripts/init_db.py --reset --seed
```

## Common Issues

### Database Locked Error
**Problem**: `database is locked` error when running multiple operations

**Solution**: SQLite doesn't support high concurrency. This is expected in development. Phase 3 will migrate to PostgreSQL.

### Module Not Found Error
**Problem**: `ModuleNotFoundError: No module named 'app'`

**Solution**: Make sure you're running scripts from the project root directory, or add project root to PYTHONPATH:

```bash
export PYTHONPATH=/path/to/task-manager-mcp:$PYTHONPATH
```

### Virtual Environment Not Activated
**Problem**: Dependencies not found or wrong Python version

**Solution**: Activate virtual environment:

```bash
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

## Next Steps

- **Phase 2**: Add OAuth 2.1 authentication (replace mock user)
- **Phase 3**: Migrate from SQLite to PostgreSQL
- **Phase 4**: Deploy to Google Cloud Run
- **Phase 5**: Add Google Calendar integration

## Documentation

- **Full Specification**: See `.specswarm/features/001-.../spec.md`
- **Architecture**: See `ARCHITECTURE.md`
- **Data Model**: See `.specswarm/features/001-.../data-model.md`
- **API Contracts**: See `.specswarm/features/001-.../contracts/mcp-protocol.md`

## Support

For issues or questions:
1. Check the specification documents in `.specswarm/features/001-../`
2. Review the implementation plan in `.specswarm/features/001-.../plan.md`
3. Run debug mode: `DEBUG=true python scripts/run_server.py`

## License

See LICENSE file for details.
