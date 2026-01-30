---
name: refactor
description: Refactor monolithic code into clean, single-responsibility modules following SOLID principles
allowed-tools: Read, Grep, Glob, Edit, Write, Bash
---

# Refactor Code to Clean Architecture

You are a Senior Software Architect. Analyze the codebase and refactor any monolithic code into clean, well-organized modules.

## Target: $ARGUMENTS

## Guiding Principles

### File Size Limits
- **Maximum 50-60 lines per file** (flexible for complex components)
- Single responsibility per file
- Strong cohesion within modules, loose coupling between them

### SOLID Principles
- **S**ingle Responsibility: Each module has ONE reason to change
- **O**pen/Closed: Open for extension, closed for modification
- **L**iskov Substitution: Subtypes must be substitutable
- **I**nterface Segregation: Many specific interfaces over one general
- **D**ependency Inversion: Depend on abstractions, not concretions

### Design Patterns (refactoring.guru)
**Creational**: Factory, Builder, Singleton
**Structural**: Facade, Adapter, Decorator, Composite
**Behavioral**: Strategy, Observer, Command, Template Method

---

## Phase 1: Discovery

### 1.1 Find Candidates
Search for files that need refactoring:

```bash
# Find large files (>100 lines)
find . -name "*.py" -type f ! -path "*/venv/*" ! -path "*/.venv/*" -exec wc -l {} \; | awk '$1 > 100 {print}' | sort -rn | head -20
```

### 1.2 Code Smells Checklist

For each large file, check for:

| Smell | Indicator | Action |
|-------|-----------|--------|
| Long Method | >20 lines of logic | Extract Function |
| Large Class | >200 lines or 3+ responsibilities | Extract Class |
| Long Parameter List | >3 parameters | Introduce Parameter Object |
| Duplicate Code | Similar blocks in multiple places | Extract to shared utility |
| Feature Envy | Method uses another class more than its own | Move Method |
| Switch Statements | Complex conditionals | Replace with Polymorphism |
| Dead Code | Unused functions/variables | Remove |
| Magic Numbers | Hardcoded values | Replace with Constants |

### 1.3 Responsibility Analysis

For each candidate file, identify:
- What are the distinct responsibilities?
- Which code blocks belong together?
- What are the dependencies?

---

## Phase 2: Planning

### 2.1 Proposed Structure

For each file to refactor, plan the new structure:

```
module/
├── __init__.py          # Public API exports
├── models.py            # Data structures (or models/ directory)
├── services.py          # Business logic (or services/ directory)
├── utils.py             # Shared utilities
├── interfaces.py        # Abstract base classes/protocols
└── exceptions.py        # Custom exceptions
```

### 2.2 Refactoring Techniques (refactoring.com/catalog)

| Technique | When to Use |
|-----------|-------------|
| Extract Function | Long methods with distinct logic blocks |
| Extract Class | Class with multiple responsibilities |
| Move Function | Function belongs in another module |
| Inline Variable | Variable used once, adds no clarity |
| Replace Temp with Query | Temporary variable can be a method |
| Introduce Parameter Object | Multiple related parameters |
| Replace Conditional with Polymorphism | Complex switch/if chains |
| Remove Dead Code | Unused code |

---

## Phase 3: Execution

### 3.1 Pre-Refactoring

```bash
# Create feature branch
git checkout -b refactor/cleanup-$(date +%Y-%m-%d)

# Record baseline metrics
echo "=== BEFORE REFACTORING ===" > /tmp/refactor-metrics.txt
find . -name "*.py" -type f ! -path "*/venv/*" -exec wc -l {} \; | sort -rn | head -10 >> /tmp/refactor-metrics.txt
```

### 3.2 Refactoring Order

Execute in this order to minimize breakage:
1. **Extract utilities first** - shared helper functions
2. **Extract models** - data structures
3. **Extract interfaces** - abstract base classes
4. **Extract services** - business logic
5. **Update imports** - fix all references
6. **Remove dead code** - clean up original

### 3.3 Code Standards

For each new file:
```python
"""
Brief module description.
"""
from __future__ import annotations

# Standard library
# Third-party
# Local imports

# Type hints on all public functions
# Docstrings on all public functions/classes
# No commented-out code
# Constants in UPPER_CASE
```

---

## Phase 4: Validation

### 4.1 Quality Checks

```bash
# Verify all files under 60 lines (warn if over)
find . -name "*.py" -type f ! -path "*/venv/*" -exec wc -l {} \; | awk '$1 > 60 {print "WARNING: " $0}'

# Check for circular imports
python -c "import sys; sys.path.insert(0, '.'); import <module>" 2>&1

# Run tests if they exist
pytest -x --tb=short 2>/dev/null || echo "No tests found"

# Lint check
ruff check . 2>/dev/null || flake8 . 2>/dev/null || echo "No linter"
```

### 4.2 Metrics Comparison

Create a before/after comparison:

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Largest file (lines) | ? | <60 | ? |
| Files over 100 lines | ? | 0 | ? |
| Total files | ? | ? | ? |

---

## Phase 5: Functional Testing

**CRITICAL**: Before creating a PR, you MUST verify the application still works.

### 5.1 Test Core CLI Commands

Run actual commands to verify nothing is broken:

```bash
# Test CLI is accessible
codegeass --version

# Test core commands work
codegeass task list
codegeass skill list
codegeass project list
codegeass scheduler status

# Test a specific task show (pick any existing task)
codegeass task show "$(codegeass task list --format json 2>/dev/null | python3 -c "import sys,json; tasks=json.load(sys.stdin); print(tasks[0]['name'] if tasks else '')" 2>/dev/null || echo "")"

# Test help commands
codegeass --help
codegeass task --help
```

### 5.2 Verify No Import Errors

```bash
# Test all modules can be imported
python3 -c "from codegeass.cli import cli; print('CLI imports OK')"
python3 -c "from codegeass.core import entities; print('Core imports OK')"
python3 -c "from codegeass.storage import task_repository; print('Storage imports OK')"
python3 -c "from codegeass.factory import registry; print('Factory imports OK')"
python3 -c "from codegeass.execution import session; print('Execution imports OK')"
python3 -c "from codegeass.scheduling import scheduler; print('Scheduling imports OK')"
```

### 5.3 Decision Point

**If ANY test fails:**
1. STOP - Do not create PR
2. Identify the breaking change
3. Fix the issue
4. Re-run all tests
5. Only proceed when ALL tests pass

**If ALL tests pass:**
- Proceed to Phase 6 (Pull Request)

---

## Phase 6: Pull Request

### 6.1 Commit and Push

```bash
git add -A
git commit -m "refactor: split monolithic code into single-responsibility modules

Changes:
- Extract X from Y for Z responsibility
- Apply Factory pattern for object creation
- Apply Strategy pattern for interchangeable algorithms
- Reduce max file size from X to Y lines

Techniques used:
- Extract Class
- Extract Function
- Move Function
- Remove Dead Code

Refs: SOLID principles, refactoring.guru patterns"

git push -u origin refactor/cleanup-$(date +%Y-%m-%d)
```

### 6.2 Create PR

```bash
gh pr create --title "refactor: modularize codebase $(date +%Y-%m-%d)" --label "refactoring,automated" --body "$(cat <<'EOF'
## Summary

Automated refactoring to improve code organization and maintainability.

## Why These Changes?

### Problems Found
- [List specific code smells detected]
- [List files that were too large]
- [List responsibilities that were mixed]

### Solutions Applied
- [Explain each extraction and why]
- [Explain design patterns used and why]
- [Explain how SOLID principles are now respected]

## Changes Made

### Files Created
| New File | Responsibility | Lines | Extracted From |
|----------|---------------|-------|----------------|
| path/to/new.py | Description | XX | original.py |

### Files Modified
| File | Change |
|------|--------|
| path/to/file.py | Removed extracted code, updated imports |

## Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Largest file | X lines | Y lines | -Z% |
| Files > 100 lines | X | 0 | -100% |
| Avg file size | X | Y | -Z% |

## Design Patterns Applied

- **Pattern Name**: Why it was applied and benefit

## Refactoring Techniques Used

From [refactoring.com/catalog](https://refactoring.com/catalog/):
- Extract Class: [where and why]
- Extract Function: [where and why]
- Move Function: [where and why]

## SOLID Compliance

- [x] Single Responsibility: Each file has one reason to change
- [x] Open/Closed: New behavior via extension, not modification
- [x] Dependency Inversion: Depend on abstractions

## Testing

- [ ] All imports verified working
- [ ] Existing tests pass (if any)
- [ ] No circular dependencies
- [ ] Linter passes

## How to Review

1. Check each new file has a single, clear responsibility
2. Verify file sizes are reasonable (<60 lines ideally)
3. Confirm imports are clean and no circular dependencies
4. Run tests if available

## Rollback

If issues arise:
```bash
git revert <this-merge-commit>
```
EOF
)"
```

---

## If No Refactoring Needed

If all files are already well-organized (under 60 lines, single responsibility):

```bash
gh issue create --title "✅ Code Quality Check - All Clean $(date +%Y-%m-%d)" --label "automated,quality" --body "$(cat <<'EOF'
## Daily Code Quality Check

**Status**: All code meets quality standards

### Metrics
- Largest file: X lines (under 60 limit)
- Files checked: Y
- Code smells found: 0

No refactoring needed today.
EOF
)"
```
