# Tasks: Bug 001-QA - Critical Quality Issues

**Workflow**: Bugfix (Quality Fixes)
**Status**: Active
**Created**: 2025-12-26

---

## Execution Strategy

**Mode**: Sequential (straightforward quality fixes)
**Smart Integration**: SpecSwarm installed (tech stack validation enabled)

---

## Phase 1: Pre-Fix Validation

### T001: Verify Pydantic Deprecation Warning Exists
**Description**: Run tests and confirm Pydantic deprecation warning appears
**Command**: `pytest tests/ -W default::DeprecationWarning 2>&1 | grep -i "PydanticDeprecatedSince20"`
**Expected**: Warning appears for `class Config` deprecation
**Validation**: Warning proves issue exists
**Parallel**: No (validation baseline)

### T002: Verify Type Checking Fails
**Description**: Run mypy strict and confirm type error on auth.py:72
**Command**: `mypy app/ --strict 2>&1 | grep "auth.py:72"`
**Expected**: Type error for missing dict type parameters
**Validation**: Error proves issue exists
**Parallel**: No (validation baseline)

### T003: Verify Linting Errors Exist
**Description**: Run ruff and confirm 97 errors
**Command**: `ruff check app/ tests/ 2>&1 | grep "Found.*errors"`
**Expected**: 97 errors found
**Validation**: Error count proves issue exists
**Parallel**: No (validation baseline)

---

## Phase 2: Implement Fixes

### T004: Fix Pydantic Deprecation
**Description**: Replace `class Config` with `model_config = ConfigDict(...)`
**File**: `app/schemas/task.py`
**Changes**:
1. Add import: `from pydantic import ConfigDict`
2. Replace lines 147-150:
   ```python
   # Before:
   class Config:
       """Pydantic configuration."""
       from_attributes = True

   # After:
   model_config = ConfigDict(from_attributes=True)
   ```
**Tech Stack Validation**: Uses approved Pydantic 2.10.0+ syntax
**Parallel**: No (critical fix)

### T005: Fix Type Annotation Error
**Description**: Add type parameters to dict type hint
**File**: `app/config/auth.py`
**Changes**:
1. Add import: `from typing import Any`
2. Update line 72:
   ```python
   # Before:
   async def get_user_preferences(user_id: str) -> Optional[dict]:

   # After:
   async def get_user_preferences(user_id: str) -> Optional[dict[str, Any]]:
   ```
**Tech Stack Validation**: Uses approved Python 3.11+ type hints
**Parallel**: Yes [P] (independent from T004)

### T006: Auto-Fix Linting Errors
**Description**: Run ruff auto-fix to resolve 56 auto-fixable errors
**Command**: `ruff check --fix app/ tests/`
**Files**: All Python files in app/ and tests/
**Changes**: Auto-applied formatting, import sorting, type annotations
**Expected**: 56 errors auto-fixed, 41 remaining
**Tech Stack Validation**: Uses approved ruff linter
**Parallel**: No (must run after T004-T005 to avoid conflicts)

### T007: Review Remaining Linting Errors
**Description**: Review and manually fix remaining 41 linting errors if critical
**Command**: `ruff check app/ tests/`
**Expected**: < 10 errors remaining (acceptable threshold)
**Validation**: Code quality score improves to ≥ 80/100
**Parallel**: No (depends on T006)

---

## Phase 3: Post-Fix Validation

### T008: Verify No Pydantic Warnings
**Description**: Run tests and confirm no deprecation warnings
**Command**: `pytest tests/ -W error::DeprecationWarning 2>&1`
**Expected**: No Pydantic warnings, all tests pass
**Validation**: Proves Pydantic fix works
**Parallel**: No (validation checkpoint)

### T009: Verify Type Checking Passes
**Description**: Run mypy strict and confirm no errors
**Command**: `mypy app/ --strict`
**Expected**: Exit code 0, no type errors
**Validation**: Proves type annotation fix works
**Parallel**: Yes [P] (independent validation)

### T010: Verify Linting Improved
**Description**: Run ruff and confirm errors reduced
**Command**: `ruff check app/ tests/ 2>&1 | grep "Found.*errors"`
**Expected**: < 10 errors (down from 97)
**Validation**: Proves linting fixes worked
**Parallel**: Yes [P] (independent validation)

### T011: Run Full Test Suite
**Description**: Verify no functional regressions introduced
**Command**: `pytest tests/ -v`
**Expected**: All tests pass (no new failures)
**Validation**: Proves fixes didn't break functionality
**Parallel**: No (comprehensive validation)

### T012: Measure Quality Score
**Description**: Re-run quality analysis to confirm improvement
**Command**: Quality gates check (mypy + ruff + pytest)
**Expected**: Quality score ≥ 80/100 (up from 58/100)
**Validation**: Proves ship-blocking issues resolved
**Parallel**: No (final gate)

---

## Summary

**Total Tasks**: 12 tasks (3 pre-fix validation, 4 fixes, 5 post-fix validation)
**Estimated Time**: 30-45 minutes
**Parallel Opportunities**: T005 [P], T009-T010 [P] (limited parallelism due to dependencies)

**Success Criteria**:
- ✅ Pre-fix validation confirms all 3 issues exist
- ✅ Pydantic deprecation fixed (no warnings)
- ✅ Type annotation fixed (mypy passes)
- ✅ Linting errors reduced < 10 (from 97)
- ✅ All functional tests still pass
- ✅ Quality score ≥ 80/100
- ✅ Tech stack compliant

**Tech Stack Compliance**: All fixes use approved technologies (Pydantic 2.10.0+, Python 3.11+ type hints, Ruff linter)
