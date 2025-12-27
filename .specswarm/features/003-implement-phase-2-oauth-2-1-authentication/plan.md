# Implementation Plan: OAuth 2.1 Authentication

**Feature**: 003 - OAuth 2.1 Authentication with Google
**Created**: 2025-12-26
**Status**: Planning Complete
**Parent Branch**: main

---

## Plan Overview

This plan outlines the implementation strategy for adding OAuth 2.1 authentication with Google to the Task Manager MCP Server. The feature replaces Phase 1 mock authentication (`user_id = "dev-user"`) with production-ready OAuth supporting web, mobile, and desktop clients through Dynamic Client Registration.

**Estimated Effort**: 1-2 days (as specified in PROJECT_SPEC.md)

**Success Criteria**:
- 100% of tool calls verify valid OAuth 2.1 token
- Zero cross-user data leakage
- OAuth flow completes in <10 seconds
- Sessions survive server restarts
- All error scenarios recoverable by users

---

## Tech Stack Compliance Report

### ✅ Approved Technologies

All technologies for this feature have been validated against `.specswarm/tech-stack.md v1.1.0`:

| Technology | Version | Status | Notes |
|------------|---------|--------|-------|
| google-auth | 2.35.0+ | ✅ APPROVED | Updated from v2.23.4+ (MINOR version bump) |
| google-auth-oauthlib | 1.2.0+ | ✅ AUTO-ADDED | No conflicts, MINOR version bump |
| cryptography | 44.0.0+ | ✅ APPROVED | Already in stack (implied by python-jose) |
| python-jose[cryptography] | 3.3.0+ | ✅ APPROVED | Retained for future features |

### ➕ New Technologies (Auto-Added)

**google-auth-oauthlib v1.2.0+**:
- **Purpose**: OAuth 2.1 authorization code flow helpers
- **Justification**: Simplifies Google OAuth implementation, handles PKCE for mobile clients
- **Integration**: Works seamlessly with google-auth library
- **Impact**: Reduces implementation complexity, official Google library
- **Added to**: Authentication section of tech-stack.md
- **Version Bump**: tech-stack.md v1.0.0 → v1.1.0 (MINOR)

### ⚠️ Resolved Conflicts

**pyjwt library (originally in spec.md)**:
- **Status**: ❌ REMOVED from spec dependencies
- **Conflict**: Redundant with python-jose (both handle JWT)
- **Resolution**: Option A selected - Keep python-jose, remove pyjwt
- **Rationale**:
  - google-auth provides native JWT validation via `google.auth.jwt` module
  - Database-backed sessions (not JWT sessions) - no custom JWT creation needed
  - python-jose already in stack - available for future features (API keys, webhooks)
  - Cleaner dependency management (one JWT library, not two)
- **Research**: See research.md "Finding 1: JWT Token Validation Strategy"

### 📊 Tech Stack Validation Summary

**Total Technologies**: 4 required
**Approved**: 3 (google-auth, cryptography, python-jose)
**Auto-Added**: 1 (google-auth-oauthlib)
**Conflicts**: 1 resolved (pyjwt removed)
**Prohibited**: 0 violations

**Tech Stack Compliance**: ✅ 100% COMPLIANT

---

## Technical Context

### Architecture Overview

OAuth 2.1 authentication integrates into the existing Task Manager MCP Server architecture:

```
┌─────────────────────────────────────────────────────────────┐
│  Claude.ai / Claude Mobile / Claude Code (Clients)          │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP + OAuth Bearer Token
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Application Layer                                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Auth Middleware (Token Validation)                     ││
│  │  - Validate OAuth token with google-auth                ││
│  │  - Extract user_id from token                          ││
│  │  - Load/extend session from database                   ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │  MCP Handler (tools/call)                               ││
│  │  - Requires authenticated user_id                       ││
│  │  - User-isolated task operations                        ││
│  └─────────────────────────────────────────────────────────┘│
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Business Logic Layer (TaskService)                          │
│  - All operations filter by user_id                          │
│  - User data isolation enforced                              │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Data Layer (SQLAlchemy + PostgreSQL/SQLite)                 │
│  ┌───────────┐  ┌───────────┐  ┌──────────────────┐        │
│  │   User    │  │  Session  │  │  DynamicClient   │        │
│  │  Table    │  │   Table   │  │     Table        │        │
│  └───────────┘  └───────────┘  └──────────────────┘        │
│  ┌───────────┐                                               │
│  │   Task    │  (existing, add user_id FK)                  │
│  │  Table    │                                               │
│  └───────────┘                                               │
└─────────────────────────────────────────────────────────────┘
```

### OAuth 2.1 Flow

**Authorization Code Grant with PKCE**:

1. **Authorization Request**:
   - User clicks "Authorize" in Claude interface
   - Server generates:
     - `state` (128-bit random, CSRF protection)
     - `code_verifier` (PKCE - 128-character random)
     - `code_challenge = BASE64URL(SHA256(code_verifier))`
   - Redirect to Google OAuth consent screen with:
     - `client_id`, `redirect_uri`, `response_type=code`
     - `scope=openid email profile`
     - `state`, `code_challenge`, `code_challenge_method=S256`

2. **User Consent**:
   - User signs into Google (if not already)
   - Reviews permissions request
   - Clicks "Allow"

3. **Authorization Callback**:
   - Google redirects to server callback URL with:
     - `code` (authorization code)
     - `state` (must match original request)
   - Server validates `state` parameter
   - Server exchanges `code` for tokens:
     - POST to Google token endpoint with:
       - `code`, `client_id`, `client_secret`
       - `redirect_uri`, `code_verifier` (PKCE)
     - Receives:
       - `access_token` (1-hour expiry)
       - `refresh_token` (valid until revoked)
       - `id_token` (Google ID token with user info)

4. **Session Creation**:
   - Validate `id_token` with google-auth library
   - Extract user claims: `sub` (user ID), `email`, `name`
   - Create/update User record in database
   - Generate cryptographically random `session_id`
   - Encrypt `access_token` and `refresh_token` (AES-256)
   - Store Session record with encrypted tokens
   - Return `session_id` to client (MCP-Session-Id header)

5. **Subsequent Requests**:
   - Client includes `session_id` in MCP-Session-Id header
   - Auth middleware:
     - Loads Session from database
     - Decrypts `access_token`
     - Validates token hasn't expired
     - If expired:
       - Uses `refresh_token` to get new `access_token`
       - Encrypts and saves new token
       - Google rotates refresh_token (single-use)
     - Loads User record
     - Injects `user_id` into request context

### Token Refresh Flow

**Automatic Transparent Refresh**:

```python
# Pseudo-code for token validation middleware
async def validate_token(session_id: str) -> str:
    session = await db.get_session(session_id)
    access_token = decrypt(session.access_token)

    # Check expiration
    if session.expires_at < datetime.now(UTC):
        # Token expired - refresh automatically
        refresh_token = decrypt(session.refresh_token)

        new_tokens = await google_oauth.refresh(refresh_token)

        # Update session with new tokens
        session.access_token = encrypt(new_tokens.access_token)
        session.refresh_token = encrypt(new_tokens.refresh_token)
        session.expires_at = datetime.now(UTC) + timedelta(hours=1)
        await db.update_session(session)

        access_token = new_tokens.access_token

    # Validate token with Google
    idinfo = id_token.verify_oauth2_token(
        access_token,
        google_requests.Request(),
        GOOGLE_CLIENT_ID
    )

    return idinfo['sub']  # Return user_id
```

**User Experience**: Completely transparent - user never sees token expiration

### Dynamic Client Registration

**For Mobile/Desktop Clients**:

Mobile and desktop apps cannot securely embed OAuth client credentials (public clients). Dynamic Client Registration (RFC 7591) allows on-demand credential generation:

1. **Registration Request**:
   ```http
   POST /oauth/register
   Content-Type: application/json

   {
     "platform": "ios",
     "redirect_uris": ["myapp://oauth/callback"],
     "client_name": "Task Manager iOS"
   }
   ```

2. **Server Response**:
   ```json
   {
     "client_id": "550e8400-e29b-41d4-a716-446655440000",
     "client_secret": "ZmQ0NGViMzY3NTE0MTBlYmE0Zjg1ZDljOGIxZjQwNDY=",
     "expires_at": 1735564800,
     "redirect_uris": ["myapp://oauth/callback"]
   }
   ```

3. **Client Storage**:
   - Client stores credentials securely (platform keychain/keystore)
   - Uses credentials for standard OAuth flow
   - Includes PKCE (mandatory for public clients)

4. **Credential Lifecycle**:
   - 30-day expiration if unused
   - Clients can re-register if expired
   - Server tracks last_used timestamp

### Session Management

**Database-Backed Sessions** (NOT JWT sessions):

**Rationale**:
- Enables session revocation (logout, token revoked)
- Audit trail (created_at, last_activity)
- Survives server restarts (persistent storage)
- Token refresh tracking
- User activity monitoring

**Session Lifecycle**:
1. Created on first OAuth authentication
2. Extended on every request (sliding window)
3. Expires after 24 hours of inactivity
4. Explicitly cleared on logout
5. Invalidated if Google revokes access

**Concurrent Sessions**:
- Users can have multiple active sessions (different devices)
- Maximum 10 concurrent sessions per user
- Oldest session auto-expired when limit reached

### Security Considerations

**Token Storage**:
- All OAuth tokens encrypted at rest (AES-256)
- Encryption key stored in environment variable `ENCRYPTION_KEY`
- Never log tokens or include in error messages

**CSRF Protection**:
- `state` parameter validated on OAuth callback
- Cryptographically random (128-bit minimum)
- Single-use (invalidated after callback)

**PKCE (Mobile/Desktop)**:
- Mandatory for all Dynamic Client Registration flows
- Prevents authorization code interception
- SHA-256 code challenge method

**Rate Limiting**:
- 10 authentication requests/minute per IP
- Prevents brute-force attacks on OAuth endpoints

**User Data Isolation**:
- All Task queries filter by authenticated `user_id`
- Service layer enforces isolation (not just controllers)
- Zero cross-user data leakage tolerance

---

## Phase 0: Research (✅ COMPLETE)

All research completed and documented in `research.md`. Key findings:

1. ✅ JWT validation strategy clarified (native google-auth)
2. ✅ Session architecture decided (database-backed)
3. ✅ OAuth libraries selected (google-auth + google-auth-oauthlib)
4. ✅ Dynamic Client Registration approach validated (RFC 7591)
5. ✅ PKCE requirements confirmed (mandatory for mobile/desktop)

**Output**: research.md created with all decisions documented

---

## Phase 1: Design & Data Modeling

### Objective
Create comprehensive data models and API contracts for OAuth implementation.

### Tasks

#### T1.1: Create data-model.md
**Description**: Define database schema for User, Session, and DynamicClient entities

**Output**: data-model.md with:
- Entity definitions (fields, types, relationships)
- Indexes for performance
- Constraints (unique, foreign keys)
- Encryption requirements
- Migration strategy from Phase 1

**Acceptance Criteria**:
- All 3 entities fully specified
- Relationships mapped (User ← Session, User ← Task)
- Indexes defined for query performance
- Encryption noted for sensitive fields

#### T1.2: Generate OpenAPI contracts
**Description**: Define API endpoints for OAuth flow and Dynamic Client Registration

**Output**: `/contracts/oauth-api.yaml` with:
- `/oauth/authorize` (GET) - Initiate OAuth flow
- `/oauth/callback` (GET) - Handle authorization callback
- `/oauth/logout` (POST) - End user session
- `/oauth/register` (POST) - Dynamic Client Registration
- `/oauth/refresh` (POST) - Manual token refresh

**Acceptance Criteria**:
- All endpoints documented with request/response schemas
- Error responses defined
- Security requirements specified (HTTPS, rate limits)
- PKCE parameters included

#### T1.3: Design MCP authentication integration
**Description**: Define how OAuth integrates with existing MCP handlers

**Output**: `/contracts/mcp-auth-integration.md` with:
- Auth middleware flow diagram
- MCP method authentication requirements:
  - `initialize`: No auth required
  - `tools/list`: No auth required
  - `tools/call`: Auth required
- Error response formats for auth failures
- Session header specification (MCP-Session-Id)

**Acceptance Criteria**:
- Clear separation of authenticated/unauthenticated methods
- Error codes aligned with MCP spec
- Integration points with existing code identified

---

## Phase 2: Database Schema Implementation

### Objective
Implement database models and migrations for OAuth entities.

### Tasks

#### T2.1: Create User model
**File**: `app/db/models.py` (extend existing)

**Changes**:
```python
class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True)  # Google sub claim
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    tasks = relationship("Task", back_populates="user")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
```

**Acceptance Criteria**:
- Model defined with all fields from spec
- Relationship to Task established
- Relationship to Session established

#### T2.2: Create Session model
**File**: `app/db/models.py`

**Changes**:
```python
class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    access_token = Column(LargeBinary, nullable=False)  # Encrypted
    refresh_token = Column(LargeBinary, nullable=False)  # Encrypted
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    user_agent = Column(String, nullable=True)

    # Relationships
    user = relationship("User", back_populates="sessions")

    # Indexes
    __table_args__ = (
        Index("idx_session_user_id", "user_id"),
        Index("idx_session_expires_at", "expires_at"),
    )
```

**Acceptance Criteria**:
- Encrypted token fields (LargeBinary type)
- Proper indexes for session lookup
- Cascade delete on user deletion

#### T2.3: Create DynamicClient model
**File**: `app/db/models.py`

**Changes**:
```python
class DynamicClient(Base):
    __tablename__ = "dynamic_clients"

    client_id = Column(String, primary_key=True)
    client_secret = Column(LargeBinary, nullable=False)  # Encrypted
    platform = Column(String, nullable=False)
    redirect_uris = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_used = Column(DateTime(timezone=True), nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_dynamic_client_expires_at", "expires_at"),
    )
```

**Acceptance Criteria**:
- JSON field for multiple redirect URIs
- Encrypted client_secret
- Expiration tracking

#### T2.4: Update Task model
**File**: `app/db/models.py` (modify existing)

**Changes**:
```python
class Task(Base):
    __tablename__ = "tasks"

    # ... existing fields ...

    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)  # Add FK

    # Add relationship
    user = relationship("User", back_populates="tasks")

    # Add index
    __table_args__ = (
        # ... existing indexes ...
        Index("idx_task_user_id", "user_id"),
    )
```

**Acceptance Criteria**:
- Foreign key to User table
- Index on user_id for query performance
- Existing Phase 1 tasks migrated to `user_id = "dev-user"`

#### T2.5: Create Alembic migration
**File**: `alembic/versions/002_add_oauth_tables.py`

**Changes**:
- Create users table
- Create sessions table
- Create dynamic_clients table
- Add user_id column to tasks table
- Add foreign key constraint
- Migrate existing tasks to dev-user

**Acceptance Criteria**:
- Migration reversible (downgrade script)
- Existing data preserved
- Indexes created
- Constraints enforced

---

## Phase 3: Token Encryption Service

### Objective
Implement secure token encryption/decryption for database storage.

### Tasks

#### T3.1: Create encryption utility
**File**: `app/auth/encryption.py` (new)

**Implementation**:
```python
from cryptography.fernet import Fernet
import base64
import os

class TokenEncryption:
    def __init__(self):
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            raise ValueError("ENCRYPTION_KEY environment variable required")
        self.fernet = Fernet(key.encode())

    def encrypt(self, token: str) -> bytes:
        """Encrypt OAuth token for database storage."""
        return self.fernet.encrypt(token.encode())

    def decrypt(self, encrypted: bytes) -> str:
        """Decrypt OAuth token from database."""
        return self.fernet.decrypt(encrypted).decode()
```

**Acceptance Criteria**:
- Uses cryptography library (AES-256)
- Environment variable for encryption key
- Clear error if key missing
- Type hints for all methods

#### T3.2: Add encryption to Session operations
**File**: `app/services/session_service.py` (new)

**Implementation**:
- create_session(): Encrypt tokens before saving
- get_session(): Decrypt tokens after loading
- refresh_session(): Re-encrypt new tokens

**Acceptance Criteria**:
- All token operations use encryption
- Decrypted tokens never logged
- Session service fully isolated

---

## Phase 4: OAuth Flow Implementation

### Objective
Implement OAuth authorization code flow with Google.

### Tasks

#### T4.1: Create OAuth configuration
**File**: `app/config/oauth.py` (new)

**Implementation**:
```python
from google_auth_oauthlib.flow import Flow
import os

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI")

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

def create_oauth_flow():
    """Create Google OAuth flow instance."""
    return Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=OAUTH_REDIRECT_URI,
    )
```

**Acceptance Criteria**:
- Environment variables validated
- OAuth scopes minimal (email + profile only)
- Flow reusable across endpoints

#### T4.2: Implement /oauth/authorize endpoint
**File**: `app/api/oauth.py` (new)

**Implementation**:
```python
@router.get("/oauth/authorize")
async def authorize():
    """Initiate OAuth authorization flow."""
    flow = create_oauth_flow()

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Generate PKCE parameters
    code_verifier = secrets.token_urlsafe(96)
    flow.code_verifier = code_verifier

    # Store state and code_verifier in temporary storage
    # (Redis recommended, or database with expiration)
    await store_oauth_state(state, code_verifier)

    # Generate authorization URL
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        state=state,
        include_granted_scopes="true",
        prompt="consent",
    )

    return {"authorization_url": authorization_url}
```

**Acceptance Criteria**:
- CSRF state parameter generated
- PKCE code_verifier generated and stored
- Authorization URL returned
- Temporary state storage implemented

#### T4.3: Implement /oauth/callback endpoint
**File**: `app/api/oauth.py`

**Implementation**:
```python
@router.get("/oauth/callback")
async def callback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """Handle OAuth authorization callback."""
    # Validate state parameter
    stored_verifier = await get_oauth_state(state)
    if not stored_verifier:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    # Exchange code for tokens
    flow = create_oauth_flow()
    flow.code_verifier = stored_verifier
    flow.fetch_token(code=code)

    credentials = flow.credentials

    # Validate ID token
    idinfo = id_token.verify_oauth2_token(
        credentials.id_token,
        google_requests.Request(),
        GOOGLE_CLIENT_ID
    )

    # Create or update user
    user = await upsert_user(
        db,
        user_id=idinfo["sub"],
        email=idinfo["email"],
        name=idinfo.get("name")
    )

    # Create session
    session = await create_session(
        db,
        user_id=user.user_id,
        access_token=credentials.token,
        refresh_token=credentials.refresh_token,
        expires_at=credentials.expiry
    )

    # Delete temporary state
    await delete_oauth_state(state)

    return {
        "session_id": session.session_id,
        "user_email": user.email
    }
```

**Acceptance Criteria**:
- State validation prevents CSRF
- PKCE code_verifier used in token exchange
- ID token validated with google-auth
- User created/updated
- Session created with encrypted tokens
- State cleaned up after use

#### T4.4: Implement token refresh logic
**File**: `app/services/session_service.py`

**Implementation**:
```python
async def refresh_session_tokens(
    db: Session,
    session: models.Session
) -> models.Session:
    """Refresh expired access token using refresh token."""
    refresh_token = decrypt(session.refresh_token)

    # Use google-auth to refresh
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    credentials = Credentials(
        token=None,  # Expired
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
    )

    credentials.refresh(Request())

    # Update session with new tokens
    session.access_token = encrypt(credentials.token)

    # Google rotates refresh tokens (single-use)
    if credentials.refresh_token:
        session.refresh_token = encrypt(credentials.refresh_token)

    session.expires_at = credentials.expiry

    await db.commit()
    return session
```

**Acceptance Criteria**:
- Refresh token decrypted
- New tokens fetched from Google
- Rotated refresh token saved (if provided)
- Session updated in database

---

## Phase 5: MCP Authentication Middleware

### Objective
Integrate OAuth authentication with MCP request handling.

### Tasks

#### T5.1: Create auth middleware
**File**: `app/api/middleware.py` (new)

**Implementation**:
```python
async def authenticate_mcp_request(
    request: Request,
    db: Session = Depends(get_db)
) -> str:
    """
    Authenticate MCP request and return user_id.

    Raises:
        HTTPException: If authentication fails
    """
    # Check if method requires auth
    body = await request.json()
    method = body.get("method")

    # Unauthenticated methods
    if method in ["initialize", "tools/list"]:
        return None  # No auth required

    # Extract session_id from header
    session_id = request.headers.get("MCP-Session-Id")
    if not session_id:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "authentication_required",
                "message": "MCP-Session-Id header required for this method",
                "authorization_url": "/oauth/authorize"
            }
        )

    # Load session
    session = await get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")

    # Check token expiration
    if session.expires_at < datetime.now(UTC):
        # Auto-refresh
        session = await refresh_session_tokens(db, session)

    # Validate access token
    access_token = decrypt(session.access_token)
    try:
        idinfo = id_token.verify_oauth2_token(
            access_token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Token validation failed"
        )

    # Update last activity
    session.last_activity = datetime.now(UTC)
    await db.commit()

    return session.user_id
```

**Acceptance Criteria**:
- initialize/tools/list bypass auth
- tools/call requires valid session
- Expired tokens auto-refreshed
- Token validation with google-auth
- Session activity updated
- Clear error messages with auth URL

#### T5.2: Integrate middleware with MCP handler
**File**: `app/main.py` (modify existing)

**Changes**:
```python
@app.post("/")
async def mcp_handler(
    request: Request,
    db: Session = Depends(get_db),
    user_id: str = Depends(authenticate_mcp_request)
):
    """Handle MCP protocol requests."""
    body = await request.json()
    method = body.get("method")

    if method == "tools/call":
        # Inject user_id into tool call
        params = body.get("params", {})
        params["user_id"] = user_id

        result = await handle_tool_call(db, params)
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

    # ... existing initialize, tools/list handlers ...
```

**Acceptance Criteria**:
- Middleware applied to MCP handler
- user_id injected into tool calls
- Unauthenticated methods still work

#### T5.3: Update TaskService for user isolation
**File**: `app/services/task_service.py` (modify existing)

**Changes**:
- Add `user_id: str` parameter to ALL methods
- Filter all queries by user_id:
  ```python
  query = select(Task).where(Task.user_id == user_id)
  ```
- Update create operations to set user_id
- Remove hardcoded `user_id = "dev-user"`

**Acceptance Criteria**:
- All methods require user_id parameter
- All database queries filter by user_id
- No global user context (dependency injection only)

---

## Phase 6: Dynamic Client Registration

### Objective
Implement RFC 7591 Dynamic Client Registration for mobile/desktop clients.

### Tasks

#### T6.1: Implement /oauth/register endpoint
**File**: `app/api/oauth.py`

**Implementation**:
```python
@router.post("/oauth/register")
async def register_client(
    registration: ClientRegistration,
    db: Session = Depends(get_db)
):
    """Register dynamic OAuth client."""
    # Generate credentials
    client_id = str(uuid.uuid4())
    client_secret = secrets.token_urlsafe(32)

    # Validate redirect URIs
    for uri in registration.redirect_uris:
        if not uri.startswith(("http://", "https://", "myapp://")):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid redirect URI: {uri}"
            )

    # Create dynamic client
    client = models.DynamicClient(
        client_id=client_id,
        client_secret=encrypt(client_secret),
        platform=registration.platform,
        redirect_uris=registration.redirect_uris,
        expires_at=datetime.now(UTC) + timedelta(days=30)
    )

    db.add(client)
    await db.commit()

    return {
        "client_id": client_id,
        "client_secret": client_secret,  # Only time secret is returned
        "expires_at": client.expires_at.isoformat(),
        "redirect_uris": registration.redirect_uris
    }
```

**Acceptance Criteria**:
- UUID-based client_id
- Secure client_secret generation
- Redirect URI validation
- 30-day expiration
- Secret encrypted in database

#### T6.2: Add cleanup job for expired clients
**File**: `app/tasks/cleanup.py` (new)

**Implementation**:
```python
async def cleanup_expired_clients(db: Session):
    """Delete expired dynamic clients."""
    await db.execute(
        delete(DynamicClient).where(
            DynamicClient.expires_at < datetime.now(UTC)
        )
    )
    await db.commit()
```

**Acceptance Criteria**:
- Scheduled job (daily cron)
- Deletes clients past expiration
- Logs deletion count

---

## Phase 7: Error Handling & User Guidance

### Objective
Provide clear, actionable error messages for authentication failures.

### Tasks

#### T7.1: Define authentication error responses
**File**: `app/schemas/auth.py` (new)

**Implementation**:
```python
class AuthError(BaseModel):
    error: str  # "authentication_required", "token_expired", "access_revoked"
    message: str  # User-friendly explanation
    authorization_url: str  # Link to re-authorize

class TokenExpiredError(AuthError):
    error: Literal["token_expired"] = "token_expired"
    message: str = "Your session has expired. Please re-authorize."

class AccessRevokedError(AuthError):
    error: Literal["access_revoked"] = "access_revoked"
    message: str = "Access was revoked. Click here to re-authorize."
```

**Acceptance Criteria**:
- Distinct error types
- User-friendly messages
- Authorization URL included
- MCP error code format

#### T7.2: Implement error logging
**File**: `app/auth/middleware.py`

**Changes**:
- Log all auth failures with:
  - user_id (if available)
  - timestamp
  - error type
  - request path
- **Never log tokens** (redact in logs)

**Acceptance Criteria**:
- All auth errors logged
- Tokens redacted
- User_id included for debugging

---

## Phase 8: Testing

### Objective
Comprehensive test coverage for OAuth implementation.

### Tasks

#### T8.1: Unit tests for encryption
**File**: `tests/test_encryption.py` (new)

**Test Cases**:
- ✅ Encrypt/decrypt round-trip
- ✅ Different tokens produce different ciphertexts
- ✅ Invalid ciphertext raises error
- ✅ Missing encryption key raises error

#### T8.2: Unit tests for token refresh
**File**: `tests/test_session_service.py` (new)

**Test Cases**:
- ✅ Refresh with valid refresh_token
- ✅ Handle rotated refresh_token
- ✅ Fail on invalid refresh_token
- ✅ Update session expiration

#### T8.3: Integration tests for OAuth flow
**File**: `tests/test_oauth_flow.py` (new)

**Test Cases**:
- ✅ Full authorization code flow (mocked Google)
- ✅ State validation (reject invalid state)
- ✅ PKCE validation
- ✅ User creation on first auth
- ✅ Session creation with encrypted tokens

#### T8.4: Integration tests for MCP auth
**File**: `tests/test_mcp_auth.py` (new)

**Test Cases**:
- ✅ initialize method without auth
- ✅ tools/list method without auth
- ✅ tools/call method requires auth
- ✅ Invalid session_id returns 401
- ✅ Expired token auto-refreshes
- ✅ User data isolation (user A can't see user B's tasks)

#### T8.5: Security tests
**File**: `tests/test_auth_security.py` (new)

**Test Cases**:
- ✅ CSRF attack prevented (invalid state)
- ✅ Token interception prevented (PKCE)
- ✅ Cross-user data leakage prevented
- ✅ Tokens not logged in error responses
- ✅ Rate limiting enforced

---

## Implementation Phases Summary

| Phase | Tasks | Estimated Time | Dependencies |
|-------|-------|----------------|--------------|
| 0: Research | 5 findings | ✅ COMPLETE | None |
| 1: Design | 3 tasks | 2-3 hours | Phase 0 |
| 2: Database | 5 tasks | 3-4 hours | Phase 1 |
| 3: Encryption | 2 tasks | 1-2 hours | Phase 2 |
| 4: OAuth Flow | 4 tasks | 4-5 hours | Phase 3 |
| 5: MCP Integration | 3 tasks | 2-3 hours | Phase 4 |
| 6: Dynamic Clients | 2 tasks | 2-3 hours | Phase 4 |
| 7: Error Handling | 2 tasks | 1-2 hours | Phase 5 |
| 8: Testing | 5 tasks | 4-5 hours | All phases |

**Total Estimated Time**: 19-27 hours (2-3.5 days)

---

## Migration from Phase 1

### Current State
- Mock authentication with `user_id = "dev-user"` hardcoded
- All existing tasks associated with dev-user
- No User table
- No authentication required

### Migration Strategy

1. **Database Migration**:
   - Create User record for dev-user: `INSERT INTO users (user_id, email, name) VALUES ('dev-user', 'dev@example.com', 'Development User')`
   - Update all existing Task records: `UPDATE tasks SET user_id = 'dev-user'`
   - Add foreign key constraint
   - No data loss

2. **Code Migration**:
   - Remove hardcoded `user_id = "dev-user"` from `app/main.py:539`
   - Replace with: `user_id = Depends(authenticate_mcp_request)`
   - Update all TaskService methods to require user_id parameter

3. **Testing Migration**:
   - Update test fixtures to create User records
   - Pass user_id to all service methods
   - Test user isolation (create multiple test users)

4. **Breaking Changes**:
   - ⚠️ MCP clients must include OAuth token in tool calls
   - ⚠️ Direct API testing requires obtaining OAuth token first
   - ⚠️ Development mode requires valid Google OAuth credentials

5. **Development Workaround**:
   - For local testing without OAuth:
   - Add `DEVELOPMENT_MODE=true` environment variable
   - If enabled, auth middleware accepts `user_id` in request body
   - **Never enable in production**

---

## Environment Variables Required

Add to `.env`:

```bash
# OAuth Configuration
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
OAUTH_REDIRECT_URI=http://localhost:8000/oauth/callback

# Token Encryption
ENCRYPTION_KEY=your-32-byte-base64-encoded-key

# Development (optional)
DEVELOPMENT_MODE=false  # Set to true for local testing only
```

Generate encryption key:
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

---

## Quality Gates

Before marking this feature complete, verify:

- ✅ All tests passing (unit + integration)
- ✅ No regression in existing Phase 1 functionality
- ✅ Type checking passes (mypy)
- ✅ Linting passes (ruff)
- ✅ Code coverage ≥80%
- ✅ Security tests passing (CSRF, PKCE, data isolation)
- ✅ OAuth flow completes in <10 seconds
- ✅ Manual testing on all platforms (web, mobile simulator, desktop)

---

## Next Steps After Plan Approval

1. Review this plan with stakeholders
2. Clarify any ambiguities
3. Generate task breakdown (`tasks.md`)
4. Begin implementation with Phase 1 (Design)
5. Execute tasks sequentially or in parallel (where dependencies allow)
6. Quality validation after each phase
7. Final testing and deployment

---

## References

- **Spec**: [spec.md](./spec.md)
- **Research**: [research.md](./research.md)
- **Tech Stack**: [.specswarm/tech-stack.md](../../tech-stack.md)
- **OAuth 2.1 Specification**: https://oauth.net/2.1/
- **Google OAuth 2.0 Documentation**: https://developers.google.com/identity/protocols/oauth2
- **RFC 7591 - Dynamic Client Registration**: https://datatracker.ietf.org/doc/html/rfc7591
- **RFC 7636 - PKCE**: https://datatracker.ietf.org/doc/html/rfc7636
- **MCP Authentication**: https://spec.modelcontextprotocol.io/specification/architecture/#authentication

---

**Planning Status**: ✅ COMPLETE - Ready for task generation
