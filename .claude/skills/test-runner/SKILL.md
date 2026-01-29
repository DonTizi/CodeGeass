---
name: test-runner
description: Run and analyze test suites. Executes tests, reports failures, and suggests fixes for broken tests. Use for automated testing in CI/CD or scheduled runs.
context: fork
agent: general-purpose
allowed-tools: Read, Grep, Glob, Bash(pytest *), Bash(npm test *), Bash(npm run test *), Bash(python -m pytest *), Bash(go test *)
disable-model-invocation: true
---

# Test Runner

Execute and analyze tests for the project at `$ARGUMENTS`.

## Supported Test Frameworks

- **Python**: pytest, unittest
- **JavaScript/TypeScript**: Jest, Mocha, Vitest
- **Go**: go test
- **Rust**: cargo test

## Dynamic Context
- Test configuration: !`find . -name "pytest.ini" -o -name "pyproject.toml" -o -name "jest.config.*" -o -name "vitest.config.*" 2>/dev/null | head -5`
- Test directories: !`find . -type d -name "test*" -o -name "__tests__" 2>/dev/null | head -5`

## Instructions

### 1. Detect Test Framework

Check for test configuration files:
- `pytest.ini`, `pyproject.toml` → pytest
- `jest.config.js`, `package.json` with jest → Jest
- `vitest.config.ts` → Vitest
- `go.mod` with `_test.go` files → go test

### 2. Run Tests

Execute the appropriate test command:

**Python (pytest)**:
```bash
python -m pytest -v --tb=short 2>&1
```

**JavaScript (npm)**:
```bash
npm test 2>&1
```

**Go**:
```bash
go test ./... -v 2>&1
```

### 3. Analyze Results

Parse test output for:
- Total tests run
- Passed/Failed/Skipped counts
- Error messages and stack traces
- Slow tests (if timing available)

### 4. For Failures

For each failing test:
1. Read the test file to understand intent
2. Check the error message
3. Suggest potential fix

## Output Format

Return a JSON test report:
```json
{
  "framework": "pytest",
  "summary": {
    "total": 50,
    "passed": 48,
    "failed": 2,
    "skipped": 0,
    "duration_seconds": 12.5
  },
  "status": "failed",
  "failures": [
    {
      "test": "test_user_login",
      "file": "tests/test_auth.py",
      "line": 42,
      "error_type": "AssertionError",
      "message": "Expected status 200, got 401",
      "suggestion": "Check if the test user credentials are valid in test fixtures"
    }
  ],
  "slow_tests": [
    {
      "test": "test_large_file_upload",
      "duration_seconds": 5.2
    }
  ],
  "coverage": {
    "percentage": 78.5,
    "missing_files": ["src/utils/cache.py"]
  }
}
```

## Interpretation

- **All Passed**: Great! Code is healthy
- **Some Failed**: Review failures, may indicate bugs or outdated tests
- **Many Failed**: Possible breaking change or environment issue
- **Slow Tests**: May need optimization or mocking

## Exit Codes

- `0`: All tests passed
- `1`: Some tests failed
- `2`: Test collection/configuration error
