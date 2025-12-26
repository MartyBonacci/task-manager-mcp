# Task Manager MCP Server - Setup Guide

## Prerequisites

Before starting, ensure you have:

- **Python 3.11+** installed
- **Git** for version control
- **Claude Code** installed and configured
- **Google Cloud Platform** account (for deployment phase)
- **Code editor** (VS Code recommended)
- **Terminal** access

## Phase 1: Local Development Setup

### Step 1: Project Initialization

```bash
# Create project directory
mkdir task-manager-mcp
cd task-manager-mcp

# Initialize git
git init
echo "*.pyc
__pycache__/
.env
*.db
venv/
.DS_Store" > .gitignore

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Create basic structure
mkdir -p app/{api,mcp,services,db,auth,config,schemas}
mkdir -p tests scripts
touch app/__init__.py
```

### Step 2: Install Dependencies

Create `requirements.txt`:

```txt
# Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0

# MCP
mcp==0.9.0

# Database
sqlalchemy==2.0.23
alembic==1.12.1

# Auth
google-auth==2.23.4
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Utilities
pydantic==2.5.0
pydantic-settings==2.1.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.1
```

Install:
```bash
pip install -r requirements.txt
```

### Step 3: Environment Configuration

Create `.env` file:

```bash
# App Settings
APP_NAME="Task Manager MCP"
DEBUG=true
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite:///./tasks.db

# Security
SECRET_KEY=dev-secret-key-change-in-production

# OAuth (leave blank for now, fill in Phase 2)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
OAUTH_REDIRECT_URI=http://localhost:8000/oauth/callback

# Server
HOST=0.0.0.0
PORT=8000
```

Create `.env.example` (copy of above with blank values for sharing).

### Step 4: Database Models

Create `app/db/models.py`:

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    project = Column(String, index=True)
    priority = Column(Integer, default=3)
    energy = Column(String, default="medium")
    time_estimate = Column(String, default="1hr")
    notes = Column(Text)
    due_date = Column(DateTime)
    completed = Column(Boolean, default=False, index=True)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True)
    email = Column(String, unique=True)
    preferences = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

Create `app/db/database.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base
from ..config.settings import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_db() -> Session:
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Step 5: Configuration

Create `app/config/settings.py`:

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
    ALLOWED_ORIGINS: str = "*"
    
    # OAuth
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

### Step 6: Pydantic Schemas

Create `app/schemas/task.py`:

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    project: Optional[str] = None
    priority: int = Field(default=3, ge=1, le=5)
    energy: str = Field(default="medium", pattern="^(light|medium|deep)$")
    time_estimate: str = Field(default="1hr")
    notes: Optional[str] = None
    due_date: Optional[datetime] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    project: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    energy: Optional[str] = Field(None, pattern="^(light|medium|deep)$")
    time_estimate: Optional[str] = None
    notes: Optional[str] = None
    due_date: Optional[datetime] = None
    completed: Optional[bool] = None

class Task(TaskBase):
    id: int
    user_id: str
    completed: bool
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

### Step 7: Task Service

Create `app/services/task_service.py`:

```python
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..db.models import Task as TaskModel
from ..schemas.task import TaskCreate, TaskUpdate, Task

class TaskService:
    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id
    
    def create_task(self, task_data: TaskCreate) -> Task:
        """Create a new task"""
        task = TaskModel(
            user_id=self.user_id,
            **task_data.model_dump()
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return Task.model_validate(task)
    
    def get_task(self, task_id: int) -> Optional[Task]:
        """Get task by ID"""
        task = self.db.query(TaskModel).filter(
            TaskModel.id == task_id,
            TaskModel.user_id == self.user_id
        ).first()
        return Task.model_validate(task) if task else None
    
    def list_tasks(
        self,
        project: Optional[str] = None,
        priority: Optional[int] = None,
        show_completed: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[Task]:
        """List tasks with filters"""
        query = self.db.query(TaskModel).filter(TaskModel.user_id == self.user_id)
        
        if not show_completed:
            query = query.filter(TaskModel.completed == False)
        
        if project:
            query = query.filter(TaskModel.project == project)
        
        if priority:
            query = query.filter(TaskModel.priority == priority)
        
        tasks = query.order_by(TaskModel.priority.desc(), TaskModel.created_at).offset(offset).limit(limit).all()
        return [Task.model_validate(t) for t in tasks]
    
    def update_task(self, task_id: int, task_data: TaskUpdate) -> Optional[Task]:
        """Update a task"""
        task = self.db.query(TaskModel).filter(
            TaskModel.id == task_id,
            TaskModel.user_id == self.user_id
        ).first()
        
        if not task:
            return None
        
        update_data = task_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)
        
        self.db.commit()
        self.db.refresh(task)
        return Task.model_validate(task)
    
    def complete_task(self, task_id: int) -> Optional[Task]:
        """Mark task as complete"""
        task = self.db.query(TaskModel).filter(
            TaskModel.id == task_id,
            TaskModel.user_id == self.user_id
        ).first()
        
        if not task:
            return None
        
        task.completed = True
        task.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(task)
        return Task.model_validate(task)
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task"""
        result = self.db.query(TaskModel).filter(
            TaskModel.id == task_id,
            TaskModel.user_id == self.user_id
        ).delete()
        self.db.commit()
        return result > 0
```

### Step 8: MCP Server Implementation

Create `app/mcp/tools.py`:

```python
from typing import Dict, Any, List
from ..services.task_service import TaskService
from ..schemas.task import TaskCreate, TaskUpdate

# Tool definitions for MCP
TOOLS = [
    {
        "name": "task_create",
        "description": "Create a new task",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Task title"},
                "project": {"type": "string", "description": "Project category"},
                "priority": {"type": "integer", "minimum": 1, "maximum": 5, "description": "Priority (1=Someday, 5=Critical)"},
                "energy": {"type": "string", "enum": ["light", "medium", "deep"], "description": "Energy level required"},
                "time_estimate": {"type": "string", "description": "Time estimate (e.g., '1hr', '30min')"},
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
                "limit": {"type": "integer", "default": 100}
            }
        }
    },
    {
        "name": "task_get",
        "description": "Get a specific task by ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer"}
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "task_update",
        "description": "Update a task",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer"},
                "title": {"type": "string"},
                "project": {"type": "string"},
                "priority": {"type": "integer", "minimum": 1, "maximum": 5},
                "energy": {"type": "string", "enum": ["light", "medium", "deep"]},
                "time_estimate": {"type": "string"},
                "notes": {"type": "string"}
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "task_complete",
        "description": "Mark a task as complete",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer"}
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "task_delete",
        "description": "Delete a task",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer"}
            },
            "required": ["task_id"]
        }
    }
]

async def handle_tool_call(tool_name: str, arguments: Dict[str, Any], task_service: TaskService) -> Any:
    """Route tool calls to appropriate handlers"""
    
    if tool_name == "task_create":
        task_data = TaskCreate(**arguments)
        return task_service.create_task(task_data).model_dump()
    
    elif tool_name == "task_list":
        tasks = task_service.list_tasks(**arguments)
        return [t.model_dump() for t in tasks]
    
    elif tool_name == "task_get":
        task = task_service.get_task(arguments["task_id"])
        if not task:
            raise ValueError(f"Task {arguments['task_id']} not found")
        return task.model_dump()
    
    elif tool_name == "task_update":
        task_id = arguments.pop("task_id")
        task_data = TaskUpdate(**arguments)
        task = task_service.update_task(task_id, task_data)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        return task.model_dump()
    
    elif tool_name == "task_complete":
        task = task_service.complete_task(arguments["task_id"])
        if not task:
            raise ValueError(f"Task {arguments['task_id']} not found")
        return task.model_dump()
    
    elif tool_name == "task_delete":
        success = task_service.delete_task(arguments["task_id"])
        if not success:
            raise ValueError(f"Task {arguments['task_id']} not found")
        return {"success": True, "task_id": arguments["task_id"]}
    
    else:
        raise ValueError(f"Unknown tool: {tool_name}")
```

### Step 9: Basic FastAPI App

Create `app/main.py`:

```python
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import json

from .config.settings import settings
from .db.database import get_db, init_db
from .services.task_service import TaskService
from .mcp.tools import TOOLS, handle_tool_call

app = FastAPI(title=settings.APP_NAME)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
def startup():
    init_db()

# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# MCP Protocol discovery
@app.head("/")
def mcp_discovery():
    return {
        "headers": {
            "MCP-Protocol-Version": "2025-06-18"
        }
    }

# MCP Message handler
@app.post("/")
async def mcp_handler(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    method = body.get("method")
    
    # For now, use a mock user_id (replace with OAuth in Phase 2)
    user_id = "dev-user"
    
    # Handle initialize
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
    
    # Handle tools/list
    elif method == "tools/list":
        return {
            "tools": TOOLS
        }
    
    # Handle tools/call
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
                        "text": json.dumps(result, indent=2)
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
```

### Step 10: Test Locally

Create `scripts/test_local.py`:

```python
import requests
import json

BASE_URL = "http://localhost:8000"

def test_initialize():
    response = requests.post(BASE_URL, json={"method": "initialize"})
    print("Initialize:", response.json())

def test_tools_list():
    response = requests.post(BASE_URL, json={"method": "tools/list"})
    print("Tools:", json.dumps(response.json(), indent=2))

def test_create_task():
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
    print("Created task:", response.json())

def test_list_tasks():
    response = requests.post(BASE_URL, json={
        "method": "tools/call",
        "params": {
            "name": "task_list",
            "arguments": {}
        }
    })
    print("Tasks:", json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_initialize()
    test_tools_list()
    test_create_task()
    test_list_tasks()
```

### Step 11: Run and Test

```bash
# Terminal 1: Start server
uvicorn app.main:app --reload

# Terminal 2: Test
python scripts/test_local.py
```

## Phase 2: Claude Code Integration

### Step 1: Create MCP Server Config

For stdio connection (local testing with Claude Code):

Create `~/.claude/config/task-manager.json`:

```json
{
  "mcpServers": {
    "task-manager": {
      "command": "python",
      "args": ["-m", "uvicorn", "app.main:app", "--port", "8000"],
      "cwd": "/path/to/task-manager-mcp",
      "env": {
        "PYTHONPATH": "/path/to/task-manager-mcp"
      }
    }
  }
}
```

### Step 2: Test from Claude Code

```bash
# In your project directory
claude

# Then in Claude Code:
"List my available MCP tools"
"Create a task: Research MCP protocol"
"Show me all my tasks"
```

## Next Steps

Once Phase 1 is working locally:

1. **Phase 2**: Implement OAuth 2.1
2. **Phase 3**: Deploy to Google Cloud Run
3. **Phase 4**: Polish and production-ready features

## Troubleshooting

**Database errors**: Make sure init_db() runs on startup
**Import errors**: Check PYTHONPATH and package structure
**MCP not connecting**: Verify config file path and server running
**Port conflicts**: Change PORT in .env

## Resources

- MCP Spec: https://spec.modelcontextprotocol.io/
- FastAPI Docs: https://fastapi.tiangolo.com/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Claude MCP: https://docs.claude.com/docs/model-context-protocol
