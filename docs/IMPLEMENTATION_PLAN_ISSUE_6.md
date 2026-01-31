# Implementation Plan: Issue #6 - Universal Code Execution Provider Architecture

> **Status:** 🚧 In Progress
> **Branch:** `feat/issue-6-universal-providers`
> **Issue:** [#6](https://github.com/DonTizi/CodeGeass/issues/6)

## Summary

Implement a Universal Provider Architecture enabling CodeGeass to support multiple AI coding assistants (Claude Code, OpenAI Codex, future providers) through a standardized adapter pattern.

**Design Principles:**
- **Faible couplage** (Low coupling): Providers are independent, interchangeable
- **Forte cohésion** (High cohesion): Each module has single responsibility
- **Pattern:** Follows existing notification provider pattern (ABC, Registry, Schema)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   CodeGeass Task                         │
│         code_source: "claude" | "codex" | "..."         │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              CodeProvider (Abstract Base)                │
│  ┌────────────────────────────────────────────────────┐ │
│  │ execute(request: ExecutionRequest) → Response      │ │
│  │ get_capabilities() → ProviderCapabilities          │ │
│  │ validate_request(request) → (bool, error)          │ │
│  └────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
   ┌───────────┐   ┌───────────┐   ┌───────────┐
   │  Claude   │   │   Codex   │   │  Future   │
   │  Adapter  │   │  Adapter  │   │ Providers │
   └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
         │               │               │
         ▼               ▼               ▼
    claude -p       codex exec        ???
```

---

## Provider Capability Matrix

| Feature | Claude Code | Codex |
|---------|-------------|-------|
| Headless | ✅ `claude -p` | ✅ `codex exec` |
| Plan mode | ✅ `--permission-mode plan` | ❌ Not available |
| Resume | ✅ `--resume` | ❌ Interactive only |
| Streaming | ✅ `stream-json` | ✅ `--json` JSONL |
| Autonomous | ✅ `--dangerously-skip-permissions` | ✅ `--yolo` |

---

## Implementation Progress

### Phase 1: Provider Infrastructure Foundation

| Step | Description | Status | Commit |
|------|-------------|--------|--------|
| 1.1 | Create provider exceptions | ⏳ Pending | - |
| 1.2 | Create provider base classes | ⏳ Pending | - |
| 1.3 | Create provider registry | ⏳ Pending | - |
| 1.4 | Create package init | ⏳ Pending | - |

### Phase 2: Claude Code Adapter (Refactor Existing)

| Step | Description | Status | Commit |
|------|-------------|--------|--------|
| 2.1 | Move Claude CLI discovery | ⏳ Pending | - |
| 2.2 | Create Claude output parser | ⏳ Pending | - |
| 2.3 | Create ClaudeCodeAdapter | ⏳ Pending | - |

### Phase 3: OpenAI Codex Adapter (New)

| Step | Description | Status | Commit |
|------|-------------|--------|--------|
| 3.1 | Create Codex CLI discovery | ⏳ Pending | - |
| 3.2 | Create Codex output parser | ⏳ Pending | - |
| 3.3 | Create CodexAdapter | ⏳ Pending | - |

### Phase 4: Task Entity & Executor Integration

| Step | Description | Status | Commit |
|------|-------------|--------|--------|
| 4.1 | Add code_source to Task entity | ⏳ Pending | - |
| 4.2 | Update executor to use providers | ⏳ Pending | - |

### Phase 5: CLI Updates

| Step | Description | Status | Commit |
|------|-------------|--------|--------|
| 5.1 | Add provider CLI commands | ⏳ Pending | - |
| 5.2 | Add --code-source to task commands | ⏳ Pending | - |

### Phase 6: Dashboard Backend

| Step | Description | Status | Commit |
|------|-------------|--------|--------|
| 6.1 | Add provider API endpoints | ⏳ Pending | - |
| 6.2 | Update task API models | ⏳ Pending | - |

### Phase 7: Dashboard Frontend

| Step | Description | Status | Commit |
|------|-------------|--------|--------|
| 7.1 | Add provider selector to TaskForm | ⏳ Pending | - |

### Phase 8: Testing & Documentation

| Step | Description | Status | Commit |
|------|-------------|--------|--------|
| 8.1 | Add unit tests | ⏳ Pending | - |
| 8.2 | Integration testing | ⏳ Pending | - |

---

## Files to Create

```
src/codegeass/providers/
├── __init__.py              # Package exports
├── base.py                  # CodeProvider ABC, dataclasses
├── exceptions.py            # ProviderError hierarchy
├── registry.py              # ProviderRegistry
├── claude/
│   ├── __init__.py
│   ├── adapter.py           # ClaudeCodeAdapter
│   ├── cli.py               # get_claude_executable()
│   └── output_parser.py     # JSON stream parser
└── codex/
    ├── __init__.py
    ├── adapter.py           # CodexAdapter
    ├── cli.py               # get_codex_executable()
    └── output_parser.py     # JSONL parser
```

---

## Files to Modify

| File | Change |
|------|--------|
| `src/codegeass/core/entities.py` | Add `code_source` field to Task |
| `src/codegeass/execution/executor.py` | Use ProviderRegistry |
| `src/codegeass/execution/strategies/claude_cli.py` | Add deprecation wrapper |
| `src/codegeass/cli/commands/task.py` | Add `--code-source` flag |
| `src/codegeass/cli/main.py` | Register provider commands |
| `dashboard/backend/main.py` | Register providers router |
| `dashboard/backend/models/task.py` | Add code_source field |
| `dashboard/frontend/src/components/tasks/TaskForm.tsx` | Provider selector |

---

## Detailed Step Specifications

### Step 1.1: Create Provider Exceptions

**File:** `src/codegeass/providers/exceptions.py`

```python
"""Provider-specific exceptions."""
from codegeass.core.exceptions import CodeGeassError

class ProviderError(CodeGeassError):
    """Base exception for provider errors."""
    def __init__(self, provider: str, message: str, cause: Exception | None = None):
        super().__init__(f"[{provider}] {message}")
        self.provider = provider
        self.cause = cause

class ProviderNotFoundError(ProviderError):
    """Raised when a provider is not registered."""
    def __init__(self, provider: str):
        super().__init__(provider, f"Provider not found: {provider}")

class ProviderCapabilityError(ProviderError):
    """Raised when a request exceeds provider capabilities."""
    pass

class ProviderExecutionError(ProviderError):
    """Raised when provider execution fails."""
    pass
```

**Test:**
```bash
python -c "from codegeass.providers.exceptions import ProviderNotFoundError; print('OK')"
```

**Commit:** `feat(providers): add provider exception hierarchy`

---

### Step 1.2: Create Provider Base Classes

**File:** `src/codegeass/providers/base.py`

Key components:
- `ProviderCapabilities` dataclass
- `ExecutionRequest` dataclass
- `ExecutionResponse` dataclass
- `CodeProvider` abstract base class

**Test:**
```bash
pytest tests/providers/test_base.py -v
```

**Commit:** `feat(providers): add CodeProvider ABC and dataclasses`

---

### Step 1.3: Create Provider Registry

**File:** `src/codegeass/providers/registry.py`

Pattern from `notifications/registry.py`:
- Lazy loading with class path strings
- Global singleton `get_provider_registry()`
- Dynamic registration via `register()` classmethod

**Test:**
```bash
python -c "from codegeass.providers import get_provider_registry; print('OK')"
```

**Commit:** `feat(providers): add ProviderRegistry with lazy loading`

---

*[Additional steps follow the same pattern...]*

---

## Verification Checklist

After each step:
- [ ] Code compiles without errors
- [ ] Unit tests pass
- [ ] No regressions in existing tests
- [ ] Commit pushed to branch

After all steps:
- [ ] `codegeass provider list` shows providers
- [ ] `codegeass task create --code-source codex --plan-mode` fails with clear error
- [ ] Dashboard provider selector works
- [ ] Existing tasks (no code_source) still work with default "claude"

---

## Notes & Decisions

*This section will be updated as we implement each step.*

---

## References

- Issue: https://github.com/DonTizi/CodeGeass/issues/6
- Notification provider pattern: `src/codegeass/notifications/providers/`
- Claude Code CLI docs: https://code.claude.com/docs/en/cli-reference
- Codex CLI docs: https://developers.openai.com/codex/cli/reference/
