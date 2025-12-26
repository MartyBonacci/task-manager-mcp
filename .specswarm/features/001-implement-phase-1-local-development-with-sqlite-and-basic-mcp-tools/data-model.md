# Data Model: Phase 1 Local Development

**Feature**: 001-implement-phase-1-local-development-with-sqlite-and-basic-mcp-tools
**Created**: 2025-12-25
**Database**: SQLite (Phase 1), PostgreSQL (Phase 3+)

---

## Overview

This data model defines the database schema for Phase 1 of the Task Manager MCP Server. It establishes two primary entities (Task and User) with a one-to-many relationship, designed for local development with SQLite but portable to PostgreSQL for production deployment.

**Design Principles**:
- User isolation enforced at database level (all queries filter by user_id)
- Proper indexing for query performance
- Timestamp tracking for audit trail
- Simple schema suitable for SQLite and PostgreSQL

---

## Entities

### Task

**Purpose**: Represents a single actionable item to be completed by a user

**Table Name**: `tasks`

**Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique task identifier |
| `user_id` | TEXT | NOT NULL, INDEXED | Owner of the task (FK to users.user_id) |
| `title` | TEXT | NOT NULL | Task title (1-500 characters) |
| `project` | TEXT | NULL, INDEXED | Project/category for organization |
| `priority` | INTEGER | NOT NULL, DEFAULT 3 | Priority level (1=Someday, 2=Low, 3=Medium, 4=High, 5=Critical) |
| `energy` | TEXT | NOT NULL, DEFAULT 'medium' | Energy level required (light \| medium \| deep) |
| `time_estimate` | TEXT | NOT NULL, DEFAULT '1hr' | Estimated time to complete (e.g., "1hr", "30min", "2hr") |
| `notes` | TEXT | NULL | Additional task notes/description |
| `due_date` | TEXT | NULL, INDEXED | Due date (ISO 8601 format) |
| `completed` | BOOLEAN | NOT NULL, DEFAULT 0, INDEXED | Task completion status |
| `completed_at` | TEXT | NULL | Timestamp when task was completed (ISO 8601) |
| `created_at` | TEXT | NOT NULL | Creation timestamp (ISO 8601, auto-generated) |
| `updated_at` | TEXT | NOT NULL | Last update timestamp (ISO 8601, auto-updated) |

**Indexes**:
```sql
CREATE INDEX idx_user_id ON tasks(user_id);
CREATE INDEX idx_completed ON tasks(completed);
CREATE INDEX idx_priority ON tasks(priority);
CREATE INDEX idx_due_date ON tasks(due_date);
CREATE INDEX idx_project ON tasks(project);
```

**Validation Rules**:
- `title`: Required, 1-500 characters
- `priority`: Must be 1, 2, 3, 4, or 5
- `energy`: Must be "light", "medium", or "deep"
- `user_id`: Required, must match authenticated user
- `completed_at`: Can only be set if `completed = true`

**Business Rules**:
- All queries MUST filter by `user_id` (user isolation)
- Cannot update a task owned by a different user
- When `completed` is set to true, `completed_at` must be set to current timestamp
- `updated_at` automatically updated on any field change
- `created_at` immutable after creation

**State Transitions**:
```
[New] --create_task()--> [Active: completed=false]
                              |
                              |--update_task()--> [Active: completed=false]
                              |
                              |--complete_task()--> [Completed: completed=true, completed_at set]
                              |
                              |--delete_task()--> [Deleted]
```

**Example SQLite Schema**:
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    project TEXT,
    priority INTEGER DEFAULT 3,
    energy TEXT DEFAULT 'medium',
    time_estimate TEXT DEFAULT '1hr',
    notes TEXT,
    due_date TEXT,
    completed BOOLEAN DEFAULT 0,
    completed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### User

**Purpose**: Represents a system user (prepared for Phase 2 OAuth integration)

**Table Name**: `users`

**Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `user_id` | TEXT | PRIMARY KEY | Unique user identifier (from OAuth in Phase 2) |
| `email` | TEXT | UNIQUE | User's email address |
| `preferences` | TEXT | NULL | User preferences (JSON blob) |
| `created_at` | TEXT | NOT NULL | Account creation timestamp (ISO 8601) |

**Indexes**:
```sql
CREATE UNIQUE INDEX idx_user_email ON users(email);
```

**Phase 1 Note**:
- Single hardcoded user: `user_id = "dev-user"`
- No actual user records created in Phase 1
- Full implementation in Phase 2 with OAuth 2.1

**Example SQLite Schema**:
```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    email TEXT UNIQUE,
    preferences TEXT,
    created_at TEXT NOT NULL
);
```

---

## Relationships

### User → Tasks (One-to-Many)

**Relationship**: One user has many tasks

**Foreign Key**: `tasks.user_id` → `users.user_id`

**Cascade Behavior** (Phase 2+):
- ON DELETE: CASCADE (deleting user deletes all their tasks)
- ON UPDATE: CASCADE (updating user_id updates all task references)

**Phase 1 Note**:
- Relationship exists logically but not enforced with FK constraint
- All tasks have `user_id = "dev-user"`
- FK constraint added in Phase 2 when real users exist

**Query Pattern**:
```python
# Get all tasks for a user
tasks = db.query(Task).filter(Task.user_id == user_id).all()

# Get incomplete tasks for a user
tasks = db.query(Task).filter(
    Task.user_id == user_id,
    Task.completed == False
).all()
```

---

## Data Types and Formats

### Timestamps (created_at, updated_at, completed_at, due_date)

**Format**: ISO 8601 with timezone
**Example**: `"2025-12-25T12:00:00Z"` or `"2025-12-25T12:00:00-07:00"`

**SQLAlchemy Handling**:
```python
from datetime import datetime

# Auto-set on creation
created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

# Auto-update on modification
updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Priority (Integer 1-5)

**Mapping**:
- 1: Someday
- 2: Low
- 3: Medium (default)
- 4: High
- 5: Critical

**Storage**: Integer for efficient sorting and comparison

**Display**: Map to labels in application layer, not database

### Energy (String Enum)

**Values**:
- "light": Quick task, minimal focus required
- "medium": Normal cognitive load (default)
- "deep": Requires sustained focus

**Storage**: String for readability

**Validation**: Enforced in Pydantic schema and application logic

### Time Estimate (String)

**Format**: Free-form string (e.g., "30min", "1hr", "2hr", "4hr+")

**Phase 1 Note**: No strict format validation, accepts any string

**Future Enhancement**: Parse to minutes for analytics and scheduling

### Preferences (JSON Blob)

**Format**: JSON string

**Example**:
```json
{
  "default_priority": 3,
  "default_energy": "medium",
  "default_project": "Personal",
  "sort_order": "priority_desc"
}
```

**Phase 1 Note**: Not used in Phase 1, prepared for Phase 2 user customization

---

## Query Patterns

### Common Queries

**1. List all incomplete tasks for a user (sorted by priority)**
```sql
SELECT * FROM tasks
WHERE user_id = ? AND completed = 0
ORDER BY priority DESC, created_at ASC;
```

**2. Get tasks by project**
```sql
SELECT * FROM tasks
WHERE user_id = ? AND project = ? AND completed = 0
ORDER BY priority DESC, created_at ASC;
```

**3. Search tasks by keywords**
```sql
SELECT * FROM tasks
WHERE user_id = ?
  AND (title LIKE ? OR notes LIKE ?)
ORDER BY priority DESC, created_at ASC;
```

**4. Get task statistics**
```sql
-- Count by project
SELECT project, COUNT(*) as count
FROM tasks
WHERE user_id = ? AND completed = 0
GROUP BY project;

-- Count by priority
SELECT priority, COUNT(*) as count
FROM tasks
WHERE user_id = ? AND completed = 0
GROUP BY priority;

-- Completion rate
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed,
    ROUND(SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as completion_rate
FROM tasks
WHERE user_id = ?;
```

### SQLAlchemy Query Patterns

**1. Create task**
```python
task = Task(
    user_id=user_id,
    title=task_data.title,
    project=task_data.project,
    priority=task_data.priority,
    ...
)
db.add(task)
await db.commit()
await db.refresh(task)
```

**2. List with filters**
```python
query = select(Task).filter(Task.user_id == user_id)

if not show_completed:
    query = query.filter(Task.completed == False)

if project:
    query = query.filter(Task.project == project)

if priority:
    query = query.filter(Task.priority == priority)

query = query.order_by(Task.priority.desc(), Task.created_at)

result = await db.execute(query)
tasks = result.scalars().all()
```

**3. Update task**
```python
result = await db.execute(
    select(Task).filter(Task.id == task_id, Task.user_id == user_id)
)
task = result.scalar_one_or_none()

if task:
    for field, value in update_data.items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
```

**4. Delete task**
```python
result = await db.execute(
    delete(Task).filter(Task.id == task_id, Task.user_id == user_id)
)
await db.commit()
return result.rowcount > 0
```

---

## Database Initialization

### SQLite Setup (Phase 1)

**File Location**: `./tasks.db` (project root, gitignored)

**Initialization**:
```python
from sqlalchemy import create_engine
from .models import Base

def init_db():
    """Initialize database tables"""
    engine = create_engine(
        "sqlite:///./tasks.db",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
```

**First Run**:
- Database file created automatically
- Tables created on first `init_db()` call
- No migrations needed (schema is final for Phase 1)

### PostgreSQL Setup (Phase 3+)

**Migration Path**:
1. Export SQLite data to JSON/CSV
2. Create PostgreSQL database
3. Update DATABASE_URL environment variable
4. Run Alembic migrations
5. Import data to PostgreSQL
6. Verify data integrity

**Connection String**:
```
postgresql://username:password@host:port/database
```

---

## Performance Considerations

### Index Strategy

**User Isolation** (`idx_user_id`):
- Most critical index
- Every query filters by user_id
- High selectivity (unique users)

**Completion Status** (`idx_completed`):
- Common filter (list incomplete tasks)
- Boolean index (low selectivity, but useful with user_id)

**Priority** (`idx_priority`):
- Used for sorting
- Composite index with user_id could improve performance

**Project** (`idx_project`):
- Filters by project category
- Variable selectivity (depends on number of projects)

**Due Date** (`idx_due_date`):
- Future feature (Phase 2 calendar integration)
- Useful for scheduling and overdue task queries

### Query Optimization

**Pagination**:
```python
query = query.limit(limit).offset(offset)
```

**Limit Results**:
- Default: 100 tasks per query
- Maximum: 1000 tasks (prevent performance issues)

**Covering Indexes** (Future):
- Composite indexes covering frequently queried columns
- Example: `(user_id, completed, priority)`

---

## Data Migration

### Phase 1 → Phase 2 (OAuth)

**Changes**:
- Replace `user_id = "dev-user"` with real OAuth user IDs
- Populate `users` table with real user data
- Add foreign key constraint `tasks.user_id → users.user_id`

**Migration Script**:
```python
# Create real user record
user = User(
    user_id="oauth-user-id",
    email="user@example.com",
    created_at=datetime.utcnow()
)
db.add(user)

# Update all dev-user tasks to new user_id
db.execute(
    update(Task)
    .filter(Task.user_id == "dev-user")
    .values(user_id="oauth-user-id")
)
db.commit()
```

### Phase 2 → Phase 3 (SQLite → PostgreSQL)

**Tools**: Alembic for schema migrations

**Steps**:
1. Create Alembic migration from SQLite schema
2. Apply migration to PostgreSQL database
3. Export SQLite data (pg_dump or custom script)
4. Import to PostgreSQL
5. Verify data integrity
6. Update DATABASE_URL
7. Test all queries

---

## Appendix

### Sample Data (Development/Testing)

```sql
-- Sample user (Phase 1)
INSERT INTO tasks (user_id, title, project, priority, energy, time_estimate, notes, completed, created_at, updated_at)
VALUES
    ('dev-user', 'Research MCP specification', 'Deep Dive Coding', 4, 'deep', '2hr', 'Focus on tool registration', 0, datetime('now'), datetime('now')),
    ('dev-user', 'Update LinkedIn profile', 'Personal', 2, 'light', '30min', NULL, 0, datetime('now'), datetime('now')),
    ('dev-user', 'Order sublimation printer', 'Custom Cult', 5, 'medium', '1hr', 'Research options first', 0, datetime('now'), datetime('now')),
    ('dev-user', 'Write unit tests', 'Deep Dive Coding', 4, 'deep', '3hr', 'TaskService tests', 1, datetime('now'), datetime('now'));
```

### Schema Evolution

**Version 1.0** (Phase 1): Current schema
**Version 1.1** (Phase 2): Add OAuth user fields, FK constraints
**Version 1.2** (Phase 2): Add `calendar_event_id` field for Google Calendar integration
**Version 1.3** (Phase 4): Add `actual_time_spent` for time tracking
**Version 2.0** (Phase 5): Add subtasks, dependencies, templates (breaking changes)
