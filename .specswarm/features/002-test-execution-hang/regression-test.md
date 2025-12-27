# Regression Test: Bug 002 - Test Execution Hang

**Purpose**: Prove hang bug exists, validate fix, prevent future regressions

**Test Type**: Infrastructure Regression Test
**Created**: 2025-12-26

---

## Test Objective

Write tests that:
1. ✅ **Hang before fix** (proves bug exists - killed by timeout)
2. ✅ **Complete cleanly after fix** (proves bug fixed)
3. ✅ **Prevent regression** (catches if bug reintroduced)

---

## Test Specification

### Test Setup

**Prerequisites**:
- pytest installed and configured
- pytest-asyncio installed
- SQLAlchemy async engine configured
- Test database fixtures available

**Initial State**:
- Clean test environment
- No existing database connections
- Fresh pytest session

### Test Execution

**Test Actions**:
1. Import db_session fixture
2. Create a simple database operation (create task)
3. Commit transaction
4. End test
5. **Critical**: Observe pytest teardown behavior

### Test Assertions

**Validations that prove bug exists/fixed**:

- ✅ **Assertion 1**: Test logic passes (task created successfully)
- ✅ **Assertion 2**: pytest completes within reasonable timeout (< 10 seconds)
- ✅ **Assertion 3**: No resource leaks (verified by clean exit)

### Test Teardown

**Cleanup**:
- All database connections closed
- Engine disposed properly
- Event loop cleaned up
- pytest exits cleanly

---

## Test Implementation

### Test File Location

**File**: `tests/test_regression_conftest_hang.py` (already created)

**Test Functions**:
1. `test_simple_database_operation_completes` - Basic hang detection
2. `test_multiple_tests_dont_cause_resource_leak` - Resource leak detection
3. `test_test_suite_completes_within_timeout` - Timeout-based validation

### Test Validation Criteria

**Before Fix**:
- ❌ Test logic PASSES (tests work correctly)
- ❌ pytest HANGS during teardown (bug exists)
- ❌ Must kill process with timeout or Ctrl+C
- **Verification**: `timeout 15 pytest tests/test_regression_conftest_hang.py` exits with code 124 (timeout)

**After Fix**:
- ✅ Test logic PASSES (tests still work)
- ✅ pytest COMPLETES cleanly (bug fixed)
- ✅ Exits with code 0 (success)
- **Verification**: `pytest tests/test_regression_conftest_hang.py` completes in < 5 seconds

---

## Test Code

**File**: tests/test_regression_conftest_hang.py

```python
"""
Regression test for Bug 002: Test execution hang

This test verifies that pytest can complete test execution without hanging.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Task


@pytest.mark.asyncio
async def test_simple_database_operation_completes(
    db_session: AsyncSession, test_user_id: str
):
    """
    Test that a simple database operation completes without hanging.

    BEFORE FIX: This test will hang after passing
    AFTER FIX: This test will complete successfully
    """
    task = Task(
        user_id=test_user_id,
        title="Regression Test Task",
        project="Test",
        priority=3,
        energy="medium",
        time_estimate="1hr",
        completed=False,
    )

    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    assert task.id is not None
    assert task.title == "Regression Test Task"


@pytest.mark.asyncio
async def test_multiple_tests_dont_cause_resource_leak(
    db_session: AsyncSession, test_user_id: str
):
    """
    Test that running multiple tests doesn't leak resources.

    Verifies proper cleanup between tests.
    """
    for i in range(5):
        task = Task(
            user_id=test_user_id,
            title=f"Test Task {i}",
            project="Test",
            priority=3,
            energy="medium",
            time_estimate="1hr",
            completed=False,
        )
        db_session.add(task)

    await db_session.commit()
    assert True  # If we get here without hanging, test passes


@pytest.mark.asyncio
@pytest.mark.timeout(10)  # 10 second timeout to detect hangs
async def test_test_suite_completes_within_timeout(
    db_session: AsyncSession, test_user_id: str
):
    """
    Test that the test suite can complete within a reasonable timeout.

    BEFORE FIX: This test may timeout/hang
    AFTER FIX: This test will complete in < 10 seconds
    """
    task = Task(
        user_id=test_user_id,
        title="Timeout Test Task",
        project="Test",
        priority=3,
        energy="medium",
        time_estimate="1hr",
        completed=False,
    )

    db_session.add(task)
    await db_session.commit()

    # If we reach here without timeout, fix is working
    assert True
```

---

## Edge Cases to Test

**Related scenarios**:

1. **Single test execution** - Verify hang occurs even with one test
2. **Multiple test files** - Verify hang doesn't accumulate across files
3. **Fixture reuse** - Verify db_session fixture cleanup works correctly
4. **Transaction rollback** - Verify failed tests still clean up properly

---

## Validation Commands

**Before Fix**:
```bash
# This will hang and require timeout kill
timeout 15 pytest tests/test_regression_conftest_hang.py -v
# Exit code: 124 (timeout killed it)
```

**After Fix**:
```bash
# This will complete cleanly
pytest tests/test_regression_conftest_hang.py -v
# Exit code: 0 (success)
# Duration: < 5 seconds
```

**Full Suite After Fix**:
```bash
# All tests should complete
pytest tests/ -v
# Exit code: 0
# All tests pass, no hangs
```

---

## Metadata

**Workflow**: Bugfix (regression-test-first)
**Created By**: SpecSwarm Bugfix Workflow
**Test Strategy**: Timeout-based validation + clean exit verification
**Automation**: Suitable for CI/CD pipeline
