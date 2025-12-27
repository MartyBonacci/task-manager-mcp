---
parent_branch: main
feature_number: 003
status: In Progress
created_at: 2025-12-26T11:45:00-05:00
---

# Feature 003: OAuth 2.1 Authentication with Google

## Overview

Implement secure user authentication for the Task Manager MCP Server using OAuth 2.1 with Google as the identity provider. This feature replaces the Phase 1 mock authentication (`user_id = "dev-user"`) with production-ready OAuth 2.1 authentication that supports web clients, mobile apps, and desktop applications through Dynamic Client Registration.

**Business Value**: Enables multi-user access while maintaining data privacy and security. Each user's tasks are isolated and accessible only to them across all platforms (web, mobile, terminal).

**User Impact**: Users authenticate once with their Google account, then access their tasks from any Claude interface (claude.ai, Claude mobile app, Claude Code CLI) without re-authentication during the session.

## User Scenarios

### Scenario 1: First-Time User Authentication (Web)

**Actor**: New user accessing Task Manager from claude.ai

**Flow**:
1. User types "Show me my tasks" in Claude chat
2. Claude detects Task Manager MCP server requires authentication
3. Claude displays: "Task Manager needs access to your Google account to store your tasks. [Authorize Now]"
4. User clicks "Authorize Now"
5. User redirected to Google OAuth consent screen
6. User signs in with Google account (if not already signed in)
7. User sees permissions request: "Task Manager wants to: Access your email address and profile"
8. User clicks "Allow"
9. User redirected back to Claude with success message
10. Claude automatically retries original request: "You have 0 tasks. Would you like to create one?"

**Success Outcome**: User is authenticated and can immediately start managing tasks.

### Scenario 2: Subsequent Access (Session Active)

**Actor**: Authenticated user returning to Claude

**Flow**:
1. User opens claude.ai (same browser session)
2. User types "Create a task to review Q4 budget"
3. Task Manager validates existing OAuth token
4. Task created successfully without re-authentication

**Success Outcome**: Seamless task management without authentication interruption.

### Scenario 3: Token Expiration and Refresh

**Actor**: User with expired access token

**Flow**:
1. User's OAuth token expires after 1 hour
2. User types "List my tasks"
3. Task Manager detects expired token
4. Task Manager uses refresh token to obtain new access token automatically
5. Task list returned successfully

**Success Outcome**: User experiences no interruption; refresh happens transparently.

### Scenario 4: Mobile App Authentication (Dynamic Client Registration)

**Actor**: User accessing from Claude mobile app

**Flow**:
1. Mobile app requests OAuth authentication
2. Task Manager performs Dynamic Client Registration with Google
3. Google returns temporary client credentials
4. Mobile app initiates OAuth flow with PKCE (Proof Key for Code Exchange)
5. User authorizes in mobile browser
6. Mobile app receives authorization code
7. Task Manager exchanges code for access token
8. User accesses tasks from mobile app

**Success Outcome**: Mobile users authenticate securely without pre-registered client credentials.

### Scenario 5: Revoked Access

**Actor**: User who revoked Task Manager's access from Google Account settings

**Flow**:
1. User revokes Task Manager access from https://myaccount.google.com/permissions
2. User tries to use Task Manager: "Show me high priority tasks"
3. Task Manager detects invalid token (403 Forbidden from Google)
4. Claude displays: "Task Manager access was revoked. [Re-authorize]"
5. User re-authorizes through OAuth flow
6. Tasks displayed successfully

**Success Outcome**: Users can revoke and re-grant access cleanly.

## Functional Requirements

### FR1: OAuth 2.1 Authorization Flow

**Requirement**: Implement OAuth 2.1 authorization code flow with PKCE support.

**Details**:
- Support authorization code grant type (not implicit grant)
- Generate cryptographically secure state parameter (prevent CSRF)
- Generate code verifier and code challenge for PKCE (mobile security)
- Redirect user to Google authorization endpoint
- Handle authorization callback with code exchange
- Validate state parameter matches original request

**Acceptance Criteria**:
- Authorization URL includes all required parameters (client_id, redirect_uri, response_type=code, scope, state, code_challenge, code_challenge_method)
- State parameter is verified on callback to prevent CSRF attacks
- PKCE code verifier successfully exchanges authorization code for tokens
- Invalid state parameters are rejected with clear error message

### FR2: Token Management

**Requirement**: Securely store, validate, and refresh OAuth tokens.

**Details**:
- Store access tokens, refresh tokens, and expiration timestamps
- Validate access token on every MCP tool call (except initialize)
- Automatically refresh expired access tokens using refresh token
- Handle token refresh failures gracefully (prompt re-authentication)
- Store tokens encrypted or use secure session storage

**Acceptance Criteria**:
- Access tokens validated before processing any task operation
- Expired tokens trigger automatic refresh without user action
- Refresh token failures result in clear re-authentication prompt
- Tokens are not logged or exposed in error messages
- Token expiration is checked before making Google API calls

### FR3: User Identification and Data Isolation

**Requirement**: Extract authenticated user identity from OAuth token and isolate user data.

**Details**:
- Exchange access token for user profile from Google (email, user ID)
- Use Google user ID as primary user identifier
- Associate all tasks with authenticated user ID
- Ensure all database queries filter by authenticated user ID
- Create user record if first-time authentication

**Acceptance Criteria**:
- Each user sees only their own tasks (no cross-user data leakage)
- User identity is extracted from Google token claims (sub field)
- Database queries always include WHERE user_id = <authenticated_user>
- New users can create account automatically on first auth
- User email is stored for display/admin purposes

### FR4: Dynamic Client Registration

**Requirement**: Support Dynamic Client Registration for mobile and desktop clients.

**Details**:
- Implement OAuth 2.0 Dynamic Client Registration protocol (RFC 7591)
- Register temporary clients on-demand for mobile/desktop apps
- Return client_id and client_secret to calling application
- Set appropriate redirect URIs for different client types
- Expire unused dynamic clients after 30 days

**Acceptance Criteria**:
- Mobile apps can request client registration without pre-configuration
- Registration endpoint returns valid client credentials
- Dynamic clients work identically to pre-registered clients
- Unused clients are automatically cleaned up
- Client metadata (platform, version) is captured for analytics

### FR5: Selective Authentication

**Requirement**: MCP initialize method works without authentication; all tool calls require authentication.

**Details**:
- Allow unauthenticated `initialize` method (returns server info)
- Allow unauthenticated `tools/list` method (lists available tools)
- Require authentication for all `tools/call` operations
- Return HTTP 401 Unauthorized for unauthenticated tool calls
- Include authentication instructions in error response

**Acceptance Criteria**:
- `POST / {"method": "initialize"}` succeeds without token
- `POST / {"method": "tools/list"}` succeeds without token
- `POST / {"method": "tools/call", ...}` returns 401 without valid token
- Error response includes OAuth authorization URL
- Authenticated requests include Authorization: Bearer <token> header

### FR6: Session Management

**Requirement**: Maintain OAuth session state across requests.

**Details**:
- Generate session ID on first authentication
- Associate session with user ID and OAuth tokens
- Include session ID in MCP-Session-Id header
- Extend session expiration on activity (sliding window)
- Clear session on explicit logout or token revocation

**Acceptance Criteria**:
- Session persists for 24 hours of inactivity
- Each request with valid token extends session expiration
- Session ID is cryptographically random (128-bit minimum)
- Logout endpoint clears session and revokes tokens
- Sessions survive server restarts (persisted to database)

### FR7: Error Handling and User Guidance

**Requirement**: Provide clear error messages and authentication guidance.

**Details**:
- Return user-friendly error messages for auth failures
- Include authorization URL in authentication errors
- Distinguish between expired tokens and invalid tokens
- Provide different messages for revoked vs. expired access
- Log authentication errors for debugging (without exposing tokens)

**Acceptance Criteria**:
- 401 Unauthorized includes message: "Authentication required. Click here to authorize: <URL>"
- 403 Forbidden (revoked) includes message: "Access revoked. Click here to re-authorize: <URL>"
- Expired token errors automatically trigger refresh attempt
- Error messages never expose access tokens or refresh tokens
- All auth errors are logged with user_id and timestamp (tokens redacted)

## Success Criteria

1. **Secure Authentication**: 100% of tool calls verify valid OAuth 2.1 token before execution
2. **User Data Isolation**: Zero cross-user data leakage incidents in security testing
3. **Transparent Token Refresh**: Users experience zero authentication interruptions during 4-hour usage sessions
4. **Multi-Platform Support**: Users successfully authenticate from web, mobile, and desktop clients
5. **Quick Authentication**: OAuth flow completes in under 10 seconds from authorization click to first task operation
6. **Session Persistence**: User sessions survive server restarts without requiring re-authentication
7. **Clear Error Recovery**: Users successfully recover from all authentication error scenarios (expired, revoked, invalid) without developer intervention

## Key Entities

### User
- **user_id** (string, primary key): Google user ID (sub claim from token)
- **email** (string): Google account email
- **name** (string, optional): Display name from Google profile
- **created_at** (datetime): First authentication timestamp
- **last_login** (datetime): Most recent authentication

### Session
- **session_id** (string, primary key): Cryptographically random session identifier
- **user_id** (string, foreign key): Associated user
- **access_token** (string, encrypted): Google OAuth access token
- **refresh_token** (string, encrypted): Google OAuth refresh token
- **expires_at** (datetime): Access token expiration
- **created_at** (datetime): Session creation time
- **last_activity** (datetime): Most recent request with this session
- **user_agent** (string, optional): Client information

### DynamicClient (for mobile/desktop)
- **client_id** (string, primary key): Generated client identifier
- **client_secret** (string, encrypted): Generated client secret
- **platform** (string): Client platform (ios, android, desktop)
- **redirect_uris** (json): Allowed redirect URIs
- **created_at** (datetime): Registration time
- **expires_at** (datetime): Client credential expiration (30 days)
- **last_used** (datetime, nullable): Most recent usage

## Non-Functional Requirements

### Security
- All tokens encrypted at rest using AES-256
- HTTPS required for all OAuth callbacks
- PKCE mandatory for mobile/public clients
- State parameter validated on every OAuth callback
- Token rotation on refresh (refresh tokens are single-use)
- Rate limiting on authentication endpoints (10 requests/minute per IP)

### Performance
- OAuth token validation completes in <50ms
- Token refresh completes in <500ms
- Session lookup cached in memory (invalidated on write)
- Database queries use indexed user_id field

### Compatibility
- Supports Google OAuth 2.1 specification
- Compatible with MCP SDK 1.0.0+
- Works with FastAPI 0.115.0+
- Browser redirect URIs follow OAuth 2.1 best practices

### Monitoring
- Log all authentication events (login, logout, token refresh, revocation)
- Track authentication success/failure rates
- Monitor token refresh failures (alert if >5% failure rate)
- Capture OAuth error codes for debugging

## Dependencies

### Required Before Implementation
- Phase 1 complete (basic MCP server functional)
- Google Cloud Platform project created
- OAuth 2.0 credentials configured in Google Cloud Console
- Redirect URIs registered for web/mobile/desktop clients

### New Dependencies
- `google-auth>=2.35.0` - Google OAuth library
- `google-auth-oauthlib>=1.2.0` - OAuth flow helpers
- `cryptography>=44.0.0` - Token encryption
- `pyjwt>=2.10.0` - JWT token validation

### Environment Variables
- `GOOGLE_CLIENT_ID` - OAuth client ID from Google Console
- `GOOGLE_CLIENT_SECRET` - OAuth client secret
- `OAUTH_REDIRECT_URI` - Callback URL for web clients
- `ENCRYPTION_KEY` - 32-byte key for token encryption

## Assumptions

1. **Google OAuth Availability**: Google OAuth services are available 99.9% of the time
2. **HTTPS in Production**: Production deployment uses HTTPS for all OAuth callbacks
3. **Browser Sessions**: Web users accept cookies for session management
4. **Token Lifespan**: Google access tokens expire in 1 hour (standard Google OAuth behavior)
5. **Refresh Token Validity**: Google refresh tokens remain valid until explicitly revoked
6. **Single Identity Provider**: Only Google OAuth supported in Phase 2 (other providers in future phases)
7. **Email Scope Sufficient**: Requesting only email and profile scopes (no calendar access yet - that's calendar integration feature)
8. **Session Storage**: Session data fits in database (PostgreSQL can handle millions of sessions)
9. **Client Secret Security**: Client secrets for dynamic registration are transmitted securely over HTTPS
10. **User Consent**: Users understand and accept permissions requested during OAuth flow

## Out of Scope

The following are explicitly NOT part of this feature:

- **Multi-factor authentication (MFA)**: Google handles MFA at their OAuth layer
- **Social login providers**: Only Google OAuth (GitHub, Microsoft, Apple in future)
- **Role-based access control (RBAC)**: Single-user tasks only (no shared tasks/teams)
- **Calendar integration**: Separate feature (uses OAuth for Calendar API access)
- **Password-based authentication**: OAuth-only (no email/password login)
- **Single Sign-On (SSO)**: Enterprise SSO in future phase
- **Biometric authentication**: Handled by Google/OS, not Task Manager
- **API key authentication**: OAuth tokens only (no API keys for Phase 2)
- **Anonymous task access**: All users must authenticate

## Technical Constraints

1. **OAuth 2.1 Only**: No support for OAuth 1.0 or deprecated implicit grant flow
2. **Token Storage**: Tokens stored encrypted in database (not in-memory only)
3. **PKCE Mandatory**: Mobile and desktop clients must use PKCE
4. **State Parameter**: All OAuth flows must include cryptographically random state
5. **Token Expiration**: Must handle Google's 1-hour access token expiration
6. **Redirect URI Validation**: Only pre-registered URIs accepted for OAuth callbacks
7. **Scope Restrictions**: Request minimal scopes (email + profile, no unnecessary permissions)
8. **Session Limit**: Maximum 10 concurrent sessions per user
9. **Token Rotation**: Refresh tokens are single-use (Google rotates on refresh)
10. **Error Logging**: Auth errors logged but tokens redacted (PII/security)

## Migration from Phase 1

**Current State**: Phase 1 uses mock authentication with hardcoded `user_id = "dev-user"`.

**Migration Strategy**:
1. All existing tasks in database associated with `user_id = "dev-user"`
2. Create a real Google user account for testing
3. On first OAuth authentication, associate `user_id = "dev-user"` with test Google account
4. Future users start with empty task list
5. No data loss for Phase 1 test data

**Breaking Changes**:
- MCP clients must include OAuth token in tool calls (previously no auth required)
- Direct API testing requires obtaining OAuth token first (can't use curl without token)
- Development mode requires valid Google OAuth credentials (no anonymous access)

## Reference Documentation

- OAuth 2.1: https://oauth.net/2.1/
- Google OAuth 2.0: https://developers.google.com/identity/protocols/oauth2
- Dynamic Client Registration: https://datatracker.ietf.org/doc/html/rfc7591
- PKCE Specification: https://datatracker.ietf.org/doc/html/rfc7636
- MCP Authentication: https://spec.modelcontextprotocol.io/specification/architecture/#authentication
