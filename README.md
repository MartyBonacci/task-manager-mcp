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
- ✅ **Production Ready** - OAuth 2.1, proper error handling, cloud deployment
- 🚧 **Calendar Integration** - (Phase 2) Schedule tasks as calendar events

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

## Development Phases

### ✅ Phase 1: Local Development (1-2 days)
- [x] Basic MCP server with stdio connection
- [x] SQLite database
- [x] All CRUD operations
- [x] Testable from Claude Code locally

### 🚧 Phase 2: HTTP + OAuth (1 day)
- [ ] HTTP endpoints
- [ ] OAuth 2.1 with Dynamic Client Registration
- [ ] MCP Spec 2025-06-18 compliance
- [ ] Session management

### 🔮 Phase 3: Cloud Deployment (1 day)
- [ ] Docker containerization
- [ ] Google Cloud Run deployment
- [ ] OAuth callback configuration
- [ ] Accessible from Claude.ai and mobile

### 🔮 Phase 4: Production Polish (ongoing)
- [ ] Comprehensive error handling
- [ ] Monitoring and logging
- [ ] Performance optimization
- [ ] Documentation updates

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

**Status**: 🚧 Phase 1 Development

**Next Milestone**: Complete local development and testing with Claude Code

**Last Updated**: December 25, 2025
