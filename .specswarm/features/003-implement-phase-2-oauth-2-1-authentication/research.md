# Research: OAuth 2.1 Authentication with Google

**Feature**: 003 - OAuth 2.1 Authentication
**Created**: 2025-12-26
**Status**: Complete

---

## Overview

This document contains research findings and technical decisions for implementing OAuth 2.1 authentication with Google as the identity provider for the Task Manager MCP Server.

---

## Research Objectives

1. Determine correct OAuth 2.1 flow for MCP server authentication
2. Identify required Google OAuth libraries and their capabilities
3. Clarify JWT token validation strategy (native vs. third-party libraries)
4. Establish session management approach (JWT-based vs. database-backed)
5. Validate Dynamic Client Registration requirements for mobile/desktop clients

---

## Key Research Findings

### Finding 1: JWT Token Validation Strategy

**Decision**: Use native Google OAuth library JWT validation (google-auth library)

**Rationale**:
- **google-auth library includes native JWT validation** via `google.auth.jwt` module
- Google ID tokens are validated using `google.oauth2.id_token.verify_oauth2_token()`
- **No separate JWT library needed** for OAuth 2.1 token validation
- python-jose retained in tech stack for potential future use cases:
  - API key generation (if implemented in later phases)
  - Webhook signature verification
  - Stateless session tokens (if migration from database sessions)

**Alternative Considered**: pyjwt library
- **Rejected**: Redundant with google-auth native capabilities
- Adds unnecessary dependency
- Same functionality as python-jose (already in stack)
- Spec writer incorrectly assumed separate JWT library needed

**Implementation Impact**:
```python
# ✅ Correct: Use google-auth native validation
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# Validate Google ID token
idinfo = id_token.verify_oauth2_token(
    token_string,
    google_requests.Request(),
    GOOGLE_CLIENT_ID
)
user_id = idinfo['sub']  # Google user ID
user_email = idinfo['email']

# ❌ NOT needed: Separate JWT library for Google tokens
# import jwt  # pyjwt - NOT required
# decoded = jwt.decode(token, ...)  # google-auth does this
```

**References**:
- [google-auth JWT module documentation](https://google-auth.readthedocs.io/en/latest/reference/google.auth.jwt.html)
- [Google ID token validation guide](https://developers.google.com/identity/protocols/oauth2/openid-connect#validatinganidtoken)

---

### Finding 2: Session Management Architecture

**Decision**: Database-backed sessions (NOT JWT-based sessions)

**Rationale**:
- **OAuth tokens stored encrypted in database** (Session table)
- Session identified by cryptographically random `session_id`
- Database storage enables:
  - Token revocation on logout
  - Session expiration management (24-hour inactivity timeout)
  - Session persistence across server restarts
  - Audit trail (last_activity, created_at timestamps)
- MCP server architecture benefits from stateful sessions (not RESTful API)

**Alternative Considered**: JWT-based stateless sessions
- **Rejected**: Cannot revoke sessions without blacklist (defeats stateless purpose)
- Tokens cannot be rotated/refreshed without new JWT issue
- No audit trail for session activity
- Exposes token lifetime in JWT claims (security concern)

**Implementation Impact**:
- Session table schema defined in spec.md (lines 241-248)
- Encrypted token storage using cryptography library (AES-256)
- Session lookup on every MCP tool call
- No custom JWT creation needed (only Google token validation)

---

### Finding 3: OAuth 2.1 Flow Libraries

**Decision**: Use google-auth + google-auth-oauthlib

**Libraries Selected**:
1. **google-auth v2.35.0+**:
   - Core OAuth 2.1 credential management
   - Token validation and refresh
   - Native JWT support

2. **google-auth-oauthlib v1.2.0+**:
   - OAuth authorization code flow helpers
   - PKCE (Proof Key for Code Exchange) support for mobile clients
   - Simplifies redirect URI handling
   - Credential refresh utilities

**Rationale**:
- Official Google libraries (maintained by Google)
- Designed specifically for Google OAuth integration
- PKCE support required for mobile/desktop Dynamic Client Registration
- Well-documented with extensive examples

**Alternative Considered**: authlib
- **Rejected**: Generic OAuth library (not Google-optimized)
- Requires more configuration for Google-specific flows
- google-auth-oauthlib is simpler for our use case

---

### Finding 4: Dynamic Client Registration

**Decision**: Implement RFC 7591 Dynamic Client Registration

**Requirements**:
- Mobile and desktop clients cannot pre-register OAuth credentials securely
- Server generates temporary client credentials on-demand
- Clients register with metadata (platform, redirect_uri)
- 30-day expiration for unused dynamic clients

**Implementation Approach**:
1. POST /oauth/register endpoint
2. Validate request metadata (platform, redirect_uris)
3. Generate client_id (UUID) and client_secret (cryptographically secure)
4. Store in DynamicClient table (encrypted client_secret)
5. Return credentials to client
6. Client uses credentials for standard OAuth flow

**Reference**: [RFC 7591 - OAuth 2.0 Dynamic Client Registration Protocol](https://datatracker.ietf.org/doc/html/rfc7591)

---

### Finding 5: PKCE for Public Clients

**Decision**: Mandatory PKCE for mobile and desktop clients

**PKCE Flow**:
1. Client generates random `code_verifier` (43-128 characters)
2. Client computes `code_challenge = BASE64URL(SHA256(code_verifier))`
3. Authorization request includes `code_challenge` and `code_challenge_method=S256`
4. Token exchange includes original `code_verifier`
5. Server validates: `code_challenge == BASE64URL(SHA256(code_verifier))`

**Rationale**:
- Prevents authorization code interception attacks
- Required for public clients (mobile/desktop apps)
- OAuth 2.1 best practice (mandatory in OAuth 2.1 spec)

**Library Support**: google-auth-oauthlib handles PKCE automatically

**Reference**: [RFC 7636 - Proof Key for Code Exchange](https://datatracker.ietf.org/doc/html/rfc7636)

---

## Technology Choices Summary

| Requirement | Technology | Version | Rationale |
|-------------|-----------|---------|-----------|
| OAuth 2.1 Core | google-auth | 2.35.0+ | Native Google OAuth, JWT validation |
| OAuth Flow Helpers | google-auth-oauthlib | 1.2.0+ | Authorization code flow, PKCE support |
| Token Encryption | cryptography | 44.0.0+ | AES-256 for database token storage |
| JWT Operations | python-jose[cryptography] | 3.3.0+ | Future use (API keys, webhooks) |
| Session Storage | SQLAlchemy (existing) | 2.0.23+ | Database-backed sessions |

---

## Open Questions Resolved

### Q1: Do we need a separate JWT library for token validation?
**A**: No. google-auth library provides native JWT validation via `google.auth.jwt` module. python-jose retained for potential future features (API keys, webhook signatures) but not required for OAuth 2.1 implementation.

### Q2: JWT sessions vs. database sessions?
**A**: Database-backed sessions. OAuth tokens stored encrypted in Session table. Enables revocation, audit trails, and persistence across server restarts.

### Q3: Which OAuth library for Google authentication?
**A**: google-auth + google-auth-oauthlib. Official Google libraries with PKCE support and simplified OAuth flows.

### Q4: How to handle mobile client authentication?
**A**: Dynamic Client Registration (RFC 7591) + PKCE. Server generates temporary credentials on-demand. PKCE prevents code interception.

### Q5: State parameter management for CSRF protection?
**A**: Generate cryptographically secure random state (128-bit minimum). Store in session before redirect. Validate on callback. Reject mismatched state.

---

## Security Considerations

1. **Token Storage**: All OAuth tokens encrypted at rest (AES-256)
2. **HTTPS Only**: OAuth callbacks require HTTPS in production
3. **State Parameter**: CSRF protection on all OAuth flows
4. **PKCE**: Mandatory for mobile/desktop clients
5. **Token Rotation**: Refresh tokens single-use (Google rotates on refresh)
6. **Session Expiration**: 24-hour inactivity timeout
7. **Rate Limiting**: 10 auth requests/minute per IP

---

## Implementation Phases

### Phase 0: Dependencies (COMPLETE)
- ✅ Tech stack validated
- ✅ google-auth v2.35.0+ approved
- ✅ google-auth-oauthlib v1.2.0+ approved
- ✅ JWT validation strategy clarified

### Phase 1: Database Schema
- Create User, Session, DynamicClient tables
- Implement token encryption utilities
- Database migration scripts

### Phase 2: OAuth Flow Implementation
- Authorization endpoint (redirect to Google)
- Callback endpoint (code exchange)
- Token refresh logic
- Dynamic Client Registration endpoint

### Phase 3: MCP Integration
- Token validation middleware
- User identification from tokens
- Session management
- Error handling (expired, revoked tokens)

### Phase 4: Testing
- Unit tests (token validation, encryption)
- Integration tests (OAuth flow end-to-end)
- Security testing (CSRF, token interception, PKCE)

---

## References

### Official Documentation
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [OAuth 2.1 Specification](https://oauth.net/2.1/)
- [RFC 7591 - Dynamic Client Registration](https://datatracker.ietf.org/doc/html/rfc7591)
- [RFC 7636 - PKCE Specification](https://datatracker.ietf.org/doc/html/rfc7636)
- [MCP Authentication Architecture](https://spec.modelcontextprotocol.io/specification/architecture/#authentication)

### Library Documentation
- [google-auth Python Library](https://google-auth.readthedocs.io/)
- [google-auth-oauthlib Documentation](https://google-auth-oauthlib.readthedocs.io/)
- [python-jose Documentation](https://python-jose.readthedocs.io/)

---

## Changelog

### 2025-12-26
- Initial research completed
- JWT validation strategy clarified (native google-auth, no pyjwt needed)
- Session management architecture decided (database-backed)
- OAuth library selection finalized
- Dynamic Client Registration approach validated
- All open questions resolved
- Ready for implementation planning
