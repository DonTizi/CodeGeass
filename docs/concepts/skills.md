# Skills

Skills are reusable, parameterized prompts that follow the [Agent Skills](https://agentskills.io) open standard.

## What is a Skill?

A skill is a markdown file with YAML frontmatter that defines:

- Metadata (name, description)
- Execution context
- Tool permissions
- The prompt template

```markdown
---
name: code-review
description: Review code changes and provide feedback
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob
---

# Review the following code

$ARGUMENTS

Focus on:
- Code quality
- Potential bugs
- Performance issues
```

## Skill Location

Skills can be stored in two locations:

### Project Skills

Project-specific skills live in `.claude/skills/`:

```
project/
└── .claude/
    └── skills/
        ├── review/
        │   └── SKILL.md
        ├── test/
        │   └── SKILL.md
        └── deploy/
            └── SKILL.md
```

### Shared Skills

Global skills available to all projects live in `~/.codegeass/skills/`:

```
~/.codegeass/
└── skills/
    ├── review/
    │   └── SKILL.md
    ├── security-scan/
    │   └── SKILL.md
    └── dependency-check/
        └── SKILL.md
```

!!! tip "Skill Priority"
    Project skills take priority over shared skills with the same name. This allows you to override shared skills with project-specific versions.

## SKILL.md Format

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Skill identifier |
| `description` | Yes | What the skill does |
| `context` | No | Execution context (`fork`, `current`) |
| `agent` | No | Agent type (`Explore`, `general`) |
| `allowed-tools` | No | Comma-separated list of allowed tools |

### Template Variables

- `$ARGUMENTS` - Replaced with user-provided arguments
- Jinja2 templates supported for complex logic

## Creating Skills

### Basic Skill

```bash
# Create skill directory
mkdir -p .claude/skills/my-skill

# Create SKILL.md
cat > .claude/skills/my-skill/SKILL.md << 'EOF'
---
name: my-skill
description: Does something useful
---

# Instructions

$ARGUMENTS

Do the thing.
EOF
```

### Validate Skill

```bash
codegeass skill validate .claude/skills/my-skill/SKILL.md
```

### List Available Skills

```bash
codegeass skill list
```

## Using Skills

### With Tasks

```bash
codegeass task create \
  --name skill-task \
  --schedule "0 9 * * *" \
  --mode skill \
  --skill review \
  --skill-args "Review the authentication module"
```

### Manual Invocation

```bash
codegeass skill run review "Check the API endpoints"
```

## Example Skills

### Code Review Skill

```markdown
---
name: review
description: Review code changes for quality and issues
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob, Bash
---

# Code Review

Review the following:

$ARGUMENTS

## Review Checklist

- [ ] Code follows project conventions
- [ ] No obvious bugs or logic errors
- [ ] Error handling is appropriate
- [ ] Performance is acceptable
- [ ] Security considerations addressed

Provide specific, actionable feedback.
```

### Test Runner Skill

```markdown
---
name: test
description: Run tests and report results
context: current
allowed-tools: Bash, Read
---

# Run Tests

$ARGUMENTS

Execute the test suite and:
1. Report any failures with context
2. Suggest fixes for failing tests
3. Note any skipped or slow tests
```

### Documentation Skill

```markdown
---
name: document
description: Generate or update documentation
context: fork
allowed-tools: Read, Grep, Write
---

# Documentation Task

$ARGUMENTS

Update documentation to:
- Reflect current code behavior
- Include examples
- Follow project documentation style
```

## Skill Context

### `fork` Context

- Creates an isolated environment
- Changes don't affect the main project
- Best for exploratory or risky operations

### `current` Context

- Runs in the current working directory
- Changes are applied directly
- Use when you want immediate results

## Included Skills

CodeGeass ships with several powerful skills that you can use immediately.

### review

Comprehensive code review for PRs or recent changes.

**What it checks:**

- **Correctness**: Logic errors, edge cases, null handling
- **Security**: Injection vulnerabilities, secrets exposure, auth issues
- **Performance**: N+1 queries, unnecessary loops, memory leaks
- **Maintainability**: Complexity, naming, documentation
- **Tests**: Coverage, edge cases, meaningful assertions

**Usage:**

```bash
codegeass task create \
  --name daily-review \
  --skill review \
  --schedule "0 9 * * 1-5"
```

**Output format:** Returns a structured JSON report with issues categorized by severity (critical, important, suggestion) and type.

### security-scan

Deep security analysis of your codebase.

**What it detects:**

- **Secrets**: API keys, tokens, passwords, private keys in code
- **Dependency vulnerabilities**: CVEs in packages (pip-audit, npm audit)
- **Code vulnerabilities**: SQL injection, XSS, command injection, path traversal
- **Configuration issues**: Debug mode, permissive CORS, missing security headers

**Usage:**

```bash
codegeass task create \
  --name weekly-security \
  --skill security-scan \
  --schedule "0 2 * * 0"
```

**Output format:** Returns a JSON security report with findings, severity levels, CWE references, and remediation suggestions.

### refactor

Automated refactoring of monolithic code into clean, single-responsibility modules.

**What it does:**

- **Identifies** files exceeding size/complexity thresholds
- **Analyzes** responsibilities and suggests splits
- **Extracts** modules following SOLID principles
- **Preserves** backward compatibility via re-exports
- **Tests** changes with linting and existing tests

**Usage:**

```bash
codegeass task create \
  --name weekly-refactor \
  --skill refactor \
  --skill-args "src/codegeass/cli/" \
  --schedule "0 3 * * 0"
```

**Output:** Creates a PR with modular code structure and detailed explanation of changes.

### Other Skills

| Skill | Description |
|-------|-------------|
| `code-review` | Automated code review with security and performance focus |
| `security-audit` | OWASP vulnerability analysis |
| `test-runner` | Execute and analyze test suites |
| `dependency-check` | Check dependencies for updates and vulnerabilities |
| `refactor` | Split monolithic code into clean modules following SOLID principles |

## Best Practices

1. **Be specific** - Clear instructions get better results
2. **Use allowed-tools** - Limit tools to what's needed
3. **Document well** - The description helps users understand the skill
4. **Test first** - Validate skills before using in scheduled tasks
5. **Version control** - Keep skills in your repo
6. **Use shared skills** - Put commonly-used skills in `~/.codegeass/skills/`
7. **Override when needed** - Project skills take priority over shared ones

## Related

- [Tasks](tasks.md) - Use skills in scheduled tasks
- [Projects](projects.md) - Multi-project support and shared skills
- [Execution](execution.md) - How skills are executed
- [CLI Reference](../cli/skill.md) - Skill commands
