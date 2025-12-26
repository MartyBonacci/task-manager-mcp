# Task Manager MCP Server - Project Specification

## Overview

A production-grade Model Context Protocol (MCP) server that provides task management capabilities accessible from Claude.ai, Claude mobile app, and Claude Code. This server will enable conversational task management where users interact naturally with Claude, and Claude manages a persistent task database through MCP tools.

## Project Goals

1. **Conversational Task Management**: Users tell Claude what needs to be done, Claude manages everything
2. **Cross-Platform Access**: Works from web, mobile, and terminal
3. **Persistent Storage**: Tasks survive conversation boundaries
4. **Calendar Integration**: Can coordinate with Google Calendar for time blocking
5. **Production Quality**: Proper auth, error handling, monitoring, documentation
6. **Strategic Visibility**: Birds eye view dashboard for holistic task overview

## Core Features

### Task CRUD Operations

**Create Tasks**
- Title (required)
- Project/category (optional)
- Priority (1-5 scale: Someday, Low, Medium, High, Critical)
- Energy level (light, medium, deep)
- Time estimate (15min, 30min, 1hr, 2hr, 4hr+)
- Notes/description (optional)
- Due date (optional)
- Created timestamp (automatic)

**Read/Query Tasks**
- List all tasks
- Filter by: project, priority, completion status, energy level
- Search by keywords in title/notes
- Sort by: priority, created date, due date
- Paginated results for large task lists

**Update Tasks**
- Modify any field
- Add/update notes
- Change priority/energy/estimates
- Reschedule due dates

**Complete/Delete Tasks**
- Mark as complete (with completion timestamp)
- Soft delete (archive)
- Hard delete (permanent removal)
- Bulk operations

### Advanced Features

**Task Analytics**
- Count by project
- Count by priority
- Completion rate
- Time tracking (if implemented)
- Pattern recognition (tasks that get delayed)

**Calendar Integration** (Phase 2)
- Link tasks to calendar events
- Suggest scheduling based on available time
- Block calendar time for tasks
- Detect conflicts between tasks and meetings

**Context Awareness**
- Remember user preferences
- Suggest next task based on time available
- Identify overdue/neglected tasks
- Smart prioritization

**Birds Eye Dashboard** (Phase 5)
- Visual overview of all tasks
- Project Kanban board
- Timeline/calendar integration view
- Analytics and insights visualization
- Energy distribution charts
- Completion patterns and trends

## Technical Requirements

### MCP Protocol Compliance

**MCP Specification Version**: 2025-06-18

**Required Endpoints**:
- `HEAD /` - Protocol discovery
- `POST /` - All MCP methods (initialize, tools/list, tools/call)

**Required Headers**:
- `MCP-Protocol-Version: 2025-06-18`
- `Mcp-Session-Id` for session management
- `Content-Type: application/json`

**Authentication**:
- OAuth 2.1 with Dynamic Client Registration
- Selective authentication (initialize without token, tools require token)
- Secure token validation

### Data Storage

**Database**: SQLite (initial), PostgreSQL (production scale)

**Schema**:
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
    updated_at TEXT NOT NULL,
    calendar_event_id TEXT,  -- Link to Google Calendar event
    actual_time_spent INTEGER  -- For learning time estimates
);

CREATE INDEX idx_user_id ON tasks(user_id);
CREATE INDEX idx_completed ON tasks(completed);
CREATE INDEX idx_priority ON tasks(priority);
CREATE INDEX idx_due_date ON tasks(due_date);
CREATE INDEX idx_project ON tasks(project);
```

**User Management**:
```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    email TEXT,
    preferences TEXT, -- JSON blob
    created_at TEXT NOT NULL
);
```

**Analytics Tables** (Phase 5):
```sql
CREATE TABLE task_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    task_id INTEGER,
    event_type TEXT, -- created, completed, rescheduled, etc
    timestamp TEXT NOT NULL,
    metadata TEXT -- JSON blob for additional context
);
```

### API Design

**MCP Tools to Expose**:

1. `task_create`
   - Parameters: title, project?, priority?, energy?, time_estimate?, notes?, due_date?
   - Returns: Created task object

2. `task_list`
   - Parameters: filter_project?, filter_priority?, show_completed?, limit?, offset?
   - Returns: Array of task objects

3. `task_get`
   - Parameters: task_id
   - Returns: Single task object

4. `task_update`
   - Parameters: task_id, fields (object with updated values)
   - Returns: Updated task object

5. `task_complete`
   - Parameters: task_id
   - Returns: Updated task object

6. `task_delete`
   - Parameters: task_id, hard_delete?
   - Returns: Success confirmation

7. `task_search`
   - Parameters: query, fields? (title, notes, or both)
   - Returns: Array of matching tasks

8. `task_stats`
   - Parameters: group_by? (project, priority, status)
   - Returns: Analytics object

9. `task_schedule` (Phase 2)
   - Parameters: task_id, start_time, duration
   - Returns: Created calendar event + updated task

### Security Requirements

**Authentication**:
- OAuth 2.1 flows
- Dynamic Client Registration for mobile clients
- Token validation on every request
- User isolation (can only access own tasks)

**Data Protection**:
- Input validation and sanitization
- SQL injection prevention (parameterized queries)
- Rate limiting
- HTTPS only

**Privacy**:
- No logging of task content
- Secure token storage
- User data deletion capability

## Deployment Requirements

**Platform**: Google Cloud Run

**Configuration**:
- Container-based deployment
- Auto-scaling (0 to N instances)
- Persistent volume for SQLite (or Cloud SQL)
- Environment variables for secrets
- Health check endpoints

**Monitoring**:
- Request logging
- Error tracking
- Performance metrics
- OAuth flow analytics

## Success Criteria

### Phase 1: Local Development (1-2 days)
- [ ] Basic MCP server running locally
- [ ] SQLite database working
- [ ] All CRUD operations functional
- [ ] Testable from Claude Code via stdio

### Phase 2: HTTP + OAuth (1 day)
- [ ] HTTP endpoints implemented
- [ ] OAuth 2.1 working
- [ ] MCP spec compliance verified
- [ ] Session management working
- [ ] Calendar integration (link tasks to events)

### Phase 3: Cloud Deployment (1 day)
- [ ] Deployed to Cloud Run
- [ ] Accessible from Claude.ai
- [ ] Accessible from Claude mobile
- [ ] OAuth callbacks configured

### Phase 4: Production Ready (ongoing)
- [ ] Error handling comprehensive
- [ ] Monitoring/logging operational
- [ ] Documentation complete
- [ ] Performance acceptable (<500ms p95)

### Phase 5: Birds Eye Dashboard (1-2 days)
- [ ] Web dashboard accessible via URL
- [ ] Read-only view of all tasks
- [ ] Project Kanban visualization (Backlog, Todo, In Progress, Done)
- [ ] Timeline/calendar integration view
- [ ] Analytics and insights:
  - Completion rates by project
  - Task velocity (tasks completed per week)
  - Time estimate accuracy
  - Energy distribution patterns
  - Overdue task trends
- [ ] Energy distribution charts
- [ ] Real-time sync with MCP server data
- [ ] Responsive design (mobile + desktop)
- [ ] Dark mode support
- [ ] Export functionality (PDF reports, CSV data)

## Phase 5 Details: Birds Eye Dashboard

### Dashboard Views

**1. Strategic Overview (Landing Page)**
- Total active tasks with trend indicators
- Tasks by priority (visual breakdown)
- Tasks by project (pie chart or cards)
- Upcoming deadlines (next 7 days)
- Completion rate trends (last 30 days)

**2. Project Kanban View**
```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│   BACKLOG   │   TODO      │ IN PROGRESS │    DONE     │
│  (Priority  │  (Scheduled │  (Active)   │  (Complete) │
│   not set)  │  or urgent) │             │             │
└─────────────┴─────────────┴─────────────┴─────────────┘
```
- Drag-and-drop disabled (read-only)
- Color-coded by energy level
- Click task for details modal
- Filter by project

**3. Timeline View**
- Weekly calendar grid showing scheduled tasks
- Unscheduled tasks in sidebar
- Visual conflicts between tasks and calendar events
- Capacity indicators (hours available vs committed)

**4. Analytics Dashboard**
- Completion rate over time (line chart)
- Tasks created vs completed (bar chart)
- Average time to completion by project
- Energy level distribution (donut chart)
- Most delayed tasks (table)
- Productivity patterns (heatmap by day/hour)

**5. Insights Page**
Natural language insights generated from data:
- "You complete 80% of teaching tasks same-day"
- "Custom Cult tasks consistently take 2x estimates"
- "Friday afternoons are your most productive"
- "Deep focus tasks get pushed - consider better blocking"

### Technical Implementation

**Frontend**:
- React (matches artifact pattern)
- Recharts for visualizations
- Tailwind CSS for styling
- Real-time updates via polling or WebSocket

**Backend API Endpoints** (in addition to MCP):
- `GET /api/dashboard/overview` - Summary stats
- `GET /api/dashboard/kanban` - Kanban data
- `GET /api/dashboard/timeline` - Calendar view data
- `GET /api/dashboard/analytics` - Analytics data
- `GET /api/dashboard/insights` - AI-generated insights

**Data Flow**:
```
Dashboard → REST API → Same Database ← MCP Server
```

Both the MCP server and dashboard read from the same SQLite/PostgreSQL database, ensuring consistency.

## Out of Scope (for now)

- Team/shared task lists
- File attachments
- Subtasks/dependencies (may add in Phase 5)
- Recurring tasks
- Email notifications
- Third-party integrations beyond Google Calendar
- Real-time collaboration
- Task templates (may add in Phase 5)

## Timeline Estimate

- **Phase 1**: 1-2 days (local development)
- **Phase 2**: 1 day (HTTP + OAuth + Calendar)
- **Phase 3**: 1 day (deployment)
- **Phase 4**: Ongoing (polish)
- **Phase 5**: 1-2 days (dashboard)

**Total**: 4-6 days of focused development

## Dependencies

**Python Packages**:
- `mcp` - MCP SDK
- `fastapi` - HTTP framework
- `uvicorn` - ASGI server
- `sqlalchemy` - Database ORM
- `google-auth` - OAuth libraries
- `python-dotenv` - Environment management
- `pytest` - Testing
- `google-api-python-client` - Google Calendar integration

**External Services**:
- Google Cloud Platform account
- OAuth 2.0 credentials
- Cloud Run service
- (Optional) Cloud SQL instance

## Notes for Development

**Start Simple**: Get basic task CRUD working locally first. Don't worry about OAuth or deployment until core functionality works.

**Iterate**: Build, test, refine. Don't try to be perfect on first pass.

**Test Frequently**: After each feature, test it from Claude Code to make sure it works as expected.

**Document As You Go**: Write README, comments, and API docs while building, not after.

**Security Last**: Get it working first, then add proper auth. Use mock auth initially.

**Dashboard Separately**: Build Phases 1-4 first, then add dashboard as enhancement.

## References

- MCP Specification: https://spec.modelcontextprotocol.io/
- Claude MCP Documentation: https://docs.claude.com/docs/model-context-protocol
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- OAuth 2.1: https://oauth.net/2.1/
- FastAPI Documentation: https://fastapi.tiangolo.com/
- Google Calendar API: https://developers.google.com/calendar
