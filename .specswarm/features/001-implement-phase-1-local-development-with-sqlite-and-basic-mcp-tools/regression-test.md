# Regression Test: Bug 001-QA - Quality Issues

**Purpose**: Prove quality issues exist, validate fixes, prevent future regressions

**Test Type**: Quality Validation Regression Test
**Created**: 2025-12-26

---

## Test Objective

Write tests/validations that:
1. ✅ **Fail before fix** (proves quality issues exist)
2. ✅ **Pass after fix** (proves issues resolved)
3. ✅ **Prevent regression** (catches if issues reintroduced)

---

## Test Specification

### Test 1: Pydantic Deprecation Detection

**Test Setup**:
- Pytest with deprecation warnings enabled
- TaskResponse schema imported and used
- Warning capture enabled

**Test Execution**:
```bash
# Run tests with deprecation warnings
pytest tests/ -W error::DeprecationWarning 2>&1 | grep -i "pydantic"
```

**Test Assertions**:
- ✅ Before fix: Deprecation warning appears for `class Config`
- ✅ After fix: No deprecation warnings
- ✅ TaskResponse schema still works correctly (ORM conversion)

**Success Criteria**:
- Before: Test fails or warning appears
- After: No warnings, test passes

---

### Test 2: Type Checking Validation

**Test Setup**:
- mypy configured with --strict mode
- All Python files in app/ directory

**Test Execution**:
```bash
# Run mypy strict type checking
mypy app/ --strict --no-error-summary 2>&1
```

**Test Assertions**:
- ✅ Before fix: Type error on auth.py:72 (Missing type parameters for dict)
- ✅ After fix: Exit code 0, no type errors
- ✅ 100% type hint coverage maintained

**Success Criteria**:
- Before: mypy exit code != 0, error count >= 1
- After: mypy exit code == 0, error count == 0

---

### Test 3: Linting Validation

**Test Setup**:
- Ruff configured per pyproject.toml
- All Python files in app/ and tests/

**Test Execution**:
```bash
# Run ruff linter
ruff check app/ tests/ 2>&1 | grep "Found.*errors"
```

**Test Assertions**:
- ✅ Before fix: 97 errors found
- ✅ After fix: < 10 errors remaining (acceptable for ship)
- ✅ All auto-fixable errors resolved

**Success Criteria**:
- Before: Error count >= 97
- After: Error count < 10

---

### Test 4: Functional Regression Test

**Test Setup**:
- Existing test suite (test_task_service.py, test_mcp_handlers.py)
- All tests should still pass after quality fixes

**Test Execution**:
```bash
# Run full test suite
pytest tests/ -v
```

**Test Assertions**:
- ✅ All existing tests pass
- ✅ No new test failures introduced
- ✅ TaskResponse schema works correctly after Pydantic config change

**Success Criteria**:
- Before and after: All tests pass
- No behavioral regressions

---

## Test Implementation

### Test File Location

**Primary Validation**: Quality gates (not unit tests)
- Validation 1: `pytest tests/ -W error::DeprecationWarning`
- Validation 2: `mypy app/ --strict`
- Validation 3: `ruff check app/ tests/`
- Validation 4: `pytest tests/`

**Optional Unit Test**: `tests/test_quality_gates.py` (for CI/CD)
```python
def test_no_pydantic_deprecation_warnings():
    """Ensure no Pydantic deprecation warnings in test suite."""
    # Run pytest with deprecation warnings as errors
    # Assert no PydanticDeprecatedSince20 warnings

def test_mypy_strict_passes():
    """Ensure mypy strict mode passes on entire codebase."""
    # Run mypy --strict on app/
    # Assert exit code 0

def test_ruff_linting_passes():
    """Ensure ruff linting has minimal errors."""
    # Run ruff check
    # Assert error count < threshold
```

### Test Validation Criteria

**Before Fix**:
- ❌ Pydantic deprecation warning appears
- ❌ mypy fails with type error
- ❌ ruff shows 97 errors

**After Fix**:
- ✅ No Pydantic warnings
- ✅ mypy passes (exit code 0)
- ✅ ruff shows < 10 errors
- ✅ All functional tests pass

---

## Edge Cases to Test

1. **Pydantic ORM Conversion**:
   - Verify TaskResponse.from_attributes still works
   - Test with actual SQLAlchemy models
   - Confirm no runtime behavior changes

2. **Type Hints in Different Contexts**:
   - Check auth.py compiles correctly
   - Verify Optional[dict[str, Any]] works in async context
   - Test that type checkers accept the fix

3. **Linting Auto-Fixes**:
   - Verify auto-fixed code still runs correctly
   - Check import sorting doesn't break functionality
   - Confirm type annotation updates are compatible

4. **Cross-File Impacts**:
   - Verify linting fixes in one file don't affect others
   - Check that import changes don't create circular dependencies
   - Test that all modules still import correctly

---

## Metadata

**Workflow**: Bugfix (quality regression test)
**Created By**: SpecSwarm Bugfix Workflow
**Test Strategy**: Quality gates + optional unit tests
**Automation**: Suitable for CI/CD pipeline
