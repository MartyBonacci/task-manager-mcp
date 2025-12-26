# Quality Standards: Task Manager MCP Server

**Version**: 1.0.0
**Created**: 2025-12-25
**Status**: Active
**Quality Level**: Standard

## Overview

This document defines the quality gates, performance budgets, and code standards that all code must meet before being merged to the main branch. These standards are enforced by `/specswarm:ship` and CI/CD pipelines.

**Goal**: Maintain production-grade quality throughout development lifecycle.

## Quality Gates

### 1. Code Quality Score

**Minimum Score**: 80/100
**Enforced**: Yes
**Measured By**: SpecSwarm analyze-quality

Quality score is calculated from:
- Code complexity (cyclomatic complexity)
- Code duplication
- Maintainability index
- Documentation coverage
- Type hint coverage

**Threshold Breakdown**:
- **90-100**: Excellent - Highly maintainable code
- **80-89**: Good - Meets production standards ✅ (Required)
- **70-79**: Fair - Needs improvement
- **Below 70**: Poor - Must refactor before merge

### 2. Test Coverage

**Minimum Coverage**: 80%
**Enforced**: Yes
**Measured By**: pytest with coverage plugin

Coverage requirements:
- **Line Coverage**: ≥80% of executable lines tested
- **Branch Coverage**: ≥75% of conditional branches tested
- **Function Coverage**: 100% of public functions have at least one test

**Exemptions**:
- Configuration files (`config/settings.py`)
- Database migration scripts
- `__init__.py` files (if only imports)
- Development scripts (`scripts/`)

Run coverage report:
```bash
pytest --cov=app --cov-report=html --cov-report=term
open htmlcov/index.html  # View detailed report
```

### 3. Type Safety

**Requirement**: 100% type hint coverage
**Enforced**: Yes
**Checked By**: mypy in strict mode

All code must pass:
```bash
mypy app/ --strict --no-error-summary
```

**Type Hints Required**:
- All function signatures (args and return types)
- All class attributes
- All module-level variables
- No `Any` types without justification comment

**Example**:
```python
# ✅ Correct
async def create_task(
    db: Session,
    user_id: str,
    task_data: TaskCreate
) -> Task:
    ...

# ❌ Wrong - missing type hints
async def create_task(db, user_id, task_data):
    ...
```

### 4. Linting

**Enforced**: Yes
**Tools**: ruff (linter) + black (formatter)

Must pass without errors:
```bash
ruff check app/
black --check app/
```

**Style Guide**: PEP 8 with project-specific rules
**Line Length**: 100 characters (configured in pyproject.toml)
**Import Order**: isort compatible (stdlib, third-party, local)

### 5. Security Scan

**Enforced**: Yes
**Tools**: bandit (security linter) + safety (dependency checker)

No high or medium severity issues allowed:
```bash
bandit -r app/ -ll  # Check for security issues
safety check        # Check for vulnerable dependencies
```

**Common Security Requirements**:
- No hardcoded secrets or credentials
- All inputs validated via Pydantic
- SQL injection prevented (ORM only)
- User isolation enforced
- Secrets in environment variables only

## Performance Budgets

### API Response Times

**Enforced**: Yes (in production monitoring)

| Endpoint | p50 | p95 | p99 |
|----------|-----|-----|-----|
| GET /health | <50ms | <100ms | <200ms |
| POST / (initialize) | <100ms | <200ms | <500ms |
| POST / (tools/list) | <50ms | <100ms | <200ms |
| POST / (tools/call) | <200ms | <500ms | <1000ms |

**Notes**:
- p50 = median response time
- p95 = 95th percentile (most requests)
- p99 = 99th percentile (worst case)
- Measured under normal load (10 concurrent users)

### Database Query Performance

**Maximum Query Time**: 100ms (p95)
**Enforced**: Via monitoring and indexing

All database queries must use proper indexes:
- `user_id` (always indexed)
- `completed` (status filtering)
- `priority` (sorting)
- `due_date` (filtering)
- `project` (filtering)

Run query analysis:
```bash
# SQLite
EXPLAIN QUERY PLAN SELECT ...

# PostgreSQL
EXPLAIN ANALYZE SELECT ...
```

### Memory Usage

**Maximum Memory**: 512MB per container instance
**Enforced**: Cloud Run resource limits

**Guidelines**:
- No memory leaks (test with long-running processes)
- Proper connection pooling (max 10 connections)
- Pagination for large result sets (max 100 items per page)
- Close database sessions properly

### Container Image Size

**Maximum Size**: 200MB compressed
**Current**: ~100MB (Python 3.11-slim base)
**Enforced**: Docker build pipeline

Use multi-stage builds:
```dockerfile
FROM python:3.11-slim as builder
# ... build dependencies

FROM python:3.11-slim
# ... copy only needed artifacts
```

## Code Complexity Standards

### Cyclomatic Complexity

**Maximum**: 10 per function
**Recommended**: ≤5 per function
**Enforced**: Yes (via ruff and code review)

**What it measures**: Number of independent paths through code
**Why it matters**: Complex functions are hard to test and maintain

**If complexity > 10**:
- Break into smaller functions
- Extract conditional logic
- Use early returns
- Consider strategy pattern for complex branching

### Function Length

**Maximum**: 50 lines of code
**Recommended**: ≤30 lines
**Enforced**: Code review

**If function exceeds 50 lines**:
- Extract helper functions
- Consider if function has too many responsibilities
- Split into logical sub-operations

### File Length

**Maximum**: 300 lines of code
**Recommended**: ≤200 lines
**Enforced**: Code review

**If file exceeds 300 lines**:
- Split into multiple modules
- Separate concerns (e.g., CRUD operations vs business logic)
- Consider if module is doing too much

### Function Parameters

**Maximum**: 5 parameters
**Recommended**: ≤3 parameters
**Enforced**: Code review

**If function needs >5 parameters**:
- Use Pydantic model to group related parameters
- Consider if function signature is too complex
- Extract parameter object pattern

## Testing Requirements

### Test Coverage by Type

**Unit Tests**: 80%+ of service layer code
- Test business logic in isolation
- Mock database and external dependencies
- Fast execution (milliseconds per test)

**Integration Tests**: All MCP protocol endpoints
- Test initialize, tools/list, tools/call
- Test error handling
- Test with real database (test fixtures)

**End-to-End Tests**: Critical user workflows
- Create task → list tasks → complete task
- User isolation (can't access other user's tasks)
- OAuth flow (in Phase 2)

### Test Quality

All tests must:
- ✅ Have descriptive names (`test_create_task_with_valid_data`)
- ✅ Follow Arrange-Act-Assert pattern
- ✅ Be independent (no shared state between tests)
- ✅ Be deterministic (same input = same output)
- ✅ Clean up after themselves (database transactions)

Example:
```python
async def test_create_task_with_valid_data():
    # Arrange
    db = get_test_db()
    user_id = "test-user"
    task_data = TaskCreate(title="Test task", priority=4)

    # Act
    service = TaskService(db, user_id)
    result = service.create_task(task_data)

    # Assert
    assert result.title == "Test task"
    assert result.priority == 4
    assert result.user_id == user_id
```

### Test Execution

All tests must pass:
```bash
pytest -v                    # Run all tests
pytest tests/test_tasks.py   # Run specific file
pytest -k "create"           # Run tests matching pattern
pytest --lf                  # Run last failed tests
```

## Code Review Standards

### Required Reviews

**Minimum Reviewers**: 1 (for production-critical changes: 2)
**Enforced**: Yes (GitHub branch protection)

All code must be reviewed before merge:
- ✅ Meets quality gates (coverage, type hints, linting)
- ✅ Follows architectural principles from constitution.md
- ✅ Uses approved technologies from tech-stack.md
- ✅ Has appropriate tests
- ✅ Documentation updated if needed

### Review Checklist

Reviewers must verify:
- [ ] Code follows DRY principle (no unnecessary duplication)
- [ ] Functions have single responsibility
- [ ] Error handling is comprehensive
- [ ] No security vulnerabilities introduced
- [ ] Database queries are optimized
- [ ] User isolation is enforced
- [ ] MCP protocol compliance maintained
- [ ] Type hints are complete and correct
- [ ] Tests cover new functionality
- [ ] Documentation is clear and accurate

## CI/CD Requirements

### Continuous Integration

**All Checks Must Pass**:
```bash
# 1. Type checking
mypy app/ --strict

# 2. Linting
ruff check app/
black --check app/

# 3. Security scanning
bandit -r app/ -ll
safety check

# 4. Tests
pytest --cov=app --cov-report=term --cov-fail-under=80

# 5. Quality score
# Verified by SpecSwarm analyze-quality
```

### Continuous Deployment

**Deployment Triggers**: Merge to main branch
**Deployment Blocker**: Any failing CI check

**Deployment Stages**:
1. Run all CI checks ✅
2. Build Docker image
3. Push to Google Container Registry
4. Deploy to Cloud Run (with health checks)
5. Run smoke tests against production
6. Rollback if smoke tests fail

## Custom Checks

### MCP Protocol Compliance

**Enforced**: Yes (integration tests)

All MCP responses must:
- Include correct protocol version header
- Use proper error codes for failures
- Return content in correct format
- Handle sessions properly
- Support all required methods

Test with:
```bash
python scripts/test_mcp_compliance.py
```

### User Isolation Verification

**Enforced**: Yes (security tests)

Every endpoint that accesses user data must:
- Validate user_id from OAuth token
- Filter database queries by user_id
- Prevent cross-user data access

Test with:
```bash
pytest tests/test_user_isolation.py
```

### Performance Regression Testing

**Enforced**: Yes (in CI/CD)

Monitor for performance degradation:
- Database query count (should not increase without reason)
- Response time (should not exceed budgets)
- Memory usage (should not grow unbounded)

## Exemptions

### Temporary Exemptions

Exemptions may be granted for:
- **Prototype code**: Marked with `# PROTOTYPE` and GitHub issue
- **Phase 1 shortcuts**: Mock auth before OAuth implementation
- **External API quirks**: Document workarounds

**All exemptions must**:
- Have associated GitHub issue
- Include TODO comment with issue number
- Have target resolution date
- Be tracked in project board

### Permanent Exemptions

Currently no permanent exemptions granted.

**To request permanent exemption**:
1. Create GitHub issue with justification
2. Discuss with team
3. Document in this file if approved

## Monitoring & Metrics

### Production Monitoring

**Required Metrics**:
- Request rate (requests/second)
- Error rate (errors/total requests)
- Response time (p50, p95, p99)
- Database connection pool usage
- Memory usage
- CPU usage

**Alerting Thresholds**:
- Error rate >1%: Warning
- Error rate >5%: Critical
- p95 response time >1s: Warning
- Memory usage >80%: Warning

### Quality Metrics

**Tracked Over Time**:
- Test coverage trend
- Code quality score trend
- Dependency vulnerability count
- Technical debt (TODO/FIXME comments)

**Review Quarterly**:
- Adjust quality thresholds if needed
- Identify areas for improvement
- Celebrate quality improvements

## Tools Configuration

### pytest Configuration

`.pytest.ini` or `pyproject.toml`:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = [
    "--strict-markers",
    "--cov=app",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-fail-under=80",
]
```

### mypy Configuration

`pyproject.toml`:
```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### ruff Configuration

`pyproject.toml`:
```toml
[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]  # Line too long (handled by black)
```

## Notes

- Quality standards apply to all phases of development
- Standards may be relaxed for Phase 1 prototyping (document exemptions)
- Re-evaluate standards after Phase 4 (production readiness)
- Quality gates are enforced by `/specswarm:ship` workflow

## Changelog

### v1.0.0 (2025-12-25)
- Initial quality standards established
- 80% test coverage requirement
- 80/100 minimum quality score
- Type safety enforced with mypy --strict
- Performance budgets defined
- Code complexity limits set
