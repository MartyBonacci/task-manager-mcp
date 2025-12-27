# Error Handling Guide

This guide explains how to handle errors properly in the Task Manager MCP Server codebase.

## Table of Contents

- [Overview](#overview)
- [Exception Hierarchy](#exception-hierarchy)
- [Raising Exceptions](#raising-exceptions)
- [Catching Exceptions](#catching-exceptions)
- [Error Responses](#error-responses)
- [Testing Errors](#testing-errors)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Task Manager MCP Server uses a custom exception hierarchy built on top of Python's standard `Exception` class. All custom exceptions are defined in `app/exceptions.py` and are automatically handled by middleware in `app/api/error_handlers.py`.

### Key Principles

1. **Use custom exceptions** - Never raise generic exceptions like `Exception` or `ValueError` directly
2. **Let middleware handle responses** - Don't manually create error responses; raise exceptions and let handlers format them
3. **Include context** - Always provide relevant detail in exception constructors
4. **Log appropriately** - Error handlers automatically log exceptions with context
5. **Follow standards** - Use OAuth 2.1, RFC 7591, and MCP error codes correctly

---

## Exception Hierarchy

```
Exception (Python built-in)
└── TaskManagerException (base for all custom exceptions)
    ├── OAuthException (OAuth 2.1 errors)
    │   ├── InvalidStateException
    │   ├── InvalidAuthorizationCodeException
    │   ├── InvalidTokenException
    │   ├── TokenExpiredException
    │   └── InsufficientScopeException
    │
    ├── DynamicClientException (RFC 7591 errors)
    │   ├── InvalidClientException
    │   ├── InvalidRedirectUriException
    │   ├── ClientExpiredException
    │   └── InvalidPlatformException
    │
    ├── SessionException (session management)
    │   ├── SessionNotFoundException
    │   ├── SessionExpiredException
    │   └── InvalidRefreshTokenException
    │
    ├── MCPException (MCP protocol errors)
    │   ├── MCPInvalidRequestException
    │   ├── MCPMethodNotFoundException
    │   ├── MCPInvalidParamsException
    │   ├── MCPInternalErrorException
    │   └── MCPAuthenticationRequiredException
    │
    ├── TaskException (task operations)
    │   ├── TaskNotFoundException
    │   ├── TaskValidationException
    │   └── TaskPermissionException
    │
    ├── UserException (user operations)
    │   ├── UserNotFoundException
    │   └── UserAlreadyExistsException
    │
    ├── DatabaseException (database errors)
    │   ├── DatabaseConnectionException
    │   └── DatabaseOperationException
    │
    └── ConfigurationException (configuration errors)
        ├── MissingConfigException
        └── InvalidConfigException
```

---

## Raising Exceptions

### Basic Usage

Always import the specific exception you need:

```python
from app.exceptions import (
    TaskNotFoundException,
    TaskValidationException,
    InvalidTokenException,
)

# Raise with default message
raise TaskNotFoundException(task_id="task-123")

# Raise with custom message
raise TaskValidationException(
    message="Title must be between 1 and 200 characters",
    field="title"
)

# Raise with context
raise InvalidTokenException("Access token has been revoked")
```

### OAuth Exceptions

```python
from app.exceptions import (
    InvalidStateException,
    InvalidAuthorizationCodeException,
    TokenExpiredException,
)

# CSRF validation failed
if state not in oauth_states:
    raise InvalidStateException()

# Authorization code exchange failed
try:
    flow.fetch_token(code=code)
except Exception:
    raise InvalidAuthorizationCodeException()

# Token expired
if datetime.now(timezone.utc) >= session.expires_at:
    raise TokenExpiredException()
```

### Dynamic Client Exceptions

```python
from app.exceptions import (
    InvalidClientException,
    InvalidRedirectUriException,
    ClientExpiredException,
    InvalidPlatformException,
)

# Invalid client credentials
client = await get_client(db, client_id)
if not client or client.client_secret != client_secret:
    raise InvalidClientException()

# Redirect URI not registered
if redirect_uri not in client.redirect_uris:
    raise InvalidRedirectUriException(redirect_uri)

# Client registration expired
if client.expires_at <= datetime.now(timezone.utc):
    raise ClientExpiredException()

# Invalid platform
valid_platforms = {"ios", "android", "macos", "windows", "linux", "cli"}
if platform not in valid_platforms:
    raise InvalidPlatformException(platform, list(valid_platforms))
```

### MCP Exceptions

```python
from app.exceptions import (
    MCPInvalidRequestException,
    MCPMethodNotFoundException,
    MCPInvalidParamsException,
    MCPAuthenticationRequiredException,
)

# Invalid request format
if "name" not in request:
    raise MCPInvalidRequestException("Missing 'name' field")

# Tool not found
if tool_name not in TOOL_HANDLERS:
    raise MCPMethodNotFoundException(tool_name)

# Invalid parameters
if not isinstance(params.get("title"), str):
    raise MCPInvalidParamsException(
        message="title must be a string",
        param_name="title"
    )

# Authentication required
if not user_id:
    raise MCPAuthenticationRequiredException()
```

### Task Exceptions

```python
from app.exceptions import (
    TaskNotFoundException,
    TaskValidationException,
    TaskPermissionException,
)

# Task not found
task = await db.execute(select(Task).where(Task.id == task_id))
if not task:
    raise TaskNotFoundException(task_id)

# Validation error
if len(title) > 200:
    raise TaskValidationException(
        message="Title cannot exceed 200 characters",
        field="title"
    )

# Permission denied
if task.user_id != current_user_id:
    raise TaskPermissionException(task_id)
```

### Database Exceptions

```python
from app.exceptions import (
    DatabaseConnectionException,
    DatabaseOperationException,
)

# Connection failed
try:
    await db.execute(text("SELECT 1"))
except Exception:
    raise DatabaseConnectionException()

# Operation failed
try:
    await db.commit()
except Exception as e:
    raise DatabaseOperationException(
        operation="commit",
        message=str(e)
    )
```

---

## Catching Exceptions

### In Services

Services should let exceptions propagate to route handlers:

```python
# ❌ Bad - Catching and re-raising generic exception
async def get_task(db: AsyncSession, task_id: str, user_id: str):
    try:
        task = await db.execute(...)
        if not task:
            raise Exception("Task not found")
    except Exception:
        raise Exception("Error getting task")

# ✅ Good - Raise specific exception, let it propagate
async def get_task(db: AsyncSession, task_id: str, user_id: str):
    task = await db.execute(...)
    if not task:
        raise TaskNotFoundException(task_id)
    if task.user_id != user_id:
        raise TaskPermissionException(task_id)
    return task
```

### In Route Handlers

Route handlers should also let exceptions propagate to error handlers:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

# ❌ Bad - Manually creating error responses
@router.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_authentication),
):
    try:
        task = await TaskService.get_task(db, task_id, user_id)
        return task
    except Exception as e:
        return JSONResponse(
            status_code=404,
            content={"error": "not_found", "message": str(e)}
        )

# ✅ Good - Let error handlers format responses
@router.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_authentication),
):
    # If TaskNotFoundException is raised, error handler converts to:
    # HTTP 404 with {"error": "TaskNotFoundException", "message": "..."}
    task = await TaskService.get_task(db, task_id, user_id)
    return task
```

### Catching for Cleanup

Only catch exceptions when you need to perform cleanup:

```python
async def create_task_with_file_upload(db: AsyncSession, ...):
    file_path = None
    try:
        # Save file
        file_path = await save_uploaded_file(file)

        # Create task
        task = await TaskService.create_task(db, ...)

        return task
    except Exception:
        # Cleanup uploaded file on error
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

        # Re-raise to let error handlers format response
        raise
```

---

## Error Responses

Error handlers automatically convert exceptions to properly formatted responses. You don't need to create these manually.

### TaskManagerException Response Format

```python
# Exception raised:
raise TaskNotFoundException(task_id="task-123")

# HTTP response (automatically generated):
# Status: 404 Not Found
{
  "error": "TaskNotFoundException",
  "message": "Task not found",
  "detail": {
    "task_id": "task-123"
  }
}
```

### OAuthException Response Format

```python
# Exception raised:
raise InvalidTokenException()

# HTTP response (OAuth 2.1 compliant):
# Status: 401 Unauthorized
{
  "error": "invalid_token",
  "error_description": "Invalid token"
}
```

### MCPException Response Format

```python
# Exception raised:
raise MCPMethodNotFoundException("task_invalid")

# HTTP response (MCP protocol compliant):
# Status: 404 Not Found
{
  "error": {
    "code": -32601,
    "message": "Method not found: task_invalid",
    "data": {
      "method": "task_invalid"
    }
  }
}
```

### ValidationError Response Format

```python
# Pydantic validation error (automatic):

# HTTP response:
# Status: 422 Unprocessable Entity
{
  "error": "validation_error",
  "message": "Request validation failed",
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Testing Errors

### Unit Tests

Test that services raise correct exceptions:

```python
import pytest
from app.exceptions import TaskNotFoundException
from app.services.task_service import TaskService

@pytest.mark.asyncio
async def test_get_task_not_found(db_session):
    """Test that getting nonexistent task raises TaskNotFoundException."""
    with pytest.raises(TaskNotFoundException) as exc_info:
        await TaskService.get_task(
            db_session,
            task_id="nonexistent",
            user_id="user-123"
        )

    # Verify exception details
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail["task_id"] == "nonexistent"
```

### Integration Tests

Test that HTTP responses are formatted correctly:

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_task_not_found_response():
    """Test that TaskNotFoundException returns proper HTTP response."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Mock authentication
        response = await client.get(
            "/tasks/nonexistent",
            headers={"Authorization": "Bearer mock-token"}
        )

        # Verify response
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "TaskNotFoundException"
        assert "not found" in data["message"].lower()
        assert data["detail"]["task_id"] == "nonexistent"
```

### Testing Error Handlers

Test that error handlers format responses correctly:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.exceptions import TaskNotFoundException

client = TestClient(app)

def test_task_not_found_handler():
    """Test that TaskNotFoundException is handled correctly."""
    # Create a route that raises the exception
    @app.get("/test/task-not-found")
    async def test_route():
        raise TaskNotFoundException(task_id="test-123")

    # Call the route
    response = client.get("/test/task-not-found")

    # Verify response format
    assert response.status_code == 404
    data = response.json()
    assert data["error"] == "TaskNotFoundException"
    assert data["detail"]["task_id"] == "test-123"
```

---

## Common Patterns

### Pattern 1: Resource Not Found

```python
async def get_resource(db: AsyncSession, resource_id: str, user_id: str):
    """Get resource by ID with permission check."""
    # Query resource
    stmt = select(Resource).where(Resource.id == resource_id)
    result = await db.execute(stmt)
    resource = result.scalar_one_or_none()

    # Resource not found
    if not resource:
        raise ResourceNotFoundException(resource_id)

    # Permission check
    if resource.user_id != user_id:
        raise ResourcePermissionException(resource_id)

    return resource
```

### Pattern 2: Validation Before Creation

```python
async def create_task(db: AsyncSession, user_id: str, data: TaskCreate):
    """Create task with validation."""
    # Validate title length
    if not data.title or len(data.title) > 200:
        raise TaskValidationException(
            message="Title must be between 1 and 200 characters",
            field="title"
        )

    # Validate priority range
    if data.priority < 1 or data.priority > 5:
        raise TaskValidationException(
            message="Priority must be between 1 and 5",
            field="priority"
        )

    # Create task
    task = Task(user_id=user_id, **data.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)

    return task
```

### Pattern 3: OAuth Flow Error Handling

```python
async def exchange_authorization_code(code: str, state: str):
    """Exchange authorization code for tokens."""
    # Validate state (CSRF protection)
    if state not in oauth_states:
        raise InvalidStateException()

    # Remove used state
    del oauth_states[state]

    # Exchange code
    flow = create_oauth_flow()
    try:
        flow.fetch_token(code=code)
    except Exception as e:
        # Log the actual error for debugging
        logger.error(f"Token exchange failed: {e}")
        # But raise OAuth-compliant exception
        raise InvalidAuthorizationCodeException()

    return flow.credentials
```

### Pattern 4: Database Transaction with Rollback

```python
async def transfer_task(
    db: AsyncSession,
    task_id: str,
    from_user_id: str,
    to_user_id: str
):
    """Transfer task ownership with transaction."""
    try:
        # Get task
        task = await get_task(db, task_id, from_user_id)

        # Verify target user exists
        target_user = await get_user(db, to_user_id)
        if not target_user:
            raise UserNotFoundException(to_user_id)

        # Transfer ownership
        task.user_id = to_user_id

        # Commit transaction
        await db.commit()
        await db.refresh(task)

        return task
    except Exception:
        # Rollback on error
        await db.rollback()
        # Re-raise to let error handlers format response
        raise
```

### Pattern 5: MCP Tool Parameter Validation

```python
async def task_update_handler(
    db: AsyncSession,
    user_id: str,
    params: dict
):
    """MCP tool handler for task_update."""
    # Validate required parameters
    task_id = params.get("id")
    if not task_id:
        raise MCPInvalidParamsException(
            message="id is required",
            param_name="id"
        )

    # Validate parameter types
    if "priority" in params:
        priority = params["priority"]
        if not isinstance(priority, int) or priority < 1 or priority > 5:
            raise MCPInvalidParamsException(
                message="priority must be an integer between 1 and 5",
                param_name="priority"
            )

    # Update task
    updated_task = await TaskService.update_task(
        db, task_id, user_id, params
    )

    # Return MCP response format
    return MCPToolResponse(
        content=[
            {
                "type": "text",
                "text": json.dumps(updated_task.model_dump(), indent=2)
            }
        ]
    )
```

---

## Troubleshooting

### Problem: Exception Not Being Caught by Handlers

**Symptom**: Your exception is raised but returns a generic 500 error instead of your custom response.

**Solution**: Make sure your exception inherits from `TaskManagerException` and is registered in error handlers:

```python
# ❌ Bad - Not inherited from TaskManagerException
class MyCustomException(Exception):
    pass

# ✅ Good - Properly inherited
from app.exceptions import TaskManagerException

class MyCustomException(TaskManagerException):
    def __init__(self, message: str):
        super().__init__(message, status_code=400)
```

### Problem: Wrong HTTP Status Code

**Symptom**: Exception is handled but returns wrong status code (e.g., 500 instead of 404).

**Solution**: Specify correct `status_code` in exception constructor:

```python
# ❌ Bad - Uses default 500 status
raise TaskManagerException("Task not found")

# ✅ Good - Specifies 404 status
raise TaskNotFoundException(task_id="task-123")  # status_code=404
```

### Problem: Missing Error Details

**Symptom**: Error response doesn't include expected context.

**Solution**: Pass details to exception constructor:

```python
# ❌ Bad - No context
raise InvalidClientException()

# ✅ Good - Includes context
raise InvalidClientException("Client credentials do not match")
```

### Problem: Sensitive Data in Error Response

**Symptom**: Error messages expose internal implementation details or sensitive data.

**Solution**: Never include sensitive data in exception messages:

```python
# ❌ Bad - Exposes token
raise InvalidTokenException(f"Token {access_token} is invalid")

# ✅ Good - Generic message
raise InvalidTokenException("Access token is invalid")

# ✅ Good - Log sensitive data, don't return it
logger.error(f"Invalid token attempt: {access_token[:10]}...")
raise InvalidTokenException()
```

### Problem: Errors Not Being Logged

**Symptom**: Exceptions are handled but don't appear in logs.

**Solution**: Error handlers automatically log all exceptions. Check log level:

```bash
# Set appropriate log level in .env
LOG_LEVEL=DEBUG  # For development
LOG_LEVEL=INFO   # For production
```

### Problem: Unhandled Exception Type

**Symptom**: Some exceptions return generic error instead of being properly formatted.

**Solution**: All unhandled exceptions are caught by `generic_exception_handler`. If you need specific handling, add a custom exception type.

---

## References

- [app/exceptions.py](../app/exceptions.py) - Exception class definitions
- [app/api/error_handlers.py](../app/api/error_handlers.py) - Error handler implementations
- [docs/MCP_ERROR_CODES.md](./MCP_ERROR_CODES.md) - Complete error code reference
- [MCP Specification](https://spec.modelcontextprotocol.io/) - MCP protocol error handling
- [FastAPI Error Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/) - FastAPI documentation
