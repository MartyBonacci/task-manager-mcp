# MCP Protocol Contract: Task Manager MCP Server

**Feature**: 001-implement-phase-1-local-development-with-sqlite-and-basic-mcp-tools
**Protocol Version**: MCP Specification 2025-06-18
**Created**: 2025-12-25

---

## Overview

This document defines the MCP (Model Context Protocol) contract for the Task Manager MCP Server Phase 1 implementation. It specifies the exact request/response formats for all MCP endpoints and methods, ensuring strict compliance with MCP Specification 2025-06-18.

**Protocol**: JSON-RPC 2.0 over stdio (Phase 1) or HTTP (Phase 2+)
**Content Type**: application/json
**Required Headers**: `MCP-Protocol-Version: 2025-06-18`

---

## Endpoints

### Protocol Discovery

**Endpoint**: `HEAD /`

**Purpose**: Advertise MCP protocol version to clients

**Request**: HTTP HEAD request (no body)

**Response Headers**:
```
MCP-Protocol-Version: 2025-06-18
```

**Response Body**: Empty

**Example**:
```
HEAD / HTTP/1.1
Host: localhost:8000

HTTP/1.1 200 OK
MCP-Protocol-Version: 2025-06-18
```

---

### MCP Methods Handler

**Endpoint**: `POST /`

**Purpose**: Handle all MCP methods (initialize, tools/list, tools/call)

**Request Format**: JSON-RPC 2.0

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "method": "<method_name>",
  "params": { ... }
}
```

**Supported Methods**:
- `initialize`: Protocol handshake
- `tools/list`: Discover available tools
- `tools/call`: Execute a tool

---

## Method: initialize

### Purpose
Establish connection between client and server, negotiate capabilities

### Request

```json
{
  "method": "initialize",
  "params": {}
}
```

**Parameters**: None

### Response (Success)

```json
{
  "protocolVersion": "2025-06-18",
  "capabilities": {
    "tools": {}
  },
  "serverInfo": {
    "name": "Task Manager MCP",
    "version": "0.1.0"
  }
}
```

**Fields**:
- `protocolVersion` (string, required): MCP spec version supported
- `capabilities` (object, required): Server capabilities
  - `tools` (object): Tool capabilities (empty for Phase 1)
- `serverInfo` (object, required): Server metadata
  - `name` (string, required): Server name
  - `version` (string, required): Server version

### Example

**Request**:
```http
POST / HTTP/1.1
Content-Type: application/json

{
  "method": "initialize",
  "params": {}
}
```

**Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "protocolVersion": "2025-06-18",
  "capabilities": {
    "tools": {}
  },
  "serverInfo": {
    "name": "Task Manager MCP",
    "version": "0.1.0"
  }
}
```

---

## Method: tools/list

### Purpose
Discover all available tools and their schemas

### Request

```json
{
  "method": "tools/list",
  "params": {}
}
```

**Parameters**: None

### Response (Success)

```json
{
  "tools": [
    {
      "name": "task_create",
      "description": "Create a new task",
      "inputSchema": {
        "type": "object",
        "properties": {
          "title": {
            "type": "string",
            "description": "Task title (1-500 characters)"
          },
          "project": {
            "type": "string",
            "description": "Project category (optional)"
          },
          "priority": {
            "type": "integer",
            "minimum": 1,
            "maximum": 5,
            "description": "Priority (1=Someday, 5=Critical, default=3)"
          },
          "energy": {
            "type": "string",
            "enum": ["light", "medium", "deep"],
            "description": "Energy level required (default=medium)"
          },
          "time_estimate": {
            "type": "string",
            "description": "Time estimate (e.g., '1hr', default='1hr')"
          },
          "notes": {
            "type": "string",
            "description": "Additional notes (optional)"
          }
        },
        "required": ["title"]
      }
    },
    ... (7 more tools)
  ]
}
```

**Fields**:
- `tools` (array, required): Array of tool definitions
  - `name` (string, required): Unique tool identifier
  - `description` (string, required): Human-readable tool description
  - `inputSchema` (object, required): JSON Schema for tool inputs

### Example

**Request**:
```http
POST / HTTP/1.1
Content-Type: application/json

{
  "method": "tools/list",
  "params": {}
}
```

**Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "tools": [
    {
      "name": "task_create",
      "description": "Create a new task",
      "inputSchema": { ... }
    },
    {
      "name": "task_list",
      "description": "List tasks with optional filters",
      "inputSchema": { ... }
    },
    ... (6 more tools)
  ]
}
```

---

## Method: tools/call

### Purpose
Execute a specific tool with provided arguments

### Request

```json
{
  "method": "tools/call",
  "params": {
    "name": "<tool_name>",
    "arguments": { ... }
  }
}
```

**Parameters**:
- `name` (string, required): Name of the tool to execute
- `arguments` (object, required): Tool-specific arguments (validated against inputSchema)

### Response (Success)

```json
{
  "content": [
    {
      "type": "text",
      "text": "<result_data_as_json_string>"
    }
  ]
}
```

**Fields**:
- `content` (array, required): Array of content blocks
  - `type` (string, required): Content type (always "text" for Phase 1)
  - `text` (string, required): Result data (typically JSON-serialized)

### Response (Error)

```json
{
  "isError": true,
  "content": [
    {
      "type": "text",
      "text": "<error_message>"
    }
  ]
}
```

**Fields**:
- `isError` (boolean, required): Always `true` for errors
- `content` (array, required): Array of content blocks
  - `type` (string, required): Content type (always "text")
  - `text` (string, required): Error message (user-friendly, no internals)

### Examples

**Success Example (task_create)**:

Request:
```json
{
  "method": "tools/call",
  "params": {
    "name": "task_create",
    "arguments": {
      "title": "Research MCP specification",
      "project": "Deep Dive Coding",
      "priority": 4,
      "energy": "deep",
      "time_estimate": "2hr"
    }
  }
}
```

Response:
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"id\": 1, \"user_id\": \"dev-user\", \"title\": \"Research MCP specification\", \"project\": \"Deep Dive Coding\", \"priority\": 4, \"energy\": \"deep\", \"time_estimate\": \"2hr\", \"notes\": null, \"due_date\": null, \"completed\": false, \"completed_at\": null, \"created_at\": \"2025-12-25T12:00:00Z\", \"updated_at\": \"2025-12-25T12:00:00Z\"}"
    }
  ]
}
```

**Error Example (validation failure)**:

Request:
```json
{
  "method": "tools/call",
  "params": {
    "name": "task_create",
    "arguments": {
      "title": "",
      "priority": 6
    }
  }
}
```

Response:
```json
{
  "isError": true,
  "content": [
    {
      "type": "text",
      "text": "Validation error: Title must be between 1 and 500 characters; Priority must be between 1 and 5"
    }
  ]
}
```

---

## Tool Contracts

### tool: task_create

**Purpose**: Create a new task

**Arguments**:
- `title` (string, **required**): Task title (1-500 characters)
- `project` (string, optional): Project category
- `priority` (integer, optional): Priority (1-5, default=3)
- `energy` (string, optional): Energy level (light|medium|deep, default=medium)
- `time_estimate` (string, optional): Time estimate (default="1hr")
- `notes` (string, optional): Additional notes

**Returns**: Created task object (JSON)

**Example**: See tools/call success example above

---

### tool: task_list

**Purpose**: List tasks with optional filters

**Arguments**:
- `project` (string, optional): Filter by project
- `priority` (integer, optional): Filter by priority (1-5)
- `show_completed` (boolean, optional): Include completed tasks (default=false)
- `limit` (integer, optional): Maximum results (default=100, max=1000)
- `offset` (integer, optional): Pagination offset (default=0)

**Returns**: Array of task objects (JSON)

**Request Example**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "task_list",
    "arguments": {
      "project": "Deep Dive Coding",
      "show_completed": false
    }
  }
}
```

**Response Example**:
```json
{
  "content": [
    {
      "type": "text",
      "text": "[{\"id\": 1, \"title\": \"Research MCP spec\", ...}, {\"id\": 2, \"title\": \"Write tests\", ...}]"
    }
  ]
}
```

---

### tool: task_get

**Purpose**: Get a specific task by ID

**Arguments**:
- `task_id` (integer, **required**): Task ID to retrieve

**Returns**: Single task object (JSON) or error if not found

**Request Example**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "task_get",
    "arguments": {
      "task_id": 1
    }
  }
}
```

**Response Example (Success)**:
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"id\": 1, \"title\": \"Research MCP spec\", ...}"
    }
  ]
}
```

**Response Example (Not Found)**:
```json
{
  "isError": true,
  "content": [
    {
      "type": "text",
      "text": "Task 1 not found"
    }
  ]
}
```

---

### tool: task_update

**Purpose**: Update a task's fields

**Arguments**:
- `task_id` (integer, **required**): Task ID to update
- `title` (string, optional): New title
- `project` (string, optional): New project
- `priority` (integer, optional): New priority (1-5)
- `energy` (string, optional): New energy level
- `time_estimate` (string, optional): New time estimate
- `notes` (string, optional): New notes

**Returns**: Updated task object (JSON)

**Request Example**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "task_update",
    "arguments": {
      "task_id": 1,
      "priority": 5,
      "notes": "Updated: now critical priority"
    }
  }
}
```

**Response Example**:
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"id\": 1, \"priority\": 5, \"notes\": \"Updated: now critical priority\", \"updated_at\": \"2025-12-25T13:00:00Z\", ...}"
    }
  ]
}
```

---

### tool: task_complete

**Purpose**: Mark a task as complete

**Arguments**:
- `task_id` (integer, **required**): Task ID to complete

**Returns**: Updated task object with `completed=true` and `completed_at` timestamp (JSON)

**Request Example**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "task_complete",
    "arguments": {
      "task_id": 1
    }
  }
}
```

**Response Example**:
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"id\": 1, \"completed\": true, \"completed_at\": \"2025-12-25T13:30:00Z\", ...}"
    }
  ]
}
```

---

### tool: task_delete

**Purpose**: Delete a task permanently

**Arguments**:
- `task_id` (integer, **required**): Task ID to delete

**Returns**: Success confirmation (JSON)

**Request Example**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "task_delete",
    "arguments": {
      "task_id": 1
    }
  }
}
```

**Response Example**:
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"success\": true, \"task_id\": 1}"
    }
  ]
}
```

---

### tool: task_search

**Purpose**: Search tasks by keywords in title or notes

**Arguments**:
- `query` (string, **required**): Search keywords
- `fields` (string, optional): Fields to search (default="both" for title+notes)

**Returns**: Array of matching task objects (JSON)

**Request Example**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "task_search",
    "arguments": {
      "query": "MCP"
    }
  }
}
```

**Response Example**:
```json
{
  "content": [
    {
      "type": "text",
      "text": "[{\"id\": 1, \"title\": \"Research MCP spec\", ...}, {\"id\": 5, \"title\": \"Test MCP integration\", ...}]"
    }
  ]
}
```

---

### tool: task_stats

**Purpose**: Get task statistics grouped by project, priority, or status

**Arguments**:
- `group_by` (string, optional): Grouping field (project|priority|status, default=all)

**Returns**: Statistics object (JSON)

**Request Example**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "task_stats",
    "arguments": {
      "group_by": "project"
    }
  }
}
```

**Response Example**:
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"by_project\": {\"Deep Dive Coding\": 3, \"Custom Cult\": 2, \"Personal\": 1}, \"total\": 6, \"completed\": 2, \"completion_rate\": 33.33}"
    }
  ]
}
```

---

## Error Codes

### MCP Standard Errors

Following JSON-RPC 2.0 error code conventions:

- **-32600**: Invalid Request (malformed JSON, missing required fields)
- **-32601**: Method Not Found (unsupported MCP method)
- **-32602**: Invalid Params (tool arguments don't match schema)
- **-32603**: Internal Error (server-side exception)

### Application Errors

Application-level errors use the `isError` flag in response (not JSON-RPC error codes):

- **Validation errors**: Returned in `content[0].text` with helpful message
- **Not found errors**: "Task {id} not found"
- **Permission errors**: "Cannot access task owned by another user" (Phase 2+)

**Error Response Format**:
```json
{
  "isError": true,
  "content": [
    {
      "type": "text",
      "text": "Helpful error message without exposing internals"
    }
  ]
}
```

---

## Protocol Compliance Checklist

Phase 1 implementation must satisfy:

- [x] HEAD / returns `MCP-Protocol-Version: 2025-06-18` header
- [x] POST / accepts JSON-RPC 2.0 formatted requests
- [x] initialize method returns protocol version, capabilities, server info
- [x] tools/list method returns array of tool definitions with complete inputSchema
- [x] tools/call method executes tools and returns content array
- [x] Success responses use `{"content": [{"type": "text", "text": "..."}]}`format
- [x] Error responses use `{"isError": true, "content": [...]}` format
- [x] All responses are valid JSON
- [x] Tool arguments validated against inputSchema
- [x] Helpful error messages (no stack traces, no internal details)

---

## Testing Protocol Compliance

### Integration Tests

**Test 1: Protocol Discovery**
```python
def test_protocol_discovery():
    response = client.head("/")
    assert response.headers["MCP-Protocol-Version"] == "2025-06-18"
```

**Test 2: Initialize Method**
```python
def test_initialize():
    response = client.post("/", json={"method": "initialize", "params": {}})
    data = response.json()
    assert data["protocolVersion"] == "2025-06-18"
    assert "capabilities" in data
    assert "serverInfo" in data
```

**Test 3: Tools List**
```python
def test_tools_list():
    response = client.post("/", json={"method": "tools/list", "params": {}})
    data = response.json()
    assert "tools" in data
    assert len(data["tools"]) == 8
    assert all("name" in tool for tool in data["tools"])
    assert all("inputSchema" in tool for tool in data["tools"])
```

**Test 4: Tool Call Success**
```python
def test_tool_call_task_create():
    response = client.post("/", json={
        "method": "tools/call",
        "params": {
            "name": "task_create",
            "arguments": {"title": "Test task"}
        }
    })
    data = response.json()
    assert "content" in data
    assert data["content"][0]["type"] == "text"
    result = json.loads(data["content"][0]["text"])
    assert result["title"] == "Test task"
```

**Test 5: Tool Call Error**
```python
def test_tool_call_validation_error():
    response = client.post("/", json={
        "method": "tools/call",
        "params": {
            "name": "task_create",
            "arguments": {"title": ""}  # Invalid: empty title
        }
    })
    data = response.json()
    assert data["isError"] is True
    assert "content" in data
```

---

## Appendix

### Complete Tool List

1. `task_create` - Create new task
2. `task_list` - List tasks with filters
3. `task_get` - Get task by ID
4. `task_update` - Update task fields
5. `task_complete` - Mark task complete
6. `task_delete` - Delete task
7. `task_search` - Search by keywords
8. `task_stats` - Get statistics

### JSON Schema Reference

All `inputSchema` definitions follow JSON Schema Draft 7 specification.

**Common field types**:
- `string`: Text fields
- `integer`: Numeric fields with range constraints
- `boolean`: True/false flags
- `enum`: String fields with allowed values

### Version History

**v1.0.0 (2025-12-25)**: Initial MCP protocol contract for Phase 1
- 3 MCP methods (initialize, tools/list, tools/call)
- 8 task management tools
- MCP Specification 2025-06-18 compliance
