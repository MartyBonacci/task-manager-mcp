# Data Model: OAuth 2.1 Authentication

**Feature**: 003 - OAuth 2.1 Authentication
**Created**: 2025-12-26
**Database**: SQLite (development) / PostgreSQL (production)
**ORM**: SQLAlchemy 2.0+ (async)

---

## Overview

This document defines the database schema for OAuth 2.1 authentication, including users, sessions, and dynamic client registration. All entities integrate with the existing Task Manager database schema.

---

## Entity Relationship Diagram

```
┌─────────────┐
│    User     │
│ (Primary)   │
└──────┬──────┘
       │
       │ 1:N
       ├──────────────┐
       │              │
       ▼              ▼
┌─────────────┐  ┌─────────────┐
│   Session   │  │    Task     │
│  (New)      │  │ (Existing)  │
└─────────────┘  └─────────────┘

┌──────────────────┐
│  DynamicClient   │
│  (Independent)   │
└──────────────────┘
```

**Relationships**:
- User → Session: One-to-Many (one user can have multiple active sessions)
- User → Task: One-to-Many (one user owns many tasks)
- DynamicClient: Standalone (no foreign keys)

---

## Entities

### 1. User

**Purpose**: Stores authenticated user information from Google OAuth

**Table Name**: `users`

#### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `user_id` | String(255) | PRIMARY KEY | Google user ID (sub claim from ID token) |
| `email` | String(320) | UNIQUE, NOT NULL | Google account email address |
| `name` | String(255) | NULLABLE | Display name from Google profile |
| `created_at` | DateTime(TZ) | NOT NULL, DEFAULT NOW() | First authentication timestamp |
| `last_login` | DateTime(TZ) | NOT NULL | Most recent authentication |

#### Indexes

```sql
CREATE INDEX idx_user_email ON users(email);
```

#### Relationships

- **sessions**: One-to-Many relationship with Session entity
  - Cascade: DELETE (when user deleted, delete all sessions)
- **tasks**: One-to-Many relationship with Task entity
  - Cascade: RESTRICT (cannot delete user with existing tasks)

#### Validation Rules

- `user_id`: Must be valid Google sub claim (alphanumeric, max 255 chars)
- `email`: Must be valid email format (RFC 5322)
- `name`: Optional, max 255 characters
- `created_at`: Immutable after creation
- `last_login`: Updated on every successful authentication

#### SQLAlchemy Model

```python
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.orm import relationship
from app.db.database import Base

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

---

### 2. Session

**Purpose**: Stores OAuth session state with encrypted tokens

**Table Name**: `sessions`

#### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `session_id` | String(43) | PRIMARY KEY | Cryptographically random session identifier (URL-safe base64, 32 bytes) |
| `user_id` | String(255) | FOREIGN KEY, NOT NULL | Reference to User.user_id |
| `access_token` | LargeBinary | NOT NULL | Encrypted Google OAuth access token (AES-256) |
| `refresh_token` | LargeBinary | NOT NULL | Encrypted Google OAuth refresh token (AES-256) |
| `expires_at` | DateTime(TZ) | NOT NULL | Access token expiration timestamp (typically 1 hour from issue) |
| `created_at` | DateTime(TZ) | NOT NULL, DEFAULT NOW() | Session creation timestamp |
| `last_activity` | DateTime(TZ) | NOT NULL, DEFAULT NOW() | Most recent request using this session |
| `user_agent` | String(500) | NULLABLE | Client User-Agent header for audit trail |

#### Indexes

```sql
CREATE INDEX idx_session_user_id ON sessions(user_id);
CREATE INDEX idx_session_expires_at ON sessions(expires_at);
CREATE INDEX idx_session_last_activity ON sessions(last_activity);
```

#### Foreign Keys

```sql
ALTER TABLE sessions ADD CONSTRAINT fk_session_user
  FOREIGN KEY (user_id) REFERENCES users(user_id)
  ON DELETE CASCADE;
```

#### Validation Rules

- `session_id`: Must be 43-character URL-safe base64 string (32 random bytes encoded)
- `user_id`: Must reference existing User record
- `access_token`: Encrypted with AES-256, max 512 bytes (encrypted token ~400 bytes)
- `refresh_token`: Encrypted with AES-256, max 512 bytes
- `expires_at`: Must be future timestamp at creation
- `last_activity`: Updated on every request using this session
- `user_agent`: Truncated to 500 chars if longer

#### Session Lifecycle

1. **Creation**: On successful OAuth callback
2. **Usage**: Loaded on every MCP tool call
3. **Refresh**: When `expires_at < now()`, auto-refresh using `refresh_token`
4. **Expiration**: Deleted when `last_activity < now() - 24 hours`
5. **Logout**: Explicitly deleted when user logs out
6. **Revocation**: Deleted when Google revokes access

#### Concurrency Rules

- Maximum 10 active sessions per user
- When limit reached, delete oldest session (by `created_at`)
- Sessions are independent (can be from different devices)

#### SQLAlchemy Model

```python
from sqlalchemy import Column, String, LargeBinary, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import relationship
from app.db.database import Base

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

---

### 3. DynamicClient

**Purpose**: Stores OAuth client credentials for mobile/desktop apps (RFC 7591)

**Table Name**: `dynamic_clients`

#### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `client_id` | String(36) | PRIMARY KEY | UUID v4 generated client identifier |
| `client_secret` | LargeBinary | NOT NULL | Encrypted client secret (AES-256, 32 random bytes) |
| `platform` | String(50) | NOT NULL | Client platform (ios, android, desktop, cli) |
| `redirect_uris` | JSON | NOT NULL | Array of allowed OAuth callback URIs |
| `created_at` | DateTime(TZ) | NOT NULL, DEFAULT NOW() | Client registration timestamp |
| `expires_at` | DateTime(TZ) | NOT NULL | Credential expiration (30 days from creation) |
| `last_used` | DateTime(TZ) | NULLABLE | Most recent OAuth flow using this client |

#### Indexes

```sql
CREATE INDEX idx_dynamic_client_expires_at ON dynamic_clients(expires_at);
CREATE INDEX idx_dynamic_client_platform ON dynamic_clients(platform);
```

#### Validation Rules

- `client_id`: Must be valid UUID v4 (36 chars with hyphens)
- `client_secret`: Encrypted with AES-256, max 512 bytes
- `platform`: Enum ['ios', 'android', 'macos', 'windows', 'linux', 'cli']
- `redirect_uris`: Array of 1-5 URIs, each must match pattern:
  - Web: `https://` or `http://localhost`
  - Mobile: `{app-scheme}://`
  - Desktop: `http://localhost:{port}/`
- `expires_at`: Exactly 30 days from `created_at`
- `last_used`: Updated when client credentials used in OAuth flow

#### Client Lifecycle

1. **Registration**: Client POSTs to `/oauth/register`
2. **Creation**: Server generates UUID + random secret, stores encrypted
3. **Usage**: Client includes credentials in OAuth flow (with PKCE)
4. **Tracking**: `last_used` updated on every OAuth flow
5. **Expiration**: Deleted when `expires_at < now()` (daily cleanup job)
6. **Re-registration**: Expired clients must re-register

#### Security Considerations

- `client_secret` **only returned ONCE** at registration
- Client must store secret securely (platform keychain/keystore)
- PKCE **mandatory** for all dynamic clients (public clients)
- No revocation mechanism (expiration only)

#### SQLAlchemy Model

```python
from sqlalchemy import Column, String, LargeBinary, DateTime, JSON, Index, func
from app.db.database import Base

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

---

## Modified Entities

### Task (Existing - Updated)

**Changes**: Add foreign key to User entity

#### New Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `user_id` | String(255) | FOREIGN KEY, NOT NULL | Owner of this task |

#### New Indexes

```sql
CREATE INDEX idx_task_user_id ON tasks(user_id);
```

#### New Foreign Keys

```sql
ALTER TABLE tasks ADD CONSTRAINT fk_task_user
  FOREIGN KEY (user_id) REFERENCES users(user_id)
  ON DELETE RESTRICT;
```

#### Migration Notes

- **Phase 1 tasks**: All existing tasks assigned to `user_id = 'dev-user'`
- **Dev user creation**: Create User record for 'dev-user' before migration
- **Constraint timing**: Add NOT NULL constraint AFTER data migration

#### Updated SQLAlchemy Model

```python
class Task(Base):
    __tablename__ = "tasks"

    # ... existing fields ...

    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="tasks")
```

---

## Database Migration Strategy

### Migration Order

1. **Create users table** (no dependencies)
2. **Create dev user record**: `INSERT INTO users (user_id, email, name, last_login) VALUES ('dev-user', 'dev@example.com', 'Development User', NOW())`
3. **Add user_id column to tasks** (nullable initially)
4. **Migrate existing tasks**: `UPDATE tasks SET user_id = 'dev-user'`
5. **Add NOT NULL constraint**: `ALTER TABLE tasks ALTER COLUMN user_id SET NOT NULL`
6. **Add foreign key constraint**: `ALTER TABLE tasks ADD CONSTRAINT fk_task_user ...`
7. **Create sessions table** (references users)
8. **Create dynamic_clients table** (no dependencies)

### Rollback Strategy

Reverse order:
1. Drop dynamic_clients table
2. Drop sessions table
3. Drop foreign key constraint from tasks
4. Drop user_id column from tasks
5. Drop users table

### Data Loss Prevention

- No existing data deleted
- All tasks preserved (migrated to dev-user)
- Constraint validation before final commit
- Test migration on copy of production database first

---

## Alembic Migration Script

**File**: `alembic/versions/002_add_oauth_tables.py`

```python
"""Add OAuth 2.1 authentication tables

Revision ID: 002
Revises: 001
Create Date: 2025-12-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime, timezone

# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('user_id', sa.String(255), primary_key=True),
        sa.Column('email', sa.String(320), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_user_email', 'users', ['email'])

    # Create dev user
    op.execute(
        f"""
        INSERT INTO users (user_id, email, name, last_login)
        VALUES ('dev-user', 'dev@example.com', 'Development User', '{datetime.now(timezone.utc).isoformat()}')
        """
    )

    # Add user_id to tasks (nullable initially)
    op.add_column('tasks', sa.Column('user_id', sa.String(255), nullable=True))

    # Migrate existing tasks to dev-user
    op.execute("UPDATE tasks SET user_id = 'dev-user'")

    # Make user_id NOT NULL
    op.alter_column('tasks', 'user_id', nullable=False)

    # Add foreign key and index
    op.create_foreign_key('fk_task_user', 'tasks', 'users', ['user_id'], ['user_id'], ondelete='RESTRICT')
    op.create_index('idx_task_user_id', 'tasks', ['user_id'])

    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('session_id', sa.String(43), primary_key=True),
        sa.Column('user_id', sa.String(255), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('access_token', sa.LargeBinary(512), nullable=False),
        sa.Column('refresh_token', sa.LargeBinary(512), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_activity', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('user_agent', sa.String(500), nullable=True),
    )
    op.create_index('idx_session_user_id', 'sessions', ['user_id'])
    op.create_index('idx_session_expires_at', 'sessions', ['expires_at'])
    op.create_index('idx_session_last_activity', 'sessions', ['last_activity'])

    # Create dynamic_clients table
    op.create_table(
        'dynamic_clients',
        sa.Column('client_id', sa.String(36), primary_key=True),
        sa.Column('client_secret', sa.LargeBinary(512), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('redirect_uris', sa.JSON, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_dynamic_client_expires_at', 'dynamic_clients', ['expires_at'])
    op.create_index('idx_dynamic_client_platform', 'dynamic_clients', ['platform'])

def downgrade():
    # Drop tables in reverse order
    op.drop_table('dynamic_clients')
    op.drop_table('sessions')

    # Remove foreign key and user_id from tasks
    op.drop_constraint('fk_task_user', 'tasks', type_='foreignkey')
    op.drop_index('idx_task_user_id', 'tasks')
    op.drop_column('tasks', 'user_id')

    # Drop users table
    op.drop_table('users')
```

---

## Query Patterns

### Common Queries

#### 1. Get User by Email
```python
user = await db.execute(
    select(User).where(User.email == email)
)
user = user.scalar_one_or_none()
```

#### 2. Get Active Sessions for User
```python
sessions = await db.execute(
    select(Session)
    .where(Session.user_id == user_id)
    .where(Session.last_activity > datetime.now(timezone.utc) - timedelta(hours=24))
    .order_by(Session.last_activity.desc())
)
sessions = sessions.scalars().all()
```

#### 3. Get User's Tasks
```python
tasks = await db.execute(
    select(Task)
    .where(Task.user_id == user_id)
    .where(Task.completed == False)
    .order_by(Task.priority.desc())
)
tasks = tasks.scalars().all()
```

#### 4. Clean Up Expired Sessions
```python
await db.execute(
    delete(Session)
    .where(Session.last_activity < datetime.now(timezone.utc) - timedelta(hours=24))
)
await db.commit()
```

#### 5. Clean Up Expired Dynamic Clients
```python
await db.execute(
    delete(DynamicClient)
    .where(DynamicClient.expires_at < datetime.now(timezone.utc))
)
await db.commit()
```

---

## Performance Considerations

### Index Strategy

**High-Priority Indexes** (frequently queried):
- `users.email` - Login lookup
- `sessions.user_id` - Session by user
- `sessions.expires_at` - Expiration cleanup
- `tasks.user_id` - User's tasks

**Medium-Priority Indexes**:
- `sessions.last_activity` - Activity-based expiration
- `dynamic_clients.expires_at` - Client cleanup

**Low-Priority** (rarely queried directly):
- `dynamic_clients.platform` - Analytics only

### Query Optimization

1. **Session Validation**: Use index on `session_id` (primary key - automatic)
2. **User Tasks**: Composite index on `(user_id, completed, priority)` for common filters
3. **Cleanup Jobs**: Indexes on timestamp fields for bulk deletes

### Connection Pooling

- **Development (SQLite)**: No pooling needed (file-based)
- **Production (PostgreSQL)**:
  - Pool size: 10 connections
  - Max overflow: 20 connections
  - Pool timeout: 30 seconds
  - Pool recycle: 3600 seconds (1 hour)

---

## Security Notes

1. **Token Encryption**: All OAuth tokens encrypted at rest (AES-256)
2. **No Plaintext Secrets**: Client secrets and tokens never stored unencrypted
3. **Foreign Key Constraints**: Prevent orphaned sessions and tasks
4. **Cascade Deletes**: Sessions deleted when user deleted (data cleanup)
5. **Restricted Deletes**: Tasks cannot be deleted if user still has tasks (data protection)

---

## Testing Considerations

### Test Fixtures

```python
@pytest_asyncio.fixture
async def test_user(db_session):
    """Create test user."""
    user = User(
        user_id="test-user-123",
        email="test@example.com",
        name="Test User",
        last_login=datetime.now(timezone.utc)
    )
    db_session.add(user)
    await db_session.commit()
    return user

@pytest_asyncio.fixture
async def test_session(db_session, test_user):
    """Create test session with encrypted tokens."""
    from app.auth.encryption import encrypt_token
    session = Session(
        session_id=secrets.token_urlsafe(32),
        user_id=test_user.user_id,
        access_token=encrypt_token("fake-access-token"),
        refresh_token=encrypt_token("fake-refresh-token"),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    db_session.add(session)
    await db_session.commit()
    return session
```

---

## Changelog

### 2025-12-26
- Initial data model created
- User, Session, DynamicClient entities defined
- Task entity updated with user_id foreign key
- Migration strategy documented
- Query patterns defined
- Performance considerations noted
