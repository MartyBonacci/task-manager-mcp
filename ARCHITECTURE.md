# Task Manager MCP Server - Architecture

## System Architecture

### High-Level Overview

```
┌─────────────────┐
│   Claude.ai     │
│  Claude Mobile  │  ←→  HTTPS + OAuth  ←→  ┌──────────────────┐
│  Claude Code    │                          │  MCP Server      │
└─────────────────┘                          │  (Cloud Run)     │
                                             │                  │
                                             │  ┌────────────┐  │
                                             │  │  FastAPI   │  │
                                             │  └────────────┘  │
                                             │  ┌────────────┐  │
                                             │  │    MCP     │  │
                                             │  │   Handler  │  │
                                             │  └────────────┘  │
                                             │  ┌────────────┐  │
                                             │  │  SQLAlch.  │  │
                                             │  │    ORM     │  │
                                             │  └────────────┘  │
                                             │  ┌────────────┐  │
                                             │  │  SQLite    │  │
                                             │  └────────────┘  │
                                             └──────────────────┘
```

## Component Architecture

### 1. API Layer (FastAPI)

**Responsibilities**:
- HTTP request handling
- OAuth token validation
- Session management
- Request routing
- Response formatting

**Key Files**:
- `main.py` - Application entry point
- `api/routes.py` - HTTP endpoints
- `api/middleware.py` - Auth, CORS, logging

**Endpoints**:
```python
HEAD /                    # Protocol discovery
POST /                    # MCP message handling
GET  /health             # Health check
GET  /.well-known/oauth  # OAuth discovery
POST /oauth/token        # Token exchange
POST /oauth/register     # Dynamic client registration
```

### 2. MCP Layer

**Responsibilities**:
- MCP protocol compliance
- Tool registration and discovery
- Method dispatch (initialize, tools/list, tools/call)
- Session state management
- Error handling per MCP spec

**Key Files**:
- `mcp/server.py` - MCP server implementation
- `mcp/tools.py` - Tool definitions and handlers
- `mcp/session.py` - Session management

**MCP Message Flow**:
```
Client Request → FastAPI → MCP Handler → Tool Handler → Database → Response
```

**Tool Structure**:
```python
class TaskTool:
    name: str
    description: str
    input_schema: dict
    handler: callable
```

### 3. Business Logic Layer

**Responsibilities**:
- Task operations (CRUD)
- Business rules enforcement
- Data validation
- User context management

**Key Files**:
- `services/task_service.py` - Task operations
- `services/user_service.py` - User management
- `services/analytics_service.py` - Stats and insights

**Service Pattern**:
```python
class TaskService:
    def __init__(self, db: Database, user_id: str):
        self.db = db
        self.user_id = user_id
    
    async def create_task(self, data: TaskCreate) -> Task:
        # Validate
        # Create
        # Return
```

### 4. Data Layer

**Responsibilities**:
- Database connection management
- ORM models
- Query execution
- Transaction management
- Data persistence

**Key Files**:
- `db/models.py` - SQLAlchemy models
- `db/database.py` - Database connection
- `db/migrations/` - Schema migrations (Alembic)

**Models**:
```python
class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    project = Column(String)
    priority = Column(Integer, default=3)
    energy = Column(String, default="medium")
    time_estimate = Column(String, default="1hr")
    notes = Column(Text)
    due_date = Column(DateTime)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True)
    email = Column(String)
    preferences = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 5. Authentication Layer

**Responsibilities**:
- OAuth 2.1 flows
- Token validation
- User identification
- Permission checking

**Key Files**:
- `auth/oauth.py` - OAuth implementation
- `auth/tokens.py` - JWT validation
- `auth/middleware.py` - Request authentication

**OAuth Flow**:
```
1. Claude initiates auth
2. User redirects to Google OAuth
3. User authorizes
4. Callback with auth code
5. Exchange for access token
6. Token stored by Claude
7. Subsequent requests include token
8. Server validates token
9. User identified from token
10. Request processed
```

### 6. Configuration Layer

**Responsibilities**:
- Environment-based configuration
- Secret management
- Feature flags
- Logging configuration

**Key Files**:
- `config/settings.py` - Application settings
- `.env` - Local environment variables
- `config/production.py` - Production overrides

**Configuration Structure**:
```python
class Settings:
    # App
    APP_NAME = "Task Manager MCP"
    DEBUG = False
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tasks.db")
    
    # OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI")
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
```

## Project Structure

```
task-manager-mcp/
├── README.md
├── requirements.txt
├── Dockerfile
├── .env.example
├── .gitignore
│
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py           # HTTP routes
│   │   └── middleware.py       # Auth, CORS, logging
│   │
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── server.py           # MCP server implementation
│   │   ├── tools.py            # Tool definitions
│   │   └── session.py          # Session management
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── task_service.py     # Task CRUD logic
│   │   ├── user_service.py     # User management
│   │   └── analytics_service.py # Stats and insights
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py           # SQLAlchemy models
│   │   ├── database.py         # DB connection
│   │   └── migrations/         # Alembic migrations
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── oauth.py            # OAuth implementation
│   │   ├── tokens.py           # Token validation
│   │   └── middleware.py       # Auth middleware
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py         # Configuration
│   │
│   └── schemas/
│       ├── __init__.py
│       ├── task.py             # Pydantic schemas
│       └── user.py
│
├── tests/
│   ├── __init__.py
│   ├── test_tasks.py
│   ├── test_mcp.py
│   └── test_auth.py
│
└── scripts/
    ├── setup_db.py
    ├── test_local.py
    └── deploy.sh
```

## Data Flow

### Creating a Task

```
1. User: "Add task: Research sublimation options"
2. Claude.ai sends HTTP POST to /
3. FastAPI receives request
4. Auth middleware validates OAuth token
5. Extracts user_id from token
6. Routes to MCP handler
7. MCP parses tool_call: task_create
8. Dispatches to TaskService.create_task()
9. TaskService validates input
10. Creates Task model instance
11. SQLAlchemy persists to database
12. Returns Task object
13. MCP formats response
14. FastAPI returns JSON
15. Claude receives result
16. Claude: "Added: Research sublimation options (Medium priority, 2hr estimate)"
```

### Listing Tasks

```
1. User: "What's on my task list?"
2. Claude.ai calls task_list tool
3. Server authenticates
4. TaskService.list_tasks(user_id)
5. Query: SELECT * FROM tasks WHERE user_id=? AND completed=0
6. Returns list of Task objects
7. Claude formats as natural language
8. Claude: "You have 3 tasks: 1) Research sublimation (High, 2hr)..."
```

## Security Architecture

### Authentication Flow

```
┌──────────┐                    ┌──────────┐                    ┌──────────┐
│  Claude  │                    │   MCP    │                    │  Google  │
│          │                    │  Server  │                    │  OAuth   │
└──────────┘                    └──────────┘                    └──────────┘
     │                               │                               │
     │ 1. Request auth               │                               │
     │ ───────────────────────────>  │                               │
     │                               │                               │
     │ 2. Return auth URL            │                               │
     │ <───────────────────────────  │                               │
     │                               │                               │
     │ 3. User clicks auth URL       │                               │
     │ ─────────────────────────────────────────────────────────────>│
     │                               │                               │
     │ 4. User authorizes            │                               │
     │ <─────────────────────────────────────────────────────────────│
     │                               │                               │
     │ 5. Callback with auth code    │                               │
     │ ───────────────────────────>  │                               │
     │                               │                               │
     │                               │ 6. Exchange code for token    │
     │                               │ ─────────────────────────────>│
     │                               │                               │
     │                               │ 7. Return access token        │
     │                               │ <─────────────────────────────│
     │                               │                               │
     │ 8. Return token to Claude     │                               │
     │ <───────────────────────────  │                               │
     │                               │                               │
     │ 9. Subsequent requests        │                               │
     │    with token in header       │                               │
     │ ───────────────────────────>  │                               │
     │                               │                               │
     │                               │ 10. Validate token            │
     │                               │ ─────────────────────────────>│
     │                               │                               │
     │                               │ 11. Token valid, user info    │
     │                               │ <─────────────────────────────│
     │                               │                               │
     │ 12. Process request           │                               │
     │ <───────────────────────────  │                               │
```

### Request Authentication

```python
async def authenticate_request(request: Request):
    # Extract Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise Unauthorized()
    
    # Parse bearer token
    token = auth_header.replace("Bearer ", "")
    
    # Validate with Google
    user_info = await validate_google_token(token)
    
    # Extract user_id
    user_id = user_info["sub"]
    
    # Attach to request
    request.state.user_id = user_id
    
    return user_id
```

## Deployment Architecture

### Local Development

```
SQLite file: ./tasks.db
Server: localhost:8000
Auth: Mock/bypass for testing
```

### Production (Cloud Run)

```
Container: task-manager-mcp:latest
Database: Cloud SQL PostgreSQL (or mounted volume for SQLite)
Environment: Production
Secrets: Google Secret Manager
Logs: Cloud Logging
Monitoring: Cloud Monitoring
```

### Environment Variables

```bash
# Required
DATABASE_URL=postgresql://user:pass@host/db
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx
SECRET_KEY=xxx

# Optional
DEBUG=false
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://claude.ai,https://claude.com
PORT=8080
```

## Error Handling

### MCP Error Responses

```python
class MCPError:
    code: int
    message: str
    data: Optional[dict]

# Standard error codes
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603
```

### Application Errors

```python
class TaskNotFound(Exception):
    status_code = 404
    detail = "Task not found"

class Unauthorized(Exception):
    status_code = 401
    detail = "Invalid or missing authentication"

class ValidationError(Exception):
    status_code = 422
    detail = "Invalid input data"
```

## Performance Considerations

### Database Optimization

- Indexes on frequently queried fields (user_id, completed, priority)
- Connection pooling
- Query result caching for analytics
- Pagination for large result sets

### API Optimization

- Response compression
- Async request handling
- Connection keep-alive
- Rate limiting per user

### Scaling Strategy

- Stateless server design (sessions in tokens, not memory)
- Horizontal scaling via Cloud Run
- Database connection pooling
- CDN for static assets (if any)

## Testing Strategy

### Unit Tests
- Test each service method
- Mock database layer
- Test error conditions

### Integration Tests
- Test MCP protocol compliance
- Test OAuth flow
- Test database operations

### End-to-End Tests
- Test from Claude Code locally
- Test full user workflows
- Test error recovery

## Future Enhancements

### Phase 2 Features
- Calendar integration (schedule tasks as events)
- Task analytics and insights
- Natural language due date parsing
- Recurring tasks

### Scalability
- Multi-user performance optimization
- Database sharding by user
- Caching layer (Redis)
- Read replicas

### Features
- Task templates
- Projects with subtasks
- Team/shared tasks
- Time tracking
- File attachments
