# Tasks: OAuth 2.1 Authentication

**Feature**: 003 - OAuth 2.1 Authentication with Google
**Created**: 2025-12-26
**Status**: Ready for Implementation
**Parent Branch**: main

<!-- Tech Stack Validation: PASSED -->
<!-- Validated against: .specswarm/tech-stack.md v1.1.0 -->
<!-- No prohibited technologies found -->
<!-- 0 unapproved technologies require runtime validation -->

---

## Execution Strategy

**Implementation Mode**: Sequential with parallel opportunities
**Estimated Effort**: 19-27 hours (2-3.5 days)
**Total Tasks**: 43 tasks across 8 phases

**Critical Path**:
1. Foundational phase MUST complete before any user story
2. Each user story phase can start once foundational complete
3. Testing phase requires all implementation phases complete

**MVP Scope**: Phase 3 only (Core OAuth Flow) - delivers Scenarios 1, 2, 3
**Full Delivery**: All phases - delivers all 5 scenarios

---

## Task Organization

Tasks are organized by **Functional Requirements** which map to **User Scenarios**:

| Phase | Functional Requirement | User Scenarios | Deliverable |
|-------|----------------------|----------------|-------------|
| 1 | Setup | All | Project configured |
| 2 | Foundational | All | Database ready |
| 3 | FR1, FR2, FR3, FR5 | 1, 2, 3 | OAuth flow working |
| 4 | FR5 (MCP Integration) | 2 | MCP tools authenticated |
| 5 | FR4 | 4 | Mobile auth working |
| 6 | FR7 | 5 | Error handling complete |
| 7 | Testing | All | Quality validated |
| 8 | Polish | All | Production ready |

---

## Phase 1: Setup (Project Initialization)

**Goal**: Configure environment and install dependencies

**Independent Test Criteria**:
- ✅ Dependencies install without errors
- ✅ Environment variables validated
- ✅ Virtual environment active

### T001: Update requirements.txt
**Description**: Add OAuth dependencies to requirements.txt
**File**: `requirements.txt`
**Story**: [Setup]
**Parallel**: No (foundational)

**Changes**:
```txt
# OAuth 2.1 Authentication
google-auth==2.35.0
google-auth-oauthlib==1.2.0
cryptography==44.0.0
```

**Validation**:
- Requirements file updated
- Version pins match tech-stack.md v1.1.0
- No conflicting dependencies

---

### T002: Install dependencies
**Description**: Install updated dependencies in virtual environment
**Command**: `pip install -r requirements.txt`
**Story**: [Setup]
**Parallel**: No (depends on T001)

**Validation**:
- All packages install successfully
- `pip list` shows correct versions:
  - google-auth>=2.35.0
  - google-auth-oauthlib>=1.2.0
  - cryptography>=44.0.0

---

### T003: Create .env.example
**Description**: Add OAuth environment variables to .env.example
**File**: `.env.example`
**Story**: [Setup]
**Parallel**: Yes [P]

**Changes**:
```bash
# OAuth 2.1 Configuration
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
OAUTH_REDIRECT_URI=http://localhost:8000/oauth/callback

# Token Encryption (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
ENCRYPTION_KEY=your-32-byte-base64-encoded-key

# Development Mode (NEVER enable in production)
DEVELOPMENT_MODE=false
```

**Validation**:
- .env.example contains all required OAuth variables
- Comments explain how to generate ENCRYPTION_KEY
- Development mode disabled by default

---

### T004: Update settings.py
**Description**: Add OAuth configuration to settings
**File**: `app/config/settings.py`
**Story**: [Setup]
**Parallel**: Yes [P]

**Changes**:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... existing settings ...

    # OAuth 2.1 Configuration
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    OAUTH_REDIRECT_URI: str
    ENCRYPTION_KEY: str
    DEVELOPMENT_MODE: bool = False

    class Config:
        env_file = ".env"
```

**Validation**:
- Settings class updated
- OAuth variables type-hinted correctly
- DEVELOPMENT_MODE defaults to False
- Settings load from .env file

---

## Phase 2: Foundational (Blocking Prerequisites)

**Goal**: Create database schema and core utilities

**CRITICAL**: This phase MUST complete before ANY user story can be implemented

**Independent Test Criteria**:
- ✅ Database migration runs successfully
- ✅ All models defined with relationships
- ✅ Token encryption/decryption works
- ✅ Dev user exists in database

### T005: Create User model
**Description**: Define User entity in SQLAlchemy
**File**: `app/db/models.py` (extend existing)
**Story**: [Foundational]
**Parallel**: No (foundational)

**Implementation**:
```python
class User(Base):
    __tablename__ = "users"

    user_id = Column(String(255), primary_key=True)
    email = Column(String(320), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user")
```

**Validation**:
- User model defined with all fields from data-model.md
- Relationships to Session and Task established
- Indexes created (email)
- Type hints correct

---

### T006: Create Session model
**Description**: Define Session entity in SQLAlchemy
**File**: `app/db/models.py`
**Story**: [Foundational]
**Parallel**: Yes [P] (same file as T005, but logically independent)

**Implementation**:
```python
class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(String(43), primary_key=True)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    access_token = Column(LargeBinary(512), nullable=False)
    refresh_token = Column(LargeBinary(512), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_agent = Column(String(500), nullable=True)

    # Relationships
    user = relationship("User", back_populates="sessions")

    # Indexes
    __table_args__ = (
        Index("idx_session_user_id", "user_id"),
        Index("idx_session_expires_at", "expires_at"),
        Index("idx_session_last_activity", "last_activity"),
    )
```

**Validation**:
- Session model defined with encrypted token fields (LargeBinary)
- Foreign key to User
- All indexes created
- Cascade delete configured

---

### T007: Create DynamicClient model
**Description**: Define DynamicClient entity in SQLAlchemy
**File**: `app/db/models.py`
**Story**: [Foundational]
**Parallel**: Yes [P]

**Implementation**:
```python
class DynamicClient(Base):
    __tablename__ = "dynamic_clients"

    client_id = Column(String(36), primary_key=True)
    client_secret = Column(LargeBinary(512), nullable=False)
    platform = Column(String(50), nullable=False)
    redirect_uris = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_used = Column(DateTime(timezone=True), nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_dynamic_client_expires_at", "expires_at"),
        Index("idx_dynamic_client_platform", "platform"),
    )
```

**Validation**:
- DynamicClient model defined
- JSON field for redirect_uris
- Encrypted client_secret (LargeBinary)
- Indexes created

---

### T008: Update Task model
**Description**: Add user_id foreign key to existing Task model
**File**: `app/db/models.py` (modify existing)
**Story**: [Foundational]
**Parallel**: No (same file, modifies existing model)

**Changes**:
```python
class Task(Base):
    __tablename__ = "tasks"

    # ... existing fields ...

    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False, index=True)

    # Add relationship
    user = relationship("User", back_populates="tasks")

    # Update table args with new index
    __table_args__ = (
        # ... existing indexes ...
        Index("idx_task_user_id", "user_id"),
    )
```

**Validation**:
- user_id column added with foreign key
- Relationship to User added
- Index created on user_id
- RESTRICT on delete (cannot delete user with tasks)

---

### T009: Create Alembic migration
**Description**: Generate database migration for OAuth tables
**File**: `alembic/versions/002_add_oauth_tables.py`
**Story**: [Foundational]
**Parallel**: No (depends on T005-T008)

**Command**: `alembic revision -m "Add OAuth 2.1 authentication tables"`

**Implementation**: See data-model.md for complete migration script

**Migration Steps**:
1. Create users table
2. Insert dev-user record
3. Add user_id column to tasks (nullable)
4. Migrate existing tasks to dev-user
5. Make user_id NOT NULL
6. Add foreign key constraint
7. Create sessions table
8. Create dynamic_clients table

**Validation**:
- Migration file created
- Upgrade() function implements all changes
- Downgrade() function reverses all changes
- Migration tested on fresh database

---

### T010: Run migration
**Description**: Apply database migration
**Command**: `alembic upgrade head`
**Story**: [Foundational]
**Parallel**: No (depends on T009)

**Validation**:
- Migration runs without errors
- All tables created:
  - users
  - sessions
  - dynamic_clients
- Task table updated (user_id column added)
- Dev user exists: `SELECT * FROM users WHERE user_id = 'dev-user'`
- Existing tasks migrated: `SELECT COUNT(*) FROM tasks WHERE user_id = 'dev-user'`

---

### T011: Create encryption utility
**Description**: Implement token encryption/decryption with AES-256
**File**: `app/auth/encryption.py` (new)
**Story**: [Foundational]
**Parallel**: Yes [P]

**Implementation**:
```python
from cryptography.fernet import Fernet
import os

class TokenEncryption:
    """AES-256 encryption for OAuth tokens."""

    def __init__(self):
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            raise ValueError("ENCRYPTION_KEY environment variable required")
        self.fernet = Fernet(key.encode())

    def encrypt(self, token: str) -> bytes:
        """Encrypt OAuth token for database storage."""
        if not token:
            raise ValueError("Token cannot be empty")
        return self.fernet.encrypt(token.encode())

    def decrypt(self, encrypted: bytes) -> str:
        """Decrypt OAuth token from database."""
        if not encrypted:
            raise ValueError("Encrypted data cannot be empty")
        return self.fernet.decrypt(encrypted).decode()

# Singleton instance
_encryption = None

def get_encryption() -> TokenEncryption:
    """Get encryption singleton."""
    global _encryption
    if _encryption is None:
        _encryption = TokenEncryption()
    return _encryption

def encrypt_token(token: str) -> bytes:
    """Convenience function for encrypting tokens."""
    return get_encryption().encrypt(token)

def decrypt_token(encrypted: bytes) -> str:
    """Convenience function for decrypting tokens."""
    return get_encryption().decrypt(encrypted)
```

**Validation**:
- Encryption class uses Fernet (AES-256)
- Environment variable validated
- Encrypt/decrypt round-trip works
- Empty token validation
- Singleton pattern for performance

---

### T012: Create Pydantic schemas
**Description**: Define request/response schemas for OAuth endpoints
**File**: `app/schemas/auth.py` (new)
**Story**: [Foundational]
**Parallel**: Yes [P]

**Implementation**:
```python
from pydantic import BaseModel, Field, field_validator
from typing import List, Literal
from datetime import datetime

class ClientRegistrationRequest(BaseModel):
    """Request to register dynamic OAuth client."""
    platform: Literal["ios", "android", "macos", "windows", "linux", "cli"]
    redirect_uris: List[str] = Field(..., min_length=1, max_length=5)
    client_name: str = Field(None, max_length=100)

    @field_validator("redirect_uris")
    def validate_redirect_uris(cls, v):
        for uri in v:
            if not (uri.startswith("https://") or
                    uri.startswith("http://localhost") or
                    "://" in uri):  # Custom scheme
                raise ValueError(f"Invalid redirect URI: {uri}")
        return v

class ClientRegistrationResponse(BaseModel):
    """Response from client registration."""
    client_id: str
    client_secret: str
    expires_at: datetime
    redirect_uris: List[str]

class AuthorizationResponse(BaseModel):
    """Response from /oauth/authorize."""
    authorization_url: str
    state: str

class CallbackResponse(BaseModel):
    """Response from /oauth/callback."""
    session_id: str
    user_email: str
    user_id: str

class AuthError(BaseModel):
    """Authentication error response."""
    error: Literal["authentication_required", "token_expired", "access_revoked", "invalid_session"]
    message: str
    authorization_url: str
    instructions: str = None
```

**Validation**:
- All schemas defined with proper types
- Validators for redirect URIs
- Literal types for enums
- Matches OpenAPI contract (oauth-api.yaml)

---

## Phase 3: Core OAuth Flow (FR1, FR2, FR3, FR5)

**Goal**: Implement OAuth authorization code flow with Google

**User Stories**: Scenarios 1, 2, 3
- Scenario 1: First-Time User Authentication (Web)
- Scenario 2: Subsequent Access (Session Active)
- Scenario 3: Token Expiration and Refresh

**Independent Test Criteria**:
- ✅ User clicks "Authorize" → Redirected to Google
- ✅ User signs in with Google → Callback succeeds
- ✅ Session created with encrypted tokens
- ✅ User record created in database
- ✅ Subsequent requests use session (no re-auth)
- ✅ Expired tokens auto-refresh transparently

### T013: Create OAuth configuration
**Description**: Configure Google OAuth flow
**File**: `app/config/oauth.py` (new)
**Story**: [US1] First-Time Authentication
**Parallel**: No (foundational for OAuth)

**Implementation**:
```python
from google_auth_oauthlib.flow import Flow
from app.config.settings import settings

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

def create_oauth_flow() -> Flow:
    """Create Google OAuth flow instance."""
    return Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=settings.OAUTH_REDIRECT_URI,
    )
```

**Validation**:
- OAuth flow configuration works
- Scopes limited to email + profile
- Environment variables loaded from settings
- Flow reusable across endpoints

---

### T014: Create user service
**Description**: Service layer for user management
**File**: `app/services/user_service.py` (new)
**Story**: [US1] First-Time Authentication
**Parallel**: Yes [P]

**Implementation**:
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import User
from datetime import datetime, timezone

async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    """Get user by Google user ID."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    return result.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Get user by email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def create_user(
    db: AsyncSession,
    user_id: str,
    email: str,
    name: str | None
) -> User:
    """Create new user from OAuth data."""
    user = User(
        user_id=user_id,
        email=email,
        name=name,
        last_login=datetime.now(timezone.utc)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def update_last_login(db: AsyncSession, user_id: str) -> None:
    """Update user's last login timestamp."""
    user = await get_user_by_id(db, user_id)
    if user:
        user.last_login = datetime.now(timezone.utc)
        await db.commit()

async def upsert_user(
    db: AsyncSession,
    user_id: str,
    email: str,
    name: str | None
) -> User:
    """Create user if doesn't exist, update last_login if exists."""
    user = await get_user_by_id(db, user_id)
    if user:
        user.last_login = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)
    else:
        user = await create_user(db, user_id, email, name)
    return user
```

**Validation**:
- All CRUD operations for User
- Async/await syntax
- Proper session handling
- Type hints for return values

---

### T015: Create session service
**Description**: Service layer for session management
**File**: `app/services/session_service.py` (new)
**Story**: [US2] Subsequent Access
**Parallel**: Yes [P]

**Implementation**: See plan.md Phase 3 for detailed implementation

**Key Functions**:
- `create_session()` - Create session with encrypted tokens
- `get_session()` - Load session by ID
- `update_session_activity()` - Update last_activity timestamp
- `refresh_session_tokens()` - Refresh expired tokens
- `delete_session()` - Delete session (logout)
- `cleanup_expired_sessions()` - Delete inactive sessions (>24h)

**Validation**:
- All session operations use encryption
- Token expiration handled
- Activity tracking works
- Cleanup job ready for cron

---

### T016: Implement /oauth/authorize endpoint
**Description**: Generate Google OAuth authorization URL
**File**: `app/api/oauth.py` (new router)
**Story**: [US1] First-Time Authentication
**Parallel**: No (uses T013)

**Implementation**:
```python
from fastapi import APIRouter, HTTPException
from app.config.oauth import create_oauth_flow
from app.schemas.auth import AuthorizationResponse
import secrets

router = APIRouter(prefix="/oauth", tags=["OAuth"])

# Temporary state storage (use Redis in production)
oauth_states = {}

@router.get("/authorize", response_model=AuthorizationResponse)
async def authorize():
    """Initiate OAuth authorization flow."""
    flow = create_oauth_flow()

    # Generate CSRF state
    state = secrets.token_urlsafe(32)

    # Generate PKCE code verifier
    code_verifier = secrets.token_urlsafe(96)
    flow.code_verifier = code_verifier

    # Store state and verifier temporarily (5 minute expiration)
    oauth_states[state] = {
        "code_verifier": code_verifier,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5)
    }

    # Generate authorization URL
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        state=state,
        include_granted_scopes="true",
        prompt="consent",
    )

    return AuthorizationResponse(
        authorization_url=authorization_url,
        state=state
    )
```

**Validation**:
- Endpoint returns authorization URL
- State parameter generated
- PKCE code_verifier generated
- Temporary state storage works

---

### T017: Implement /oauth/callback endpoint
**Description**: Handle OAuth callback and create session
**File**: `app/api/oauth.py`
**Story**: [US1] First-Time Authentication
**Parallel**: No (depends on T016)

**Implementation**: See plan.md Phase 4, Task T4.3

**Key Steps**:
1. Validate state parameter (CSRF protection)
2. Exchange authorization code for tokens (with PKCE)
3. Validate ID token with google-auth
4. Create or update user
5. Create session with encrypted tokens
6. Delete temporary state
7. Return session_id

**Validation**:
- State validation prevents CSRF
- PKCE code_verifier used
- ID token validated
- User created/updated
- Session created with encrypted tokens
- Callback succeeds end-to-end

---

### T018: Implement token refresh logic
**Description**: Auto-refresh expired access tokens
**File**: `app/services/session_service.py` (add to existing)
**Story**: [US3] Token Expiration and Refresh
**Parallel**: Yes [P]

**Implementation**: See plan.md Phase 4, Task T4.4

**Key Logic**:
1. Decrypt refresh_token from session
2. Use google-auth to refresh
3. Encrypt new access_token
4. Update session with new tokens (Google rotates refresh_token)
5. Commit to database

**Validation**:
- Refresh token decrypted correctly
- New tokens fetched from Google
- Rotated refresh_token saved
- Session updated in database
- No user interruption (transparent)

---

### T019: Create authentication middleware
**Description**: Authenticate MCP requests and inject user_id
**File**: `app/api/middleware.py` (new)
**Story**: [US2] Subsequent Access
**Parallel**: No (uses session_service from T015)

**Implementation**: See mcp-auth-integration.md for complete middleware

**Key Logic**:
1. Check if method requires auth (initialize, tools/list = no)
2. Extract MCP-Session-Id header
3. Load session from database
4. Check token expiration (auto-refresh if expired)
5. Validate access token with Google
6. Update session activity
7. Return user_id

**Validation**:
- initialize/tools/list bypass auth
- tools/call requires session
- Expired tokens auto-refreshed
- Token validation works
- Activity timestamp updated
- User_id returned correctly

---

### T020: Update MCP handler
**Description**: Integrate auth middleware with existing MCP handler
**File**: `app/main.py` (modify existing)
**Story**: [US2] Subsequent Access
**Parallel**: No (depends on T019)

**Changes**:
```python
from fastapi import Depends
from app.api.middleware import authenticate_mcp_request

@app.post("/")
async def mcp_handler(
    request: Request,
    db: Session = Depends(get_db),
    user_id: str = Depends(authenticate_mcp_request)  # NEW: Auth middleware
):
    """Handle MCP protocol requests."""
    body = await request.json()
    method = body.get("method")

    if method == "tools/call":
        # NEW: Inject user_id from middleware
        params = body.get("params", {})
        params["user_id"] = user_id

        result = await handle_tool_call(db, params)
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

    # ... existing initialize, tools/list handlers ...
```

**Validation**:
- Middleware dependency injected
- user_id passed to tool calls
- Unauthenticated methods still work
- Authentication errors returned correctly

---

### T021: Update TaskService for user isolation
**Description**: Add user_id parameter to all TaskService methods
**File**: `app/services/task_service.py` (modify existing)
**Story**: [US2] Subsequent Access
**Parallel**: No (core service change)

**Changes**:
- Add `user_id: str` parameter to ALL methods
- Filter all queries: `where(Task.user_id == user_id)`
- Set user_id on create: `task.user_id = user_id`
- Remove hardcoded `user_id = "dev-user"`

**Affected Methods**:
- `create_task(db, user_id, task_data)` - NEW user_id parameter
- `list_tasks(db, user_id, filters)` - Filter by user_id
- `get_task(db, user_id, task_id)` - Filter by user_id
- `update_task(db, user_id, task_id, updates)` - Filter by user_id
- `complete_task(db, user_id, task_id)` - Filter by user_id
- `delete_task(db, user_id, task_id)` - Filter by user_id
- `search_tasks(db, user_id, query)` - Filter by user_id
- `get_task_stats(db, user_id)` - Filter by user_id

**Validation**:
- All methods require user_id
- All queries filter by user_id
- User cannot access other user's tasks
- Create operations set user_id correctly

---

### T022: Register OAuth router
**Description**: Add OAuth router to FastAPI app
**File**: `app/main.py` (modify existing)
**Story**: [US1] First-Time Authentication
**Parallel**: Yes [P]

**Changes**:
```python
from app.api.oauth import router as oauth_router

app = FastAPI(title="Task Manager MCP Server")

# Register OAuth routes
app.include_router(oauth_router)
```

**Validation**:
- OAuth endpoints accessible:
  - GET /oauth/authorize
  - GET /oauth/callback
  - POST /oauth/logout
  - POST /oauth/refresh
- Routes return correct schemas

---

## Phase 4: MCP Integration Testing (FR5)

**Goal**: Verify MCP authentication integration works end-to-end

**User Story**: Scenario 2 (Subsequent Access)

**Independent Test Criteria**:
- ✅ MCP initialize works without auth
- ✅ MCP tools/list works without auth
- ✅ MCP tools/call requires auth (401 without session)
- ✅ MCP tools/call works with valid session
- ✅ Expired session auto-refreshes
- ✅ Invalid session returns clear error

### T023: Test MCP unauthenticated methods
**Description**: Verify initialize and tools/list work without auth
**File**: `tests/test_mcp_auth.py` (new)
**Story**: [US2] Subsequent Access
**Parallel**: No (integration test)

**Test Cases**:
```python
@pytest.mark.asyncio
async def test_initialize_without_auth(client):
    """MCP initialize should work without authentication."""
    response = await client.post("/", json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {...}
    })
    assert response.status_code == 200
    assert "result" in response.json()

@pytest.mark.asyncio
async def test_tools_list_without_auth(client):
    """MCP tools/list should work without authentication."""
    response = await client.post("/", json={
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list"
    })
    assert response.status_code == 200
    assert "result" in response.json()
    assert "tools" in response.json()["result"]
```

**Validation**:
- Both tests pass
- No authentication required
- Responses match MCP spec

---

### T024: Test MCP authenticated methods
**Description**: Verify tools/call requires auth
**File**: `tests/test_mcp_auth.py`
**Story**: [US2] Subsequent Access
**Parallel**: Yes [P]

**Test Cases**:
```python
@pytest.mark.asyncio
async def test_tools_call_without_auth(client):
    """tools/call should require authentication."""
    response = await client.post("/", json={
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "task_create", "arguments": {"title": "Test"}}
    })
    assert response.status_code == 401
    error = response.json()["error"]
    assert error["data"]["error"] == "authentication_required"
    assert "authorization_url" in error["data"]

@pytest.mark.asyncio
async def test_tools_call_with_valid_session(authenticated_client):
    """tools/call should work with valid session."""
    response = await authenticated_client.post("/", json={
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {"name": "task_create", "arguments": {"title": "Test"}}
    })
    assert response.status_code == 200
    assert "result" in response.json()
```

**Validation**:
- Unauthenticated request returns 401
- Authenticated request succeeds
- Error message includes authorization URL

---

### T025: Test token refresh
**Description**: Verify expired tokens auto-refresh
**File**: `tests/test_mcp_auth.py`
**Story**: [US3] Token Expiration and Refresh
**Parallel**: Yes [P]

**Test Case**:
```python
@pytest.mark.asyncio
async def test_expired_token_auto_refreshes(db_session, test_user):
    """Expired tokens should auto-refresh transparently."""
    # Create session with expired token
    session = create_test_session(
        user_id=test_user.user_id,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1)  # Expired
    )

    # Make request with expired session
    response = await client.post(
        "/",
        json={"jsonrpc": "2.0", "id": 5, "method": "tools/call", ...},
        headers={"MCP-Session-Id": session.session_id}
    )

    # Should succeed (token refreshed automatically)
    assert response.status_code == 200

    # Verify session updated in database
    updated_session = await get_session(db_session, session.session_id)
    assert updated_session.expires_at > datetime.now(timezone.utc)
```

**Validation**:
- Expired token triggers refresh
- Request succeeds after refresh
- Session updated in database
- User unaware of refresh (transparent)

---

### T026: Test user data isolation
**Description**: Verify users cannot access other users' tasks
**File**: `tests/test_user_isolation.py` (new)
**Story**: [US2] Subsequent Access
**Parallel**: Yes [P]

**Test Case**:
```python
@pytest.mark.asyncio
async def test_user_data_isolation(db_session):
    """Users should only see their own tasks."""
    # Create two users
    user_a = await create_user(db_session, "user-a", "a@example.com", "User A")
    user_b = await create_user(db_session, "user-b", "b@example.com", "User B")

    # Create task for user A
    task_a = await create_task(db_session, user_a.user_id, {"title": "Task A"})

    # User B should NOT see user A's task
    tasks_b = await list_tasks(db_session, user_b.user_id)
    assert len(tasks_b) == 0

    # User B cannot access task A by ID
    with pytest.raises(HTTPException) as exc:
        await get_task(db_session, user_b.user_id, task_a.id)
    assert exc.value.status_code == 404
```

**Validation**:
- Users see only their own tasks
- User cannot access other user's tasks by ID
- Cross-user data leakage prevented

---

## Phase 5: Dynamic Client Registration (FR4)

**Goal**: Implement RFC 7591 for mobile/desktop clients

**User Story**: Scenario 4 (Mobile App Authentication)

**Independent Test Criteria**:
- ✅ Client can register with platform and redirect URIs
- ✅ Client receives client_id and client_secret
- ✅ Client credentials work in OAuth flow
- ✅ Client secret encrypted in database
- ✅ Expired clients cleaned up

### T027: Implement /oauth/register endpoint
**Description**: Dynamic client registration endpoint
**File**: `app/api/oauth.py` (add to existing router)
**Story**: [US4] Mobile App Authentication
**Parallel**: No (extends T016/T017)

**Implementation**: See plan.md Phase 6, Task T6.1

**Key Logic**:
1. Generate UUID client_id
2. Generate secure client_secret (32 bytes)
3. Validate redirect URIs (https:// or custom scheme://)
4. Create DynamicClient record with encrypted secret
5. Set 30-day expiration
6. Return credentials (secret returned ONLY ONCE)

**Validation**:
- Client registration succeeds
- client_id is valid UUID
- client_secret is cryptographically secure
- Secret encrypted in database
- 30-day expiration set
- Invalid redirect URIs rejected

---

### T028: Create dynamic client service
**Description**: Service layer for dynamic client management
**File**: `app/services/dynamic_client_service.py` (new)
**Story**: [US4] Mobile App Authentication
**Parallel**: Yes [P]

**Functions**:
- `create_dynamic_client()` - Register client
- `get_dynamic_client()` - Load client by ID
- `validate_client_credentials()` - Verify client_id + client_secret
- `update_last_used()` - Track client usage
- `cleanup_expired_clients()` - Delete expired clients

**Validation**:
- All CRUD operations work
- Secret encryption/decryption correct
- Cleanup job ready for cron

---

### T029: Test dynamic client registration
**Description**: Integration test for client registration
**File**: `tests/test_dynamic_client.py` (new)
**Story**: [US4] Mobile App Authentication
**Parallel**: Yes [P]

**Test Cases**:
```python
@pytest.mark.asyncio
async def test_register_dynamic_client(client):
    """Client registration should return credentials."""
    response = await client.post("/oauth/register", json={
        "platform": "ios",
        "redirect_uris": ["com.example.app://oauth/callback"],
        "client_name": "Test App"
    })
    assert response.status_code == 201
    data = response.json()
    assert "client_id" in data
    assert "client_secret" in data
    assert data["expires_at"] is not None

@pytest.mark.asyncio
async def test_dynamic_client_oauth_flow(client, db_session):
    """Dynamic client should work in OAuth flow."""
    # 1. Register client
    reg_response = await client.post("/oauth/register", json={
        "platform": "ios",
        "redirect_uris": ["com.example.app://oauth/callback"]
    })
    client_id = reg_response.json()["client_id"]

    # 2. Use client in OAuth flow (with PKCE)
    # ... (full OAuth flow test with dynamic client)

    # 3. Verify last_used updated
    dynamic_client = await get_dynamic_client(db_session, client_id)
    assert dynamic_client.last_used is not None
```

**Validation**:
- Registration succeeds
- Credentials work in OAuth flow
- last_used timestamp updated
- Secret only returned once

---

### T030: Implement client cleanup job
**Description**: Scheduled job to delete expired clients
**File**: `app/tasks/cleanup.py` (new)
**Story**: [US4] Mobile App Authentication
**Parallel**: Yes [P]

**Implementation**:
```python
from sqlalchemy import delete
from app.db.models import DynamicClient, Session
from datetime import datetime, timezone

async def cleanup_expired_clients(db: AsyncSession):
    """Delete expired dynamic clients."""
    result = await db.execute(
        delete(DynamicClient).where(
            DynamicClient.expires_at < datetime.now(timezone.utc)
        )
    )
    await db.commit()
    return result.rowcount

async def cleanup_expired_sessions(db: AsyncSession):
    """Delete inactive sessions (>24 hours)."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    result = await db.execute(
        delete(Session).where(Session.last_activity < cutoff)
    )
    await db.commit()
    return result.rowcount
```

**Validation**:
- Expired clients deleted correctly
- Inactive sessions deleted
- Cleanup job ready for cron scheduler

---

## Phase 6: Error Handling (FR7)

**Goal**: Provide clear, actionable error messages

**User Story**: Scenario 5 (Revoked Access)

**Independent Test Criteria**:
- ✅ Authentication errors include authorization URL
- ✅ Expired vs. revoked access distinguished
- ✅ Error messages user-friendly
- ✅ Tokens never exposed in errors
- ✅ All auth errors logged

### T031: Implement error schemas
**Description**: Define error response schemas
**File**: `app/schemas/auth.py` (extend from T012)
**Story**: [US5] Revoked Access
**Parallel**: Yes [P]

**Already Done in T012** - Validation:
- AuthError schema defined
- Error types enumerated
- User-friendly messages
- Authorization URL included

---

### T032: Enhance error responses
**Description**: Update middleware with better error messages
**File**: `app/api/middleware.py` (modify T019)
**Story**: [US5] Revoked Access
**Parallel**: No (extends T019)

**Changes**:
```python
# Distinguish between different error types
if not session:
    raise HTTPException(
        status_code=401,
        detail={
            "error": "invalid_session",
            "message": "Session not found or expired",
            "authorization_url": "/oauth/authorize",
            "instructions": "Your session has expired. Please re-authorize."
        }
    )

# Token validation failed (could be revoked)
except GoogleAuthError as e:
    if "invalid_grant" in str(e):
        # Access revoked
        raise HTTPException(
            status_code=403,
            detail={
                "error": "access_revoked",
                "message": "Task Manager access was revoked from your Google account",
                "authorization_url": "/oauth/authorize",
                "instructions": "Click the authorization URL to re-grant access"
            }
        )
    else:
        # Token expired or invalid
        raise HTTPException(
            status_code=401,
            detail={
                "error": "token_expired",
                "message": "Your session has expired",
                "authorization_url": "/oauth/authorize"
            }
        )
```

**Validation**:
- Different errors have different messages
- Revoked access returns 403
- Expired session returns 401
- Authorization URL always included
- Instructions clear and actionable

---

### T033: Implement auth error logging
**Description**: Log authentication errors without exposing tokens
**File**: `app/api/middleware.py` (modify T019)
**Story**: [US5] Revoked Access
**Parallel**: Yes [P]

**Implementation**:
```python
import logging

logger = logging.getLogger(__name__)

async def authenticate_mcp_request(...):
    try:
        # ... authentication logic ...
    except HTTPException as e:
        # Log auth failures (without tokens)
        logger.warning(
            f"Authentication failed: {e.detail.get('error')}",
            extra={
                "user_id": session.user_id if session else None,
                "error_type": e.detail.get("error"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        raise
```

**Validation**:
- All auth errors logged
- Tokens never logged
- User_id included for debugging
- Error type and timestamp captured

---

### T034: Test error scenarios
**Description**: Integration tests for all error types
**File**: `tests/test_auth_errors.py` (new)
**Story**: [US5] Revoked Access
**Parallel**: Yes [P]

**Test Cases**:
```python
@pytest.mark.asyncio
async def test_missing_session_error(client):
    """Missing session should return clear error."""
    response = await client.post("/", json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {...}
    })
    assert response.status_code == 401
    error = response.json()["error"]["data"]
    assert error["error"] == "authentication_required"
    assert "authorization_url" in error
    assert "instructions" in error

@pytest.mark.asyncio
async def test_revoked_access_error(client, revoked_session):
    """Revoked access should return 403 with re-auth URL."""
    response = await client.post(
        "/",
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/call", ...},
        headers={"MCP-Session-Id": revoked_session.session_id}
    )
    assert response.status_code == 403
    error = response.json()["error"]["data"]
    assert error["error"] == "access_revoked"
    assert "re-grant access" in error["instructions"]
```

**Validation**:
- All error types tested
- Error messages correct
- Authorization URLs included
- No tokens in error responses

---

## Phase 7: Testing

**Goal**: Comprehensive test coverage for OAuth implementation

**Independent Test Criteria**:
- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ Security tests pass (CSRF, PKCE, isolation)
- ✅ Code coverage ≥80%
- ✅ No regressions in Phase 1 functionality

### T035: Unit tests - Encryption
**Description**: Test token encryption/decryption
**File**: `tests/test_encryption.py` (new)
**Parallel**: Yes [P]

**Test Cases**:
- Encrypt/decrypt round-trip
- Different tokens produce different ciphertexts
- Invalid ciphertext raises error
- Missing encryption key raises error
- Empty token validation

**Validation**: All tests pass

---

### T036: Unit tests - User service
**Description**: Test user CRUD operations
**File**: `tests/test_user_service.py` (new)
**Parallel**: Yes [P]

**Test Cases**:
- Create user
- Get user by ID
- Get user by email
- Update last login
- Upsert user (create if new, update if exists)

**Validation**: All tests pass

---

### T037: Unit tests - Session service
**Description**: Test session management
**File**: `tests/test_session_service.py` (new)
**Parallel**: Yes [P]

**Test Cases**:
- Create session with encrypted tokens
- Get session by ID
- Update session activity
- Refresh expired token
- Delete session (logout)
- Cleanup expired sessions

**Validation**: All tests pass

---

### T038: Integration tests - OAuth flow
**Description**: End-to-end OAuth flow (mocked Google)
**File**: `tests/test_oauth_flow.py` (new)
**Parallel**: No (integration test)

**Test Cases**:
- Full authorization code flow
- State validation (reject invalid state)
- PKCE validation
- User creation on first auth
- Session creation with encrypted tokens
- Token refresh flow

**Validation**: All tests pass

---

### T039: Security tests
**Description**: Security vulnerability tests
**File**: `tests/test_auth_security.py` (new)
**Parallel**: Yes [P]

**Test Cases**:
- CSRF attack prevented (invalid state)
- Token interception prevented (PKCE)
- Cross-user data leakage prevented
- Tokens not logged in errors
- Rate limiting enforced (if implemented)

**Validation**: All tests pass

---

### T040: Test coverage report
**Description**: Measure and validate code coverage
**Command**: `pytest --cov=app --cov-report=html tests/`
**Parallel**: No (depends on all tests)

**Validation**:
- Overall coverage ≥80%
- Auth module coverage ≥90%
- No critical paths uncovered
- HTML report generated

---

## Phase 8: Polish & Documentation

**Goal**: Production readiness and documentation

**Independent Test Criteria**:
- ✅ All endpoints documented
- ✅ README updated with OAuth setup
- ✅ Environment variables documented
- ✅ Development mode instructions clear
- ✅ Deployment guide updated

### T041: Update README.md
**Description**: Add OAuth setup instructions
**File**: `README.md`
**Parallel**: Yes [P]

**Sections to Add**:
- OAuth 2.1 Authentication Setup
- Google Cloud Console configuration
- Environment variables (.env setup)
- Development mode instructions
- Testing with OAuth flow

**Validation**: README complete and accurate

---

### T042: Create OAUTH_SETUP.md
**Description**: Detailed OAuth setup guide
**File**: `docs/OAUTH_SETUP.md` (new)
**Parallel**: Yes [P]

**Contents**:
- Google Cloud Platform project setup
- OAuth 2.0 credentials configuration
- Redirect URIs for different environments
- Dynamic Client Registration setup
- Testing OAuth locally
- Troubleshooting common issues

**Validation**: Setup guide comprehensive

---

### T043: Update deployment guide
**Description**: Add OAuth configuration to deployment docs
**File**: `SETUP_GUIDE.md` (modify existing)
**Parallel**: Yes [P]

**Changes**:
- Phase 2 deployment with OAuth
- Environment variables for Cloud Run
- OAuth redirect URI configuration
- Secret Manager setup for credentials
- Token encryption key rotation

**Validation**: Deployment guide updated

---

## Summary

### Task Breakdown by Phase

| Phase | Task Count | Estimated Time | Parallel Tasks |
|-------|-----------|----------------|----------------|
| 1: Setup | 4 tasks | 1-2 hours | 2 tasks |
| 2: Foundational | 8 tasks | 3-4 hours | 3 tasks |
| 3: Core OAuth Flow | 10 tasks | 6-8 hours | 4 tasks |
| 4: MCP Integration Testing | 4 tasks | 2-3 hours | 2 tasks |
| 5: Dynamic Client Registration | 4 tasks | 2-3 hours | 3 tasks |
| 6: Error Handling | 4 tasks | 1-2 hours | 3 tasks |
| 7: Testing | 6 tasks | 3-4 hours | 4 tasks |
| 8: Polish & Documentation | 3 tasks | 1-2 hours | 3 tasks |
| **TOTAL** | **43 tasks** | **19-27 hours** | **24 parallel** |

### Dependency Graph

```
Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3+ (All implementation phases)
                                         ↓
                                    Phase 7 (Testing)
                                         ↓
                                    Phase 8 (Polish)
```

### Parallel Execution Opportunities

**Within Phase 3** (Core OAuth Flow):
- T014 (user_service) || T015 (session_service) || T018 (token_refresh)
- T022 (register router) can run parallel to implementation tasks

**Within Phase 4** (MCP Integration):
- T024 (auth tests) || T025 (refresh tests) || T026 (isolation tests)

**Within Phase 5** (Dynamic Client):
- T028 (client_service) || T029 (client_tests) || T030 (cleanup_job)

**Within Phase 7** (Testing):
- All unit tests can run in parallel (T035-T037, T039)

### MVP Scope

**Minimum Viable Product** (Scenarios 1, 2, 3):
- Phase 1: Setup (4 tasks)
- Phase 2: Foundational (8 tasks)
- Phase 3: Core OAuth Flow (10 tasks)
- Phase 4: MCP Integration Testing (4 tasks)

**Total MVP**: 26 tasks, 12-17 hours (1.5-2 days)

**Delivers**:
- ✅ Web-based OAuth authentication
- ✅ User data isolation
- ✅ Token refresh
- ✅ MCP authentication integration

**Deferred to Post-MVP**:
- Dynamic Client Registration (mobile/desktop)
- Advanced error handling
- Comprehensive testing
- Documentation

---

## Implementation Checklist

Before starting implementation:
- [ ] All design artifacts reviewed (spec.md, plan.md, data-model.md, contracts/)
- [ ] Tech stack validated (tech-stack.md v1.1.0)
- [ ] Development environment set up (.env configured)
- [ ] Google Cloud Console OAuth credentials created

During implementation:
- [ ] Run tests after each phase
- [ ] Commit after each completed task
- [ ] Update task status (mark completed with ✅)
- [ ] Review security implications of each change

After implementation:
- [ ] All tests passing
- [ ] Code coverage ≥80%
- [ ] OAuth flow tested end-to-end
- [ ] User data isolation validated
- [ ] Documentation updated
- [ ] Ready for `/specswarm:ship`

---

**Status**: ✅ TASKS READY FOR IMPLEMENTATION

**Next Step**: Begin Phase 1 (Setup) or run `/specswarm:implement` to execute all tasks
