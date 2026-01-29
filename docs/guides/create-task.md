# Creating Tasks

This guide walks through creating effective scheduled tasks in CodeGeass.

## Basic Task Creation

The simplest task requires a name, schedule, and prompt:

```bash
codegeass task create \
  --name my-task \
  --schedule "0 9 * * *" \
  --prompt "Your instructions here"
```

## Step-by-Step Guide

### 1. Choose a Meaningful Name

Task names should be:
- Descriptive and lowercase
- Use hyphens for spaces
- Unique within your project

```bash
# Good names
daily-code-review
weekly-report
dependency-check

# Avoid
task1
my-task
thing
```

### 2. Define the Schedule

Use CRON expressions to specify when tasks run:

```bash
# Every day at 9 AM
--schedule "0 9 * * *"

# Weekdays at 9 AM
--schedule "0 9 * * 1-5"

# Every 6 hours
--schedule "0 */6 * * *"

# Monday at 10 AM
--schedule "0 10 * * 1"
```

!!! tip "Test Your Schedule"
    Use [crontab.guru](https://crontab.guru) to verify CRON expressions.

### 3. Write Clear Prompts

Good prompts are:
- **Specific** - Say exactly what you want
- **Scoped** - Focus on one thing
- **Actionable** - Request concrete outputs

```bash
# Good prompt
--prompt "Review commits from the last 24 hours. List any potential bugs, security issues, or code style violations. Summarize findings in a bullet list."

# Too vague
--prompt "Look at the code"
```

### 4. Choose Execution Mode

| Mode | Use When |
|------|----------|
| `headless` | Reading, analyzing, reporting (default) |
| `autonomous` | Making file changes |
| `skill` | Using a predefined skill |

```bash
# Read-only analysis
--mode headless

# Allowing file changes
--mode autonomous

# Using a skill
--mode skill --skill review
```

### 5. Set Working Directory

Specify where the task should run:

```bash
--working-dir /path/to/your/project
```

If not specified, uses the current directory.

## Complete Examples

### Daily Code Review

```bash
codegeass task create \
  --name daily-review \
  --schedule "0 9 * * 1-5" \
  --prompt "Review commits from the last 24 hours. Check for:
- Potential bugs
- Security issues
- Code style violations
- Missing tests
Provide a summary with specific file references." \
  --working-dir /home/user/myproject \
  --mode headless
```

### Weekly Dependency Check

```bash
codegeass task create \
  --name weekly-deps \
  --schedule "0 10 * * 1" \
  --prompt "Check for outdated dependencies. List:
- Outdated packages with current and latest versions
- Security vulnerabilities
- Recommended updates
Do not make changes, just report findings." \
  --working-dir /home/user/myproject \
  --mode headless
```

### Automated Test Runner

```bash
codegeass task create \
  --name test-runner \
  --schedule "0 */4 * * *" \
  --prompt "Run the test suite. If any tests fail:
1. Identify the failing tests
2. Analyze the error messages
3. Suggest potential fixes
Report results concisely." \
  --working-dir /home/user/myproject \
  --mode headless
```

### Code Cleanup with Approval

```bash
codegeass task create \
  --name code-cleanup \
  --schedule "0 6 * * 6" \
  --prompt "Clean up the codebase:
- Remove unused imports
- Fix formatting issues
- Add missing type hints
Create small, focused changes." \
  --working-dir /home/user/myproject \
  --mode autonomous \
  --plan-mode
```

## Testing Your Task

Always test manually before enabling schedules:

```bash
# Run the task immediately
codegeass task run daily-review

# Check the output
codegeass logs list --limit 1
codegeass logs show <execution-id>
```

## Modifying Tasks

Tasks are stored in `config/schedules.yaml`. You can:

### Edit via CLI

```bash
# Disable temporarily
codegeass task disable daily-review

# Re-enable
codegeass task enable daily-review

# Delete
codegeass task delete old-task
```

### Edit YAML Directly

```yaml
# config/schedules.yaml
tasks:
  - id: daily-review
    name: Daily Review
    schedule: "0 9 * * 1-5"
    prompt: "Your updated prompt here"
    working_dir: /home/user/myproject
    enabled: true
    mode: headless
```

## Best Practices

1. **Start simple** - Begin with headless mode and basic prompts
2. **Test first** - Always run manually before scheduling
3. **Use plan mode** - For autonomous tasks, enable approval workflow
4. **Enable notifications** - Know when tasks complete or fail
5. **Review logs** - Check execution history regularly
6. **Iterate** - Refine prompts based on results

## Common Patterns

### Analysis + Report

```bash
--prompt "Analyze X and generate a report with:
1. Summary
2. Key findings
3. Recommendations"
```

### Check + Alert

```bash
--prompt "Check for X. If issues found, list them clearly.
If no issues, respond with 'All clear.'"
```

### Review + Suggest

```bash
--prompt "Review X and suggest improvements.
For each suggestion, explain why and provide example code."
```

## Next Steps

- [Scheduling](../concepts/scheduling.md) - Learn CRON expressions
- [Execution Modes](../concepts/execution.md) - Understand modes
- [Plan Mode](../concepts/plan-mode.md) - Set up approval workflow
- [Notifications](setup-notifications.md) - Get alerted on completion
