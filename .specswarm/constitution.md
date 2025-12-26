# Project Constitution: Task Manager MCP Server

**Version**: 1.0.0
**Created**: 2025-12-25
**Status**: Active

## Purpose

This constitution defines the governance principles and coding standards for the Task Manager MCP Server project. All code, documentation, and architectural decisions must align with these principles.

## Core Principles

### 1. Type Safety First
- Use Python 3.11+ type hints throughout the codebase
- Leverage Pydantic for runtime validation and data models
- Ensure all function signatures have complete type annotations
- Use mypy for static type checking in CI/CD

**Rationale**: Type safety prevents runtime errors, improves IDE support, and makes the codebase more maintainable as it scales.

### 2. Async by Default
- Use async/await patterns for all I/O operations
- Leverage FastAPI's async capabilities for concurrent request handling
- Implement async database operations with SQLAlchemy 2.0+
- Never block the event loop with synchronous operations

**Rationale**: MCP servers must handle multiple concurrent connections efficiently. Async patterns ensure responsive performance and scalability.

### 3. MCP Specification Compliance
- Strictly adhere to MCP Protocol Specification 2025-06-18
- Implement all required endpoints (HEAD /, POST /)
- Use correct MCP error codes and response formats
- Maintain proper session management per spec
- Test protocol compliance continuously

**Rationale**: Compliance ensures compatibility with Claude.ai, Claude mobile, and Claude Code across all platforms.

### 4. Comprehensive Testing
- Write tests before implementation (TDD encouraged)
- Maintain minimum 80% code coverage
- Include unit, integration, and end-to-end tests
- Test error conditions and edge cases
- Mock external dependencies appropriately

**Rationale**: MCP servers are infrastructure components that must be reliable. Comprehensive testing prevents regressions and ensures production readiness.

### 5. Clear Documentation
- Document all public APIs with docstrings
- Maintain up-to-date README, ARCHITECTURE, and SETUP_GUIDE
- Include inline comments for complex business logic
- Document all MCP tool schemas and behaviors
- Provide examples for all MCP tools

**Rationale**: This project is designed to be educational and reusable. Clear documentation enables others to learn from and extend the codebase.

## Architectural Principles

### Layered Architecture
Maintain strict separation of concerns:
1. **API Layer** (FastAPI) - HTTP handling, routing, middleware
2. **MCP Layer** - Protocol compliance, tool registration, method dispatch
3. **Business Logic Layer** - Task operations, validation, user context
4. **Data Layer** - Database models, queries, transactions
5. **Auth Layer** - OAuth 2.1, token validation, user identification
6. **Config Layer** - Environment-based settings, feature flags

**Never bypass layers** - e.g., MCP handlers should not directly access database models.

### User Isolation
- All database queries MUST filter by `user_id`
- Validate user ownership before any update/delete operation
- Never expose one user's data to another user
- Test user isolation in all service methods

### Error Handling
- Use MCP-compliant error codes and formats
- Provide helpful error messages without exposing internals
- Log errors with context but never log task content (privacy)
- Implement graceful degradation where possible

### Security First
- OAuth 2.1 only (no API keys, no basic auth)
- Input validation via Pydantic schemas
- Parameterized queries only (SQLAlchemy ORM)
- HTTPS in production
- Rate limiting per user
- Secrets in environment variables, never in code

## Development Workflow

### Phase-Based Implementation
Follow the phases defined in PROJECT_SPEC.md:
1. **Phase 1**: Local development with SQLite and mock auth
2. **Phase 2**: HTTP + OAuth 2.1 + Calendar integration
3. **Phase 3**: Cloud deployment (Google Cloud Run)
4. **Phase 4**: Production polish and monitoring
5. **Phase 5**: Birds Eye Dashboard (optional)

**Never skip phases** - each builds on the previous.

### SpecSwarm Orchestration
This project is designed for SpecSwarm multi-agent development:
- Main agent coordinates overall implementation
- Specialist agents handle database, API, MCP, auth, testing
- Agents must read PROJECT_SPEC.md, ARCHITECTURE.md, SETUP_GUIDE.md
- Integration happens at layer boundaries

### Code Review Standards
- All code must pass type checking (mypy)
- All tests must pass (pytest)
- Coverage must meet or exceed 80%
- No TODO comments without GitHub issues
- Follow PEP 8 style guide (enforced by black/ruff)

## Technology Constraints

### Required Stack
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **MCP SDK**: Official MCP Python SDK
- **Database**: SQLAlchemy 2.0+ ORM
- **Auth**: OAuth 2.1 with google-auth
- **Testing**: pytest with pytest-asyncio

### Prohibited Patterns
- ❌ Synchronous database operations
- ❌ Global state or singletons (except config)
- ❌ Circular imports
- ❌ Direct SQL queries (use ORM)
- ❌ Hardcoded credentials or secrets
- ❌ Non-MCP-compliant response formats

## Quality Gates

All code must pass these gates before merge:

1. **Type Safety**: `mypy app/ --strict` passes with no errors
2. **Tests**: `pytest` passes with ≥80% coverage
3. **Linting**: `ruff check app/` passes with no errors
4. **Formatting**: `black --check app/` passes
5. **Security**: No secrets in code, all inputs validated
6. **Documentation**: All public functions have docstrings

## Versioning and Changes

### Constitution Updates
- Changes require team consensus
- Version number increments on changes
- Changelog maintained at bottom of this file
- Never remove principles, only add or refine

### Deviation Requests
If you need to deviate from these principles:
1. Document the reason in code comments
2. Create a GitHub issue explaining the deviation
3. Add a TODO to resolve the deviation
4. Get explicit approval from project lead

## Enforcement

This constitution is enforced by:
- SpecSwarm validation agents (stack-coherence-validator)
- CI/CD pipelines (GitHub Actions)
- Code review process
- Pre-commit hooks (when configured)

Violations should be caught before merge, not after.

---

## Changelog

### v1.0.0 (2025-12-25)
- Initial constitution created
- Established 5 core principles
- Defined architectural constraints
- Set quality gates at 80% coverage
- Specified required technology stack
