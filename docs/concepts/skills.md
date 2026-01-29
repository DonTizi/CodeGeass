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

Skills live in `.claude/skills/` directories:

```
.claude/
└── skills/
    ├── review/
    │   └── SKILL.md
    ├── test/
    │   └── SKILL.md
    └── deploy/
        └── SKILL.md
```

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

## Best Practices

1. **Be specific** - Clear instructions get better results
2. **Use allowed-tools** - Limit tools to what's needed
3. **Document well** - The description helps users understand the skill
4. **Test first** - Validate skills before using in scheduled tasks
5. **Version control** - Keep skills in your repo

## Related

- [Tasks](tasks.md) - Use skills in scheduled tasks
- [Execution](execution.md) - How skills are executed
- [CLI Reference](../cli/skill.md) - Skill commands
