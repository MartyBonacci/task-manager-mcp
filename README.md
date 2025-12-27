# Task Manager MCP Server

> A production-grade Model Context Protocol (MCP) server for conversational task management, accessible from Claude.ai, Claude mobile, and Claude Code.

## Overview

This project implements a full-featured task management system that works through natural conversation with Claude. Instead of clicking through a UI, you simply tell Claude what needs to be done, and Claude manages a persistent task database through MCP tools.

**Example Interaction:**
```
You: "I need to research sublimation options for Custom Cult and update my LinkedIn profile"
Claude: "Added two tasks:
  1. Research sublimation options (Custom Cult, High priority, 2hr)
  2. Update LinkedIn profile (Personal, Medium priority, 30min)"

You: "What should I work on now? I have about an hour free."
Claude: "You could tackle the LinkedIn update (30min, light energy) and still have time left, 
or start the sublimation research if you're feeling focused."
```

## Key Features

- ✅ **Conversational Interface** - Natural language task management through Claude
- ✅ **Cross-Platform** - Works on web, mobile, and terminal via MCP
- ✅ **Persistent Storage** - Tasks survive conversation boundaries
- ✅ **Smart Prioritization** - Priority, energy level, and time estimate tracking
- ✅ **Project Organization** - Categorize tasks by project
- ✅ **OAuth 2.1 Authentication** - Secure authentication with Dynamic Client Registration (RFC 7591)
- ✅ **Comprehensive Testing** - 81 tests with 66.93% code coverage
- 🚧 **Calendar Integration** - (Future) Schedule tasks as calendar events

## Documentation

This project includes comprehensive documentation for building from scratch:

### 📋 [PROJECT_SPEC.md](./PROJECT_SPEC.md)
Complete technical specification including:
- Feature requirements and scope
- MCP protocol compliance details
- Database schema and API design
- Security requirements
- Success criteria for each phase
- Timeline estimates

### 🏗️ [ARCHITECTURE.md](./ARCHITECTURE.md)
System architecture and design decisions:
- Component breakdown (API, MCP, Business Logic, Data layers)
- Data flow diagrams
- Authentication architecture
- Deployment strategy
- Performance considerations
- Project structure and file organization

### 🚀 [SETUP_GUIDE.md](./SETUP_GUIDE.md)
Step-by-step implementation guide:
- Prerequisites and dependencies
- Phase 1: Local development setup
- Complete code examples for all components
- Testing instructions
- Troubleshooting tips
- Next steps for OAuth and deployment

### ☁️ [DEPLOYMENT.md](./docs/DEPLOYMENT.md)
Google Cloud Run deployment guide:
- Prerequisites and GCP setup
- OAuth credential configuration
- Docker containerization
- Cloud Run deployment steps
- Post-deployment verification
- Monitoring and logging setup
- Troubleshooting and rollback procedures

### 📊 [PROJECT_STATUS.md](./docs/PROJECT_STATUS.md)
Current implementation status:
- Phase completion summary (Phases 1-2 complete)
- Test coverage analysis (66.93%)
- Critical fixes applied
- Production readiness checklist
- Lessons learned and next steps

### 🧪 [TEST_RESULTS.md](./docs/TEST_RESULTS.md)
Detailed test analysis:
- Test results by module (81 tests, 100% passing)
- Priority-based fix tracking
- Coverage report breakdown
- Known issues and workarounds

## Quick Start

### Prerequisites

- Python 3.11+
- Claude Code installed
- Google Cloud Platform account (for deployment)

### Installation

```bash
# Clone repository
git clone https://github.com/MartyBonacci/task-manager-mcp.git
cd task-manager-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python -c "from app.db.database import init_db; init_db()"

# Run server
uvicorn app.main:app --reload
```

### Test It

```bash
# Terminal 1: Server running (from above)

# Terminal 2: Test the API
python scripts/test_local.py
```

### Connect to Claude Code

Add to your `~/.claude/mcp_servers.json`:

```json
{
  "task-manager": {
    "command": "python",
    "args": ["-m", "uvicorn", "app.main:app", "--port", "8000"],
    "cwd": "/path/to/task-manager-mcp"
  }
}
```

Then in Claude Code:
```
"Show me my MCP tools"
"Create a task: Build amazing MCP server"
"List all my tasks"
```

## Testing

The project includes comprehensive test coverage (66.93% overall):

### Run All Tests
```bash
# Run complete test suite
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

# View coverage report in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Test Modules
- **test_mcp_handlers.py** - MCP tool unit tests (10/10 passing)
- **test_task_service.py** - Task service business logic (10/10 passing)
- **test_mcp_auth.py** - MCP authentication flow (9/9 passing)
- **test_oauth_integration.py** - OAuth 2.1 flow end-to-end (8/8 passing)
- **test_session_validation.py** - Session management (10/10 passing)
- **test_user_isolation.py** - User data isolation (8/8 passing)
- **test_dynamic_clients.py** - Dynamic client registration (18/18 passing)
- **test_regression_conftest_hang.py** - Database cleanup regression (3/3 passing)

### Known Issue
Full test suite may hang with pytest-asyncio event loop cleanup. Workaround: Run test modules individually or in smaller groups.

See [docs/TEST_RESULTS.md](./docs/TEST_RESULTS.md) for detailed test results and coverage analysis.

## Development Phases

### ✅ Phase 1: Local Development (COMPLETE)
- [x] Basic MCP server with stdio connection
- [x] SQLite database with SQLAlchemy ORM
- [x] All CRUD operations (8 MCP tools)
- [x] Testable from Claude Code locally
- [x] Comprehensive unit tests (10/10 passing)

### ✅ Phase 2: HTTP + OAuth (COMPLETE)
- [x] HTTP endpoints with FastAPI
- [x] OAuth 2.1 with Google authentication
- [x] Dynamic Client Registration (RFC 7591) for mobile/native apps
- [x] MCP Spec 2025-06-18 compliance
- [x] Session management with encrypted refresh tokens
- [x] Integration tests (8/8 OAuth flow tests passing)
- [x] Error scenario tests (23/23 passing)
- [x] Code coverage: 66.93% (1022/1360 statements)

### 🚧 Phase 3: Cloud Deployment (NEXT)
- [ ] Docker containerization
- [ ] Google Cloud Run deployment
- [ ] OAuth callback configuration
- [ ] Accessible from Claude.ai and mobile
- [ ] Production database (PostgreSQL)

### 🔮 Phase 4: Production Polish (FUTURE)
- [ ] Comprehensive error handling
- [ ] Monitoring and logging (structured logs)
- [ ] Performance optimization (caching, query optimization)
- [ ] Calendar integration
- [ ] Analytics dashboard

## Project Structure

```
task-manager-mcp/
├── README.md                    # This file
├── PROJECT_SPEC.md              # Technical specification
├── ARCHITECTURE.md              # System design
├── SETUP_GUIDE.md               # Implementation guide
├── requirements.txt
├── Dockerfile
├── .env.example
│
├── app/
│   ├── main.py                  # FastAPI app entry
│   ├── api/                     # HTTP routes & middleware
│   ├── mcp/                     # MCP server implementation
│   ├── services/                # Business logic
│   ├── db/                      # Database models & connection
│   ├── auth/                    # OAuth implementation
│   ├── config/                  # Configuration
│   └── schemas/                 # Pydantic schemas
│
├── tests/                       # Test suite
└── scripts/                     # Utility scripts
```

## MCP Tools

The server exposes the following MCP tools:

- **task_create** - Create a new task with title, project, priority, energy level, time estimate
- **task_list** - List tasks with optional filters (project, priority, completion status)
- **task_get** - Get a specific task by ID
- **task_update** - Update any task fields
- **task_complete** - Mark a task as complete
- **task_delete** - Delete a task
- **task_search** - Search tasks by keywords
- **task_stats** - Get analytics (counts by project, priority, completion rate)

## Tech Stack

- **Framework**: FastAPI (async Python web framework)
- **MCP SDK**: Official MCP Python SDK
- **Database**: SQLAlchemy ORM with SQLite (dev) / PostgreSQL (prod)
- **Auth**: OAuth 2.1 with google-auth
- **Deployment**: Google Cloud Run (serverless containers)
- **Testing**: pytest with async support

## Building with SpecSwarm

This project was designed to be built using [SpecSwarm](https://github.com/MartyBonacci/specswarm), a multi-agent development orchestrator.

### SpecSwarm Approach

**Main Agent** (Orchestra Conductor):
- Coordinates overall development
- Reads PROJECT_SPEC.md, ARCHITECTURE.md, SETUP_GUIDE.md
- Delegates to specialist agents
- Integrates components

**Specialist Agents**:
- **Database Agent**: Models, migrations, schema
- **API Agent**: FastAPI routes, middleware
- **MCP Agent**: Protocol compliance, tool handlers  
- **Auth Agent**: OAuth implementation
- **Testing Agent**: Unit and integration tests

### Initialize with SpecSwarm

```bash
# In project directory with all .md files present
specswarm init

# SpecSwarm will:
# 1. Read README.md (this file)
# 2. Discover PROJECT_SPEC.md, ARCHITECTURE.md, SETUP_GUIDE.md
# 3. Create work breakdown from specs
# 4. Coordinate specialist agents
# 5. Build the complete system
```

See [SpecSwarm documentation](https://github.com/MartyBonacci/specswarm) for more details.

## Security

- OAuth 2.1 authentication
- User data isolation (users can only access their own tasks)
- Input validation and sanitization
- Parameterized SQL queries (injection prevention)
- HTTPS only in production
- Rate limiting
- No task content in logs

## Contributing

Contributions welcome! Please:

1. Read the [PROJECT_SPEC.md](./PROJECT_SPEC.md) and [ARCHITECTURE.md](./ARCHITECTURE.md)
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Roadmap

**Phase 2 Features**:
- Calendar integration (schedule tasks as events)
- Natural language due date parsing
- Task templates
- Analytics dashboard

**Future Enhancements**:
- Recurring tasks
- Subtasks and dependencies
- Team/shared task lists
- Time tracking
- Mobile push notifications
- Third-party integrations (Slack, GitHub, etc.)

## Use Cases

**Personal Productivity**:
- Managing multiple business ventures
- Coordinating teaching prep with development work
- Tracking creative projects alongside technical work

**Development Projects**:
- Breaking down features into tasks
- Tracking bugs and technical debt
- Sprint planning and backlog management

**Content Creation**:
- Video production task lists
- Blog post ideas and outlines
- Social media content calendar

**Business Operations**:
- Customer follow-ups
- Vendor communications
- Inventory and supply management

## Author

**Marty Bonacci**
- Coding bootcamp instructor at Deep Dive Coding
- Technical Founder, Custom Cult Snowboards
- Creator of SpecSwarm and the Four Minds Pattern
- [LinkedIn](https://linkedin.com/in/martybonacci)
- [GitHub](https://github.com/MartyBonacci)

## License

MIT License - see LICENSE file for details

## Acknowledgments

Built with:
- [Anthropic's MCP](https://modelcontextprotocol.io/) - Model Context Protocol
- [Claude Code](https://code.claude.ai/) - AI-assisted development
- [SpecSwarm](https://github.com/MartyBonacci/specswarm) - Multi-agent orchestration
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework

## Support

For questions, issues, or feature requests:
- Open an issue on GitHub
- Reach out on LinkedIn
- Check the [SETUP_GUIDE.md](./SETUP_GUIDE.md) for troubleshooting

---

**Status**: ✅ Phase 2 Complete - OAuth 2.1 Authentication Implemented

**Test Coverage**: 66.93% (81 tests, all passing)

**Next Milestone**: Phase 3 - Docker containerization and Google Cloud Run deployment

**Last Updated**: December 26, 2025
