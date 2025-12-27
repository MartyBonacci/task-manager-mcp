# MCP Error Codes

This document defines the error codes used in the Task Manager MCP Server, following the [MCP Specification](https://spec.modelcontextprotocol.io/) version 2025-06-18.

## Overview

The Task Manager MCP Server uses JSON-RPC 2.0 error codes for MCP protocol errors, combined with custom error codes for domain-specific errors.

All MCP errors are returned in this format:

```json
{
  "error": {
    "code": -32600,
    "message": "Human-readable error message",
    "data": {
      "...": "Optional additional context"
    }
  }
}
```

---

## Standard JSON-RPC 2.0 Error Codes

These are the standard error codes defined by the JSON-RPC 2.0 specification:

| Code    | Name              | Meaning                                                                 | Example                                      |
|---------|-------------------|-------------------------------------------------------------------------|----------------------------------------------|
| -32700  | Parse error       | Invalid JSON was received by the server                                 | Malformed JSON in request body               |
| -32600  | Invalid Request   | The JSON sent is not a valid Request object                             | Missing required field like "name" or "params"|
| -32601  | Method not found  | The method does not exist / is not available                            | Calling unknown tool `task_invalid`          |
| -32602  | Invalid params    | Invalid method parameter(s)                                             | Wrong parameter type or missing required param|
| -32603  | Internal error    | Internal JSON-RPC error                                                 | Unexpected server error during execution     |

### Usage in Code

```python
from app.exceptions import (
    MCPInvalidRequestException,   # -32600
    MCPMethodNotFoundException,   # -32601
    MCPInvalidParamsException,    # -32602
    MCPInternalErrorException,    # -32603
)

# Invalid request format
raise MCPInvalidRequestException("Missing 'name' field")

# Tool not found
raise MCPMethodNotFoundException("task_invalid_tool")

# Invalid parameters
raise MCPInvalidParamsException("title must be a string", param_name="title")

# Internal error
raise MCPInternalErrorException("Database connection failed")
```

---

## Custom MCP Error Codes (-32000 to -32099)

These are application-specific error codes in the range reserved for server-defined errors:

| Code    | Name                          | Meaning                                                          | Example                                      |
|---------|-------------------------------|------------------------------------------------------------------|----------------------------------------------|
| -32000  | Authentication Required       | MCP method requires authentication but no valid session provided | Calling `task_list` without session token    |
| -32001  | Invalid Session               | Session ID is invalid or expired                                 | Using expired session_id                     |
| -32002  | Insufficient Permissions      | User lacks permission for this resource                          | Accessing another user's task                |
| -32003  | Resource Not Found            | Requested resource does not exist                                | Task ID not found in database                |
| -32004  | Resource Already Exists       | Resource with this identifier already exists                     | Creating task with duplicate ID              |
| -32005  | Validation Failed             | Request data failed validation                                   | Task title too long (>200 chars)             |
| -32006  | Rate Limit Exceeded           | Too many requests in time window                                 | More than 100 requests per minute            |
| -32007  | Service Unavailable           | External service is temporarily unavailable                      | Database connection pool exhausted           |

### Usage in Code

```python
from app.exceptions import MCPAuthenticationRequiredException

# Authentication required
raise MCPAuthenticationRequiredException()

# Custom error with specific code
raise MCPException(
    message="Resource already exists",
    status_code=409,
    mcp_error_code=-32004,
    detail={"resource_id": "task-123"}
)
```

---

## HTTP Status Code Mapping

MCP errors are returned over HTTP with appropriate status codes:

| MCP Error Code Range | HTTP Status Code | Description                                |
|----------------------|------------------|--------------------------------------------|
| -32700               | 400              | Bad Request (parse error)                  |
| -32600               | 400              | Bad Request (invalid request)              |
| -32601               | 404              | Not Found (method not found)               |
| -32602               | 400              | Bad Request (invalid params)               |
| -32603               | 500              | Internal Server Error                      |
| -32000               | 401              | Unauthorized (authentication required)     |
| -32001               | 401              | Unauthorized (invalid session)             |
| -32002               | 403              | Forbidden (insufficient permissions)       |
| -32003               | 404              | Not Found (resource not found)             |
| -32004               | 409              | Conflict (resource already exists)         |
| -32005               | 422              | Unprocessable Entity (validation failed)   |
| -32006               | 429              | Too Many Requests (rate limit exceeded)    |
| -32007               | 503              | Service Unavailable                        |

---

## OAuth 2.1 Error Codes

OAuth errors follow [RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749#section-5.2) format and are NOT MCP errors.

They use a different response format:

```json
{
  "error": "invalid_grant",
  "error_description": "Authorization code is invalid or expired",
  "detail": {
    "...": "Optional context"
  }
}
```

| Error Code            | HTTP Status | Meaning                                                      |
|-----------------------|-------------|--------------------------------------------------------------|
| invalid_request       | 400         | Request is missing required parameter                        |
| invalid_client        | 401         | Client authentication failed                                 |
| invalid_grant         | 400         | Authorization code/refresh token is invalid                  |
| unauthorized_client   | 403         | Client is not authorized for this grant type                 |
| unsupported_grant_type| 400         | Grant type not supported by authorization server             |
| invalid_scope         | 400         | Requested scope is invalid or exceeds granted scope          |
| invalid_token         | 401         | Access token is invalid                                      |
| token_expired         | 401         | Access token has expired                                     |
| insufficient_scope    | 403         | Token lacks required scope                                   |
| server_error          | 500         | Authorization server encountered an unexpected error         |

### Usage in Code

```python
from app.exceptions import (
    InvalidAuthorizationCodeException,  # invalid_grant
    InvalidTokenException,              # invalid_token
    TokenExpiredException,              # token_expired
    InsufficientScopeException,         # insufficient_scope
)
```

---

## Dynamic Client Registration (RFC 7591) Error Codes

Dynamic client registration errors follow [RFC 7591](https://datatracker.ietf.org/doc/html/rfc7591#section-3.2.2) format:

```json
{
  "error": "invalid_redirect_uri",
  "error_description": "Redirect URI not registered for client",
  "detail": {
    "redirect_uri": "myapp://callback"
  }
}
```

| Error Code            | HTTP Status | Meaning                                                      |
|-----------------------|-------------|--------------------------------------------------------------|
| invalid_redirect_uri  | 400         | One or more redirect URIs are invalid                        |
| invalid_client_metadata | 400       | Client metadata is malformed or invalid                      |
| invalid_client        | 401         | Client credentials are invalid                               |
| client_expired        | 401         | Client registration has expired                              |
| invalid_platform      | 400         | Platform is not supported                                    |

### Usage in Code

```python
from app.exceptions import (
    InvalidClientException,         # invalid_client
    InvalidRedirectUriException,    # invalid_redirect_uri
    ClientExpiredException,         # client_expired
    InvalidPlatformException,       # invalid_platform
)
```

---

## Error Response Examples

### MCP Error (Method Not Found)

**Request:**
```http
POST /mcp/tools/call HTTP/1.1
Content-Type: application/json

{
  "name": "task_invalid",
  "params": {}
}
```

**Response:**
```http
HTTP/1.1 404 Not Found
Content-Type: application/json

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

### MCP Error (Authentication Required)

**Request:**
```http
POST /mcp/tools/call HTTP/1.1
Content-Type: application/json

{
  "name": "task_list",
  "params": {}
}
```

**Response:**
```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "error": {
    "code": -32000,
    "message": "Authentication required",
    "data": {}
  }
}
```

### OAuth Error (Invalid Token)

**Request:**
```http
POST /oauth/refresh HTTP/1.1
Content-Type: application/json

{
  "session_id": "session_123",
  "refresh_token": "invalid_token"
}
```

**Response:**
```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "error": "invalid_token",
  "error_description": "Invalid refresh token"
}
```

### Dynamic Client Error (Invalid Redirect URI)

**Request:**
```http
GET /oauth/authorize?client_id=client_abc&redirect_uri=evil://hack HTTP/1.1
```

**Response:**
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": "invalid_redirect_uri",
  "error_description": "Redirect URI not registered for client: evil://hack",
  "detail": {
    "redirect_uri": "evil://hack"
  }
}
```

### Validation Error (Pydantic)

**Request:**
```http
POST /clients/register HTTP/1.1
Content-Type: application/json

{
  "platform": "invalid_platform",
  "redirect_uris": []
}
```

**Response:**
```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

{
  "error": "validation_error",
  "message": "Request validation failed",
  "detail": [
    {
      "loc": ["body", "redirect_uris"],
      "msg": "ensure this value has at least 1 item",
      "type": "value_error.list.min_items"
    }
  ]
}
```

---

## Error Handling Best Practices

### 1. Always Include Context

Provide specific, actionable error messages:

```python
# ❌ Bad - Generic error
raise TaskNotFoundException("Task not found")

# ✅ Good - Specific error with context
raise TaskNotFoundException(task_id="task-123")
```

### 2. Use Appropriate Error Codes

Choose the most specific error code:

```python
# ❌ Bad - Generic internal error
raise MCPInternalErrorException("Something went wrong")

# ✅ Good - Specific error type
raise MCPAuthenticationRequiredException()
```

### 3. Never Expose Sensitive Data

Don't include sensitive information in error messages:

```python
# ❌ Bad - Exposes token
raise InvalidTokenException(f"Token {token} is invalid")

# ✅ Good - Generic message
raise InvalidTokenException("Token is invalid")
```

### 4. Log Errors Appropriately

All errors are automatically logged with context by the error handlers:

```python
# Error handlers automatically log:
# - Exception type and message
# - HTTP method and path
# - Status code
# - Additional detail/data
```

### 5. Provide Recovery Guidance

When possible, include guidance in the `detail` field:

```python
raise MCPInvalidParamsException(
    message="title must be between 1 and 200 characters",
    param_name="title"
)
# Returns:
# {
#   "error": {"code": -32602, "message": "...", "data": {"param": "title"}}
# }
```

---

## Debugging Errors

### Enable Debug Mode

Set `DEBUG=true` in `.env` to see full stack traces (development only):

```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

### View Error Logs

Errors are logged with structured context:

```bash
# View recent errors
tail -f logs/app.log | grep ERROR

# View MCP errors specifically
tail -f logs/app.log | grep "MCP Error"
```

### Test Error Responses

Use the test suite to verify error handling:

```bash
# Run error handling tests
pytest tests/test_error_handlers.py -v

# Test specific error scenario
pytest tests/test_error_handlers.py::test_mcp_authentication_required -v
```

---

## References

- [MCP Specification](https://spec.modelcontextprotocol.io/) - MCP Protocol Version 2025-06-18
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification) - Error codes -32700 to -32603
- [RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749) - OAuth 2.0 Authorization Framework
- [RFC 7591](https://datatracker.ietf.org/doc/html/rfc7591) - OAuth 2.0 Dynamic Client Registration Protocol
- [FastAPI Exception Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/) - FastAPI error handler documentation
