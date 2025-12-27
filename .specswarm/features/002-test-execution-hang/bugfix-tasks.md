# Tasks: Bug 002 - Test Execution Hang

**Workflow**: Bugfix (Regression-Test-First)
**Status**: Active
**Created**: 2025-12-26

---

## Execution Strategy

**Mode**: Sequential (critical infrastructure fix)
**Smart Integration**: SpecSwarm detected (tech stack validation enabled)

---

## Phase 1: Regression Test Creation

### T001: Verify Regression Test Exists
**Description**: Confirm regression test file already created
**File**: `tests/test_regression_conftest_hang.py`
**Validation**: File exists and contains 3 test functions
**Status**: ✅ COMPLETE (created in /specswarm:fix workflow)
**Parallel**: No (foundational)

### T002: Verify Test Reproduces Hang
**Description**: Run regression test with timeout to confirm hang bug exists
**Command**: `timeout 15 ./venv/bin/pytest tests/test_regression_conftest_hang.py::test_simple_database_operation_completes -v`
**Expected**: Test passes but pytest hangs (timeout kills process with exit code 124)
**Validation**: Exit code 124 proves hang exists
**Status**: ✅ COMPLETE (hang confirmed)
**Parallel**: No (depends on T001)

---

## Phase 2: Bug Fix Implementation

### T003: Implement Engine Disposal Fixture
**Description**: Add session-scoped fixture to dispose test_engine after all tests
**File**: `tests/conftest.py`
**Changes**:
1. Add after line 35 (after TestAsyncSessionLocal creation):
```python
@pytest_asyncio.fixture(scope="session", autouse=True)
async def cleanup_engine():
    """
    Clean up test engine after all tests complete.

    This fixture runs automatically at session scope and ensures
    the async engine is properly disposed, allowing pytest to exit cleanly.
    """
    yield  # Run all tests first

    # After all tests complete, dispose the engine
    await test_engine.dispose()
```
**Tech Stack Validation**: Uses approved pytest-asyncio patterns
**Parallel**: No (core fix)

### T004: Update Event Loop Fixture (Optional)
**Description**: Improve event loop fixture with modern asyncio patterns
**File**: `tests/conftest.py`
**Changes**:
1. Update event_loop fixture (lines 38-47):
```python
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for test session with proper cleanup."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()
```
**Tech Stack Validation**: Uses standard asyncio patterns
**Parallel**: Yes [P] (optional improvement, independent from T003)

### T005: Add Pytest Configuration
**Description**: Add pytest-asyncio configuration to pyproject.toml
**File**: `pyproject.toml`
**Changes**:
1. Add to `[tool.pytest.ini_options]` section:
```toml
asyncio_mode = "auto"
```
**Tech Stack Validation**: Standard pytest configuration
**Parallel**: Yes [P] (independent from T003)

---

## Phase 3: Verification

### T006: Verify Test Passes Without Hang
**Description**: Run regression test and confirm pytest completes cleanly
**Command**: `./venv/bin/pytest tests/test_regression_conftest_hang.py::test_simple_database_operation_completes -v`
**Expected**:
- Test passes
- pytest completes in < 5 seconds
- Exit code 0 (success, not 124)
**Validation**: Clean completion proves bug fixed
**Parallel**: No (depends on T003)

### T007: Verify Full Regression Test Suite Passes
**Description**: Run all 3 regression tests to ensure no resource leaks
**Command**: `./venv/bin/pytest tests/test_regression_conftest_hang.py -v`
**Expected**: All 3 tests pass, pytest completes cleanly
**Validation**: All tests pass without hangs
**Parallel**: No (depends on T006)

### T008: Verify Full Test Suite Completes
**Description**: Run entire test suite to ensure no regressions
**Command**: `./venv/bin/pytest tests/ -v`
**Expected**: All tests pass (existing + new regression tests)
**Validation**: 100% test pass rate, no hangs
**Parallel**: No (final validation)

---

## Summary

**Total Tasks**: 8 tasks
**Estimated Time**: 30-45 minutes
**Parallel Opportunities**: T004-T005 [P] (optional improvements)

**Success Criteria**:
- ✅ Regression test created (T001) ✓
- ✅ Test reproduced hang (T002) ✓
- ✅ Engine disposal fixture added (T003)
- ✅ Event loop improved (T004 - optional)
- ✅ Pytest configured (T005 - optional)
- ✅ Regression test passes (T006)
- ✅ All regression tests pass (T007)
- ✅ Full suite passes (T008)
- ✅ Tech stack compliant

**Tech Stack Compliance**: All fixes use approved technologies (pytest-asyncio, SQLAlchemy async, standard pytest patterns)
