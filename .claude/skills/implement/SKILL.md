---
name: implement
description: Implement code from a GitHub issue specification. Explores codebase, researches docs, creates temporary implementation plan, then implements incrementally (small piece → test → commit → next). Cleans up plan file before PR.
allowed-tools: Read, Grep, Glob, Edit, Write, Bash, WebSearch, WebFetch
disable-model-invocation: true
---

# Implement GitHub Issue: $ARGUMENTS

You are a Senior Software Engineer implementing a feature from a GitHub issue specification.

**Input**: Issue number (e.g., `#4` or `4`)

**Core Principle**: Research first, plan everything, then implement piece by piece. Each working piece gets committed immediately.

---

## Phase 1: Parse Issue & Comments

### 1.1 Fetch Issue Details

```bash
# Extract issue number (handle #4 or 4 format)
ISSUE_NUM=$(echo "$ARGUMENTS" | sed 's/#//')

# Fetch complete issue data
gh issue view $ISSUE_NUM --json title,body,labels,assignees,comments
```

### 1.2 Fetch Issue Comments

**CRITICAL**: Comments contain important context, clarifications, and decisions.

```bash
gh issue view $ISSUE_NUM --comments
```

Parse comments for:
- **Clarifications**: Updated requirements or scope changes
- **Technical decisions**: Architecture choices made in discussion
- **Additional context**: Links, examples, edge cases

### 1.3 Extract From Issue

From the issue body AND comments, extract:
- **Summary**: What needs to be built
- **Technical Approach**: Architecture decisions from the issue
- **Implementation Checklist**: All `- [ ]` items
- **Files to Create/Modify**: Expected changes
- **External APIs/Libraries**: Third-party integrations mentioned

### 1.4 Validate Issue Structure

The issue MUST contain:
- [ ] Clear description of the feature
- [ ] Implementation checklist with checkboxes
- [ ] At least one file to create or modify

If missing, STOP and ask user to update the issue.

---

## Phase 2: Deep Codebase Exploration

**CRITICAL**: Understand the codebase BEFORE writing any code.

### 2.1 Understand Project Structure

```bash
ls -la src/codegeass/
cat CLAUDE.md
```

### 2.2 Find Related Subsystems

| Feature Type | Location |
|--------------|----------|
| Notification provider | `src/codegeass/notifications/` |
| Storage backend | `src/codegeass/storage/` |
| Execution strategy | `src/codegeass/execution/` |
| CLI command | `src/codegeass/cli/` |
| Core entities | `src/codegeass/core/` |

### 2.3 Study Reference Implementations

Find and READ similar implementations - these are your templates.

### 2.4 Check Existing Tests

```bash
ls tests/
```

---

## Phase 3: Research External Documentation

**If the issue mentions external APIs, libraries, or services:**

```
WebSearch: "<service> API documentation 2026"
WebSearch: "<service> Python SDK official"
WebFetch: <official-docs-url>
```

Extract: Authentication, endpoints, rate limits, error handling.

---

## Phase 4: Create Implementation Plan File

**CRITICAL**: Create `IMPLEMENTATION_PLAN.md` as your working document.

> ⚠️ **This file is TEMPORARY** - it will be deleted before the PR is created.
> It exists only to guide your implementation and track progress.

### 4.1 Create the Plan File

Create `IMPLEMENTATION_PLAN.md` with this structure:

```markdown
# Implementation Plan: Issue #N - <title>

> **Working Document** - Delete before PR.

## Issue Summary

**Goal**: <1-2 sentence summary>

## Research Findings

### Codebase Patterns
| Pattern | File | How We'll Use It |
|---------|------|------------------|

### Reference Implementation
Using `<file>` as template.

### External Docs
| Topic | Source | Key Findings |
|-------|--------|--------------|

## Architecture Decisions
1. <Decision>: <rationale>

## Files to Change

### Create
| File | Purpose |
|------|---------|

### Modify
| File | Change |
|------|--------|

## Implementation Steps

### Step 1: <description>
- [ ] What: <task>
- [ ] Files: `<files>`
- [ ] Test: `<command>`
- [ ] Commit: `<type>(<scope>): <msg>`

### Step 2: <description>
...

## Progress Log
| Step | Status | Commit |
|------|--------|--------|
| 1 | ⏳ | - |
```

---

## Phase 5: Setup Git

### 5.1 Verify Clean State

```bash
git status --porcelain
```

If dirty, STOP.

### 5.2 Create Feature Branch

```bash
git fetch origin main
git checkout -b feat/issue-$ISSUE_NUM origin/main
```

**Note**: Do NOT commit `IMPLEMENTATION_PLAN.md` to git. Keep it as untracked working file.

---

## Phase 6: Incremental Implementation

**CRITICAL**: Follow the plan step by step. Small piece → test → commit → next.

### 6.1 The Implementation Loop

```
┌─────────────────────────────────────────────────────────┐
│  FOR EACH STEP in IMPLEMENTATION_PLAN.md:              │
│                                                         │
│    1. Read the step from the plan                       │
│    2. Implement ONLY that step                          │
│    3. Test immediately                                  │
│    4. If works → commit code + update plan locally      │
│    5. If fails → fix, re-test, then commit              │
│    6. Move to next step                                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 6.2 For Each Step

#### A. Read the Step from Plan

Check `IMPLEMENTATION_PLAN.md`:
- What exactly needs to be done?
- Which files to touch?
- How to test?
- What commit message?

#### B. Implement Only This Step

- Write the minimal code for THIS step only
- Follow patterns from the plan's "Reference Implementation"
- Apply research findings from the plan

#### C. Test Immediately

```bash
# Syntax check
python -m py_compile <file>.py

# Quick import test
python -c "from codegeass.<module> import <thing>; print('OK')"

# Run relevant tests
pytest tests/test_<feature>.py -v --tb=short -x

# Verify nothing broke
pytest tests/ -v --tb=short -x
```

#### D. If Tests Pass → Commit + Update Plan

```bash
# Commit the code (NOT the plan file)
git add <code_files_only>
git commit -m "<type>(<scope>): <message from plan>

Part of #$ISSUE_NUM"
```

Then update `IMPLEMENTATION_PLAN.md` locally:
- Check off completed items: `[x]`
- Update Progress Log with commit hash

#### E. If Tests Fail → Fix First

- Debug and fix
- Re-run tests
- Only commit when working
- **NEVER proceed with broken tests**

#### F. Move to Next Step

### 6.3 Commit Types

- `feat`: New functionality
- `fix`: Bug fix
- `refactor`: Code restructure
- `test`: Adding tests

### 6.4 Example Progress

After completing Step 1, your `IMPLEMENTATION_PLAN.md` shows:

```markdown
### Step 1: Create provider skeleton
- [x] What: Create WhatsAppProvider class
- [x] Files: `src/.../whatsapp.py`
- [x] Test: import works
- [x] Commit: `feat(notifications): add WhatsAppProvider skeleton`

## Progress Log
| Step | Status | Commit |
|------|--------|--------|
| 1 | ✅ | a1b2c3d |
| 2 | ⏳ | - |
```

---

## Phase 7: Final Validation

After all steps complete:

### 7.1 Run Full Test Suite

```bash
pytest tests/ -v --tb=short
```

### 7.2 Quality Checks

```bash
mypy src/codegeass/ --ignore-missing-imports
ruff check src/codegeass/
ruff check src/codegeass/ --fix
```

### 7.3 Manual Verification

Test the feature as described in the issue.

---

## Phase 8: Cleanup & Create PR

### 8.1 Delete the Plan File

**IMPORTANT**: Remove the temporary working document before creating PR.

```bash
rm IMPLEMENTATION_PLAN.md
```

### 8.2 Verify Clean State

```bash
git status
# Should show nothing about IMPLEMENTATION_PLAN.md
```

### 8.3 Push Branch

```bash
git push -u origin feat/issue-$ISSUE_NUM
```

### 8.4 Create PR

```bash
gh pr create --title "feat: <summary>" --body "$(cat <<'EOF'
## Summary

<1-2 sentence summary>

Closes #$ISSUE_NUM

## Changes

### Files Created
| File | Purpose |
|------|---------|
| `path/file.py` | Description |

### Files Modified
| File | Change |
|------|--------|
| `path/file.py` | What changed |

## Testing

- [x] All tests pass
- [x] Type check passes
- [x] Lint passes
- [x] Manual verification done

## Checklist from Issue

- [x] Item 1
- [x] Item 2
EOF
)"
```

---

## Using the Plan During Implementation

**At any point**, if unsure:

1. **Read `IMPLEMENTATION_PLAN.md`** to:
   - Check what step you're on
   - Review architecture decisions
   - See reference implementations
   - Verify you're following the patterns

2. **Validate your work** against:
   - The step's test criteria
   - The architecture decisions
   - The patterns from references

---

## Error Handling

- **Issue Not Found**: Report and stop
- **No Checklist**: Ask user to update issue
- **Tests Fail**: Fix before proceeding
- **Plan Unclear**: Re-read issue, update plan

---

## Output Summary

```
## Implementation Complete

**Issue**: #N - <title>
**Branch**: feat/issue-N
**PR**: <URL>

### Steps Completed
1. ✅ <step 1> (commit: abc123)
2. ✅ <step 2> (commit: def456)
...

### Files Changed
- Created: list
- Modified: list

### Cleanup
- ✅ IMPLEMENTATION_PLAN.md deleted

### Next Steps
1. Review PR
2. Address feedback
3. Merge when approved
```
