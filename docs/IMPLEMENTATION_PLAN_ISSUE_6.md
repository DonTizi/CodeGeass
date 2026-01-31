# Implementation Plan: Issue #6 - Universal Code Execution Provider Architecture

> **Status:** 🟢 COMPLETE
> **Branch:** `feat/issue-6-universal-providers`
> **Issue:** [#6](https://github.com/DonTizi/CodeGeass/issues/6)
> **Last Updated:** 2026-01-30

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
│  │ build_command(request) → list[str]                 │ │
│  │ get_capabilities() → ProviderCapabilities          │ │
│  │ validate_request(request) → (bool, error)          │ │
│  │ parse_output(raw) → (text, session_id)             │ │
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

### Phase 1: Provider Infrastructure Foundation ✅ COMPLETE

| Step | Description | Status | Files |
|------|-------------|--------|-------|
| 1.1 | Create provider exceptions | ✅ Done | `src/codegeass/providers/exceptions.py` |
| 1.2 | Create provider base classes | ✅ Done | `src/codegeass/providers/base.py` |
| 1.3 | Create provider registry | ✅ Done | `src/codegeass/providers/registry.py` |
| 1.4 | Create package init | ✅ Done | `src/codegeass/providers/__init__.py` |

### Phase 2: Claude Code Adapter ✅ COMPLETE

| Step | Description | Status | Files |
|------|-------------|--------|-------|
| 2.1 | Move Claude CLI discovery | ✅ Done | `src/codegeass/providers/claude/cli.py` |
| 2.2 | Create Claude output parser | ✅ Done | `src/codegeass/providers/claude/output_parser.py` |
| 2.3 | Create ClaudeCodeAdapter | ✅ Done | `src/codegeass/providers/claude/adapter.py` |
| 2.4 | Add deprecation wrapper | ✅ Done | `src/codegeass/execution/strategies/claude_cli.py` |

### Phase 3: OpenAI Codex Adapter ✅ COMPLETE

| Step | Description | Status | Files |
|------|-------------|--------|-------|
| 3.1 | Create Codex CLI discovery | ✅ Done | `src/codegeass/providers/codex/cli.py` |
| 3.2 | Create Codex output parser | ✅ Done | `src/codegeass/providers/codex/output_parser.py` |
| 3.3 | Create CodexAdapter | ✅ Done | `src/codegeass/providers/codex/adapter.py` |

### Phase 4: Task Entity & Executor Integration ✅ COMPLETE

| Step | Description | Status | Files |
|------|-------------|--------|-------|
| 4.1 | Add code_source to Task entity | ✅ Done | `src/codegeass/core/entities.py` |
| 4.2 | Create ProviderStrategy | ✅ Done | `src/codegeass/execution/strategies/provider.py` |
| 4.3 | Update executor to use providers | ✅ Done | `src/codegeass/execution/executor.py` |

### Phase 5: CLI Updates ✅ COMPLETE

| Step | Description | Status | Files |
|------|-------------|--------|-------|
| 5.1 | Add provider CLI commands | ✅ Done | `src/codegeass/cli/commands/provider.py` |
| 5.2 | Add --code-source to task commands | ✅ Done | `src/codegeass/cli/commands/task.py` |
| 5.3 | Register provider commands | ✅ Done | `src/codegeass/cli/main.py` |

**CLI Commands Available:**
- `codegeass provider list` - List all providers with capabilities
- `codegeass provider info <name>` - Show provider details
- `codegeass provider check` - Check availability of all providers
- `codegeass task create --code-source <provider>` - Create task with specific provider
- `codegeass task update --code-source <provider>` - Update task provider

### Phase 6: Dashboard Backend ✅ COMPLETE

| Step | Description | Status | Files |
|------|-------------|--------|-------|
| 6.1 | Add provider API endpoints | ✅ Done | `dashboard/backend/routers/providers.py` |
| 6.2 | Add provider models | ✅ Done | `dashboard/backend/models/provider.py` |
| 6.3 | Update task API models | ✅ Done | `dashboard/backend/models/task.py` |
| 6.4 | Update task service | ✅ Done | `dashboard/backend/services/task_service.py` |
| 6.5 | Register providers router | ✅ Done | `dashboard/backend/main.py` |

**API Endpoints Available:**
- `GET /api/providers` - List all providers
- `GET /api/providers/available` - List available providers only
- `GET /api/providers/{name}` - Get provider details

### Phase 7: Dashboard Frontend ✅ COMPLETE

| Step | Description | Status | Files |
|------|-------------|--------|-------|
| 7.1 | Add provider types | ✅ Done | `dashboard/frontend/src/types/provider.ts` |
| 7.2 | Add providers API client | ✅ Done | `dashboard/frontend/src/lib/api.ts` |
| 7.3 | Add provider selector to TaskForm | ✅ Done | `dashboard/frontend/src/components/tasks/TaskForm.tsx` |

**Frontend Features:**
- Provider dropdown in TaskForm
- Plan Mode automatically disabled when provider doesn't support it
- Warning message when non-Claude provider selected

### Phase 8: Testing & Documentation ✅ COMPLETE

| Step | Description | Status | Files |
|------|-------------|--------|-------|
| 8.1 | Add unit tests for providers | ✅ Done | `tests/providers/` (72 tests) |
| 8.2 | Integration testing | ✅ Done | Manual verification complete |
| 8.3 | Update documentation | ✅ Done | This file |

---

## Files Created

```
src/codegeass/providers/
├── __init__.py              ✅ Package exports
├── base.py                  ✅ CodeProvider ABC, dataclasses
├── exceptions.py            ✅ ProviderError hierarchy
├── registry.py              ✅ ProviderRegistry with lazy loading
├── claude/
│   ├── __init__.py          ✅
│   ├── adapter.py           ✅ ClaudeCodeAdapter
│   ├── cli.py               ✅ get_claude_executable()
│   └── output_parser.py     ✅ JSON stream parser
└── codex/
    ├── __init__.py          ✅
    ├── adapter.py           ✅ CodexAdapter
    ├── cli.py               ✅ get_codex_executable()
    └── output_parser.py     ✅ JSONL parser

src/codegeass/execution/strategies/provider.py  ✅ ProviderStrategy wrapper
src/codegeass/cli/commands/provider.py          ✅ CLI commands
dashboard/backend/models/provider.py            ✅ Pydantic models
dashboard/backend/routers/providers.py          ✅ API endpoints
dashboard/frontend/src/types/provider.ts        ✅ TypeScript types

tests/providers/
├── __init__.py              ✅
├── test_base.py             ✅ Dataclasses, capability validation
├── test_registry.py         ✅ Lazy loading, registration
├── test_claude_adapter.py   ✅ Command building, output parsing
└── test_codex_adapter.py    ✅ Command building, capability rejection
```

---

## Files Modified

| File | Change | Status |
|------|--------|--------|
| `src/codegeass/core/entities.py` | Add `code_source` field to Task | ✅ Done |
| `src/codegeass/execution/executor.py` | Add provider validation & ProviderStrategy support | ✅ Done |
| `src/codegeass/execution/strategies/__init__.py` | Export ProviderStrategy | ✅ Done |
| `src/codegeass/execution/strategies/claude_cli.py` | Add deprecation wrapper | ✅ Done |
| `src/codegeass/execution/output_parser.py` | Add deprecation wrapper | ✅ Done |
| `src/codegeass/cli/commands/task.py` | Add `--code-source` flag | ✅ Done |
| `src/codegeass/cli/main.py` | Register provider commands | ✅ Done |
| `dashboard/backend/main.py` | Register providers router | ✅ Done |
| `dashboard/backend/models/task.py` | Add code_source field | ✅ Done |
| `dashboard/backend/services/task_service.py` | Handle code_source | ✅ Done |
| `dashboard/backend/routers/__init__.py` | Export providers_router | ✅ Done |
| `dashboard/frontend/src/types/task.ts` | Add code_source field | ✅ Done |
| `dashboard/frontend/src/types/index.ts` | Export provider types | ✅ Done |
| `dashboard/frontend/src/lib/api.ts` | Add providers API | ✅ Done |
| `dashboard/frontend/src/components/tasks/TaskForm.tsx` | Provider selector | ✅ Done |

---

## Verification Checklist ✅ ALL COMPLETE

- [x] Code compiles without errors
- [x] All 165 tests pass (93 original + 72 provider tests)
- [x] Linting passes (`ruff check`)
- [x] `codegeass provider list` shows providers
- [x] `codegeass provider info claude` shows details
- [x] `codegeass task create --code-source codex --plan-mode` fails with clear error
- [x] `codegeass task show` displays code_source field
- [x] API endpoint `GET /api/providers` returns provider list
- [x] Dashboard TaskForm shows provider selector
- [x] Plan Mode disabled when non-Claude provider selected
- [x] Existing tasks (no code_source in YAML) load with default "claude"
- [x] Executor validates provider capabilities before execution
- [x] Non-Claude providers use ProviderStrategy for execution

---

## Usage Examples

### CLI

```bash
# List all providers
codegeass provider list

# Show provider details
codegeass provider info claude
codegeass provider info codex

# Check provider availability
codegeass provider check

# Create task with specific provider
codegeass task create --name my-task --schedule "0 9 * * *" \
    --prompt "Review code" --working-dir /project \
    --code-source claude

# This fails (codex doesn't support plan mode)
codegeass task create --name test --schedule "0 0 * * *" \
    --prompt "test" --working-dir /project \
    --code-source codex --plan-mode
# Error: Provider 'codex' does not support plan mode
```

### Python

```python
from codegeass.providers import get_provider_registry

registry = get_provider_registry()

# List providers
print(registry.list_providers())  # ['claude', 'codex']

# Get provider info
info = registry.get_provider_info('claude')
print(info.capabilities.plan_mode)  # True

# Validate request
provider = registry.get('codex')
valid, error = provider.validate_request(ExecutionRequest(
    prompt="test",
    working_dir=Path.cwd(),
    plan_mode=True  # Codex doesn't support this
))
print(valid, error)  # False, "Codex does not support plan mode..."
```

---

## Notes & Decisions

1. **Backward Compatibility**: All existing tasks work unchanged. `code_source` defaults to "claude".

2. **Deprecation Path**: Old `get_claude_executable()` and `parse_stream_json()` in execution module now import from providers with deprecation warnings.

3. **Capability Validation**: Validation happens at two levels:
   - Task creation/update time in CLI (prevents invalid configurations)
   - Executor execute() time (fail-fast before subprocess spawn)

4. **Frontend UX**: Plan Mode switch is disabled (not hidden) when provider doesn't support it, with explanatory warning.

5. **Model Mapping**: Codex adapter maps Claude model names to OpenAI equivalents (sonnet→gpt-4o, haiku→gpt-4o-mini, opus→o1).

6. **Strategy Pattern Preserved**: For Claude provider, the existing battle-tested strategy pattern is used. For non-Claude providers, the new ProviderStrategy wrapper is used.

7. **Pre-existing Frontend Issues**: TypeScript build errors (`import.meta.env`, nullable strings) existed before this PR and are not addressed here.

---

## References

- Issue: https://github.com/DonTizi/CodeGeass/issues/6
- Notification provider pattern: `src/codegeass/notifications/providers/`
- Claude Code CLI docs: https://docs.anthropic.com/en/docs/claude-code
- Codex CLI docs: https://github.com/openai/codex
