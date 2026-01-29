# CodeGeass CLI Reference

Complete reference for all CodeGeass command-line interface commands.

## Installation

```bash
cd /path/to/codegeass
pip install -e .
```

After installation, the `codegeass` command is available globally.

## Global Options

```bash
codegeass [OPTIONS] COMMAND [ARGS]...

Options:
  --config PATH    Config directory (default: ./config)
  --data PATH      Data directory (default: ./data)
  --verbose, -v    Enable verbose output
  --help           Show help and exit
```

---

## Task Commands

Manage scheduled tasks.

### `codegeass task list`

List all configured tasks.

```bash
codegeass task list [OPTIONS]

Options:
  --enabled      Show only enabled tasks
  --disabled     Show only disabled tasks
  --format       Output format: table, json, yaml (default: table)
```

**Example Output (table):**

```
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ ID         ┃ Name           ┃ Schedule      ┃ Skill     ┃ Last Run           ┃ Status   ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ abc12345   │ daily-review   │ 0 9 * * 1-5   │ code-     │ 2026-01-29 09:15   │ ✓ success│
│            │                │               │ review    │                    │          │
│ def67890   │ test-runner    │ 0 */4 * * *   │ -         │ 2026-01-29 08:00   │ ✗ failure│
│ ghi11223   │ security-scan  │ 0 2 * * 0     │ security  │ Never              │ - pending│
└────────────┴────────────────┴───────────────┴───────────┴────────────────────┴──────────┘
```

**Example Output (json):**

```bash
codegeass task list --format json
```

```json
[
  {
    "id": "abc12345",
    "name": "daily-review",
    "schedule": "0 9 * * 1-5",
    "skill": "code-review",
    "enabled": true,
    "last_run": "2026-01-29T09:15:00",
    "last_status": "success"
  }
]
```

---

### `codegeass task create`

Create a new scheduled task.

```bash
codegeass task create [OPTIONS]

Required:
  --name TEXT           Unique task name
  --schedule TEXT       CRON expression
  --working-dir PATH    Working directory (absolute path)

Optional:
  --skill TEXT          Skill to execute
  --prompt TEXT         Direct prompt (if no skill)
  --model TEXT          Model: haiku, sonnet, opus (default: sonnet)
  --timeout INT         Timeout in seconds (default: 300)
  --max-turns INT       Max agentic turns
  --autonomous          Skip permission prompts
  --disabled            Create in disabled state
  --allowed-tools TEXT  Comma-separated tool list
```

**Examples:**

```bash
# Create task using a skill
codegeass task create \
  --name daily-review \
  --schedule "0 9 * * 1-5" \
  --working-dir /home/user/project \
  --skill code-review

# Create task with direct prompt
codegeass task create \
  --name test-runner \
  --schedule "0 */4 * * *" \
  --working-dir /home/user/project \
  --prompt "Run all tests and report failures" \
  --model haiku \
  --timeout 600

# Create autonomous task
codegeass task create \
  --name auto-format \
  --schedule "0 3 * * *" \
  --working-dir /home/user/project \
  --prompt "Format all code using prettier" \
  --autonomous \
  --allowed-tools "Read,Write,Bash"
```

**Output:**

```
✓ Task created successfully

  ID:       abc12345
  Name:     daily-review
  Schedule: 0 9 * * 1-5 (At 09:00 on weekdays)
  Skill:    code-review
  Model:    sonnet
  Enabled:  Yes

Next run: 2026-01-30 09:00:00
```

---

### `codegeass task show`

Show detailed information about a task.

```bash
codegeass task show <task_id_or_name>
```

**Example:**

```bash
codegeass task show daily-review
```

**Output:**

```
Task: daily-review
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ID:          abc12345
  Name:        daily-review
  Enabled:     Yes

  Schedule:    0 9 * * 1-5
  Description: At 09:00 on weekdays
  Next Run:    2026-01-30 09:00:00

  Execution:
    Skill:     code-review
    Model:     sonnet
    Timeout:   300s
    Max Turns: unlimited
    Autonomous: No

  Working Dir: /home/user/project

  Last Execution:
    Run:       2026-01-29 09:15:00
    Status:    success
    Duration:  45.2s

  Statistics:
    Total Runs:    150
    Success Rate:  94.7%
    Avg Duration:  42.3s
```

---

### `codegeass task edit`

Edit an existing task.

```bash
codegeass task edit <task_id_or_name> [OPTIONS]

Options:
  --name TEXT           New task name
  --schedule TEXT       New CRON expression
  --working-dir PATH    New working directory
  --skill TEXT          New skill (use --no-skill to clear)
  --prompt TEXT         New prompt
  --model TEXT          New model
  --timeout INT         New timeout
  --max-turns INT       New max turns
  --autonomous/--no-autonomous
  --enabled/--disabled
```

**Example:**

```bash
# Change schedule
codegeass task edit daily-review --schedule "0 10 * * 1-5"

# Disable task
codegeass task edit daily-review --disabled

# Change model
codegeass task edit daily-review --model opus
```

**Output:**

```
✓ Task updated successfully

Changed:
  schedule: 0 9 * * 1-5 → 0 10 * * 1-5

Next run: 2026-01-30 10:00:00
```

---

### `codegeass task delete`

Delete a task.

```bash
codegeass task delete <task_id_or_name> [OPTIONS]

Options:
  --force, -f    Skip confirmation prompt
  --keep-logs    Don't delete execution logs
```

**Example:**

```bash
codegeass task delete test-runner
```

**Output:**

```
Are you sure you want to delete task 'test-runner'? [y/N]: y

✓ Task deleted
✓ Execution logs cleared (23 entries)
```

---

### `codegeass task enable`

Enable a disabled task.

```bash
codegeass task enable <task_id_or_name>
```

**Output:**

```
✓ Task 'daily-review' enabled
  Next run: 2026-01-30 09:00:00
```

---

### `codegeass task disable`

Disable a task (stops scheduled execution).

```bash
codegeass task disable <task_id_or_name>
```

**Output:**

```
✓ Task 'daily-review' disabled
  Scheduled runs suspended
```

---

### `codegeass task run`

Run a task manually (ignoring schedule).

```bash
codegeass task run <task_id_or_name> [OPTIONS]

Options:
  --dry-run      Simulate execution without running
  --wait, -w     Wait for completion and show output
  --background   Run in background (default)
```

**Example:**

```bash
codegeass task run daily-review --wait
```

**Output (waiting):**

```
⟳ Running task 'daily-review'...
  Session: session-abc123
  Started: 2026-01-29 14:30:00

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Claude is reviewing code...]

Found 3 issues:
1. src/utils.ts:45 - Unused variable 'temp'
2. src/api.ts:123 - Missing error handling
3. src/config.ts:8 - Hardcoded secret

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Task completed successfully
  Duration: 45.2s
  Exit code: 0
```

**Output (dry run):**

```bash
codegeass task run daily-review --dry-run
```

```
Dry run for task 'daily-review':

  Command that would execute:
    claude -p "/code-review" \
           --output-format json \
           --model sonnet \
           --max-turns 10

  Working directory: /home/user/project
  Timeout: 300s

No changes made.
```

---

## Skill Commands

Manage Claude Code skills.

### `codegeass skill list`

List all available skills.

```bash
codegeass skill list [OPTIONS]

Options:
  --format       Output format: table, json (default: table)
```

**Output:**

```
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Name           ┃ Description                               ┃ Context  ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ code-review    │ Review code for issues and improvements   │ inline   │
│ test-generator │ Generate unit tests for functions         │ fork     │
│ security-scan  │ Scan for security vulnerabilities         │ inline   │
│ doc-generator  │ Generate documentation from code          │ inline   │
│ refactor       │ Refactor code for better maintainability  │ fork     │
└────────────────┴───────────────────────────────────────────┴──────────┘

5 skills found in .claude/skills/
```

---

### `codegeass skill show`

Show detailed skill information.

```bash
codegeass skill show <skill_name>
```

**Example:**

```bash
codegeass skill show code-review
```

**Output:**

```
Skill: code-review
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Path:        /home/user/project/.claude/skills/code-review
  Context:     inline
  Agent:       None

  Description:
    Review code for issues and improvements

  Allowed Tools:
    - Read
    - Grep
    - Glob
    - WebSearch

  Dynamic Commands:
    - git diff
    - npm test

  Content Preview:
  ─────────────────────────────────────────
  # Code Review Skill

  Review the codebase for:
  1. Code quality issues
  2. Security vulnerabilities
  3. Performance problems
  4. Best practice violations

  $ARGUMENTS
  ─────────────────────────────────────────
```

---

### `codegeass skill reload`

Reload skills from disk (rescans .claude/skills/).

```bash
codegeass skill reload
```

**Output:**

```
⟳ Reloading skills...

Found 5 skills:
  + code-review (unchanged)
  + test-generator (unchanged)
  + security-scan (unchanged)
  + doc-generator (NEW)
  - old-skill (REMOVED)

✓ Skills reloaded
```

---

## Scheduler Commands

Control the scheduler.

### `codegeass scheduler status`

Show scheduler status.

```bash
codegeass scheduler status
```

**Output:**

```
Scheduler Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Status:         Running
  Check Interval: 60s
  Max Concurrent: 1

  Tasks:
    Total:    10
    Enabled:  8
    Due Now:  2

  Last Check:  2026-01-29 14:29:00
  Next Check:  2026-01-29 14:30:00

  Due Tasks:
    • daily-review (due at 14:30)
    • test-runner (due at 14:30)
```

---

### `codegeass scheduler run-due`

Run all tasks that are currently due.

```bash
codegeass scheduler run-due [OPTIONS]

Options:
  --window INT     Time window in seconds (default: 60)
  --dry-run        Simulate without executing
  --wait           Wait for completion
```

**Example:**

```bash
codegeass scheduler run-due --wait
```

**Output:**

```
Found 2 due tasks:
  • daily-review
  • test-runner

⟳ Running daily-review...
✓ daily-review completed (45.2s) - success

⟳ Running test-runner...
✗ test-runner failed (12.5s) - failure
  Error: Tests failed with 3 errors

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Summary:
  Completed: 2
  Success:   1
  Failure:   1

Total time: 57.7s
```

---

### `codegeass scheduler upcoming`

Show upcoming scheduled runs.

```bash
codegeass scheduler upcoming [OPTIONS]

Options:
  --hours INT    Hours to look ahead (default: 24)
  --limit INT    Max results (default: 20)
```

**Example:**

```bash
codegeass scheduler upcoming --hours 48
```

**Output:**

```
Upcoming Runs (next 48 hours)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  2026-01-29 15:00   test-runner        0 */4 * * *
  2026-01-29 19:00   test-runner        0 */4 * * *
  2026-01-29 23:00   test-runner        0 */4 * * *
  2026-01-30 02:00   security-scan      0 2 * * *
  2026-01-30 03:00   test-runner        0 */4 * * *
  2026-01-30 09:00   daily-review       0 9 * * 1-5
  2026-01-30 11:00   test-runner        0 */4 * * *
  ...

12 runs scheduled
```

---

## Log Commands

View execution logs.

### `codegeass logs list`

List execution logs.

```bash
codegeass logs list [OPTIONS]

Options:
  --task TEXT       Filter by task name or ID
  --status TEXT     Filter by status: success, failure, timeout
  --since TEXT      Show logs since (e.g., "1h", "24h", "7d")
  --limit INT       Max results (default: 50)
  --format          Output format: table, json
```

**Example:**

```bash
codegeass logs list --task daily-review --limit 5
```

**Output:**

```
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Timestamp           ┃ Task           ┃ Status   ┃ Duration   ┃ Session        ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ 2026-01-29 09:15    │ daily-review   │ ✓ success│ 45.2s      │ session-abc123 │
│ 2026-01-28 09:12    │ daily-review   │ ✓ success│ 38.5s      │ session-def456 │
│ 2026-01-27 09:18    │ daily-review   │ ✓ success│ 52.1s      │ session-ghi789 │
│ 2026-01-24 09:22    │ daily-review   │ ✗ failure│ 15.3s      │ session-jkl012 │
│ 2026-01-23 09:10    │ daily-review   │ ✓ success│ 41.8s      │ session-mno345 │
└─────────────────────┴────────────────┴──────────┴────────────┴────────────────┘
```

---

### `codegeass logs show`

Show detailed log entry.

```bash
codegeass logs show <session_id>
```

**Example:**

```bash
codegeass logs show session-abc123
```

**Output:**

```
Execution Log: session-abc123
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Task:      daily-review (abc12345)
  Status:    success
  Started:   2026-01-29 09:15:00
  Finished:  2026-01-29 09:15:45
  Duration:  45.2s
  Exit Code: 0

Output:
─────────────────────────────────────────
Reviewing codebase for issues...

Found 3 issues:

1. [WARNING] src/utils.ts:45
   Unused variable 'temp'

2. [ERROR] src/api.ts:123
   Missing error handling for API call

3. [INFO] src/config.ts:8
   Consider using environment variable

Review complete. 3 issues found.
─────────────────────────────────────────
```

---

### `codegeass logs stats`

Show execution statistics.

```bash
codegeass logs stats [OPTIONS]

Options:
  --task TEXT    Stats for specific task
  --since TEXT   Stats since (e.g., "7d", "30d")
```

**Example:**

```bash
codegeass logs stats --since 30d
```

**Output:**

```
Execution Statistics (last 30 days)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Total Executions:  450

  By Status:
    ✓ Success:       420 (93.3%)
    ✗ Failure:        25 (5.6%)
    ⏱ Timeout:         5 (1.1%)

  Performance:
    Avg Duration:    42.3s
    Min Duration:    12.1s
    Max Duration:   298.5s

  By Task:
  ┏━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
  ┃ Task           ┃ Runs   ┃ Success  ┃ Avg Duration  ┃
  ┡━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
  │ daily-review   │ 22     │ 95.5%    │ 45.2s         │
  │ test-runner    │ 180    │ 92.2%    │ 38.1s         │
  │ security-scan  │ 4      │ 100%     │ 120.5s        │
  └────────────────┴────────┴──────────┴───────────────┘
```

---

### `codegeass logs clear`

Clear execution logs.

```bash
codegeass logs clear [OPTIONS]

Options:
  --task TEXT    Clear logs for specific task
  --before TEXT  Clear logs before date (ISO format)
  --force        Skip confirmation
```

**Example:**

```bash
codegeass logs clear --task test-runner
```

**Output:**

```
This will delete 180 log entries for task 'test-runner'.
Are you sure? [y/N]: y

✓ Cleared 180 log entries
```

---

## Common Patterns

### Cron Expression Reference

| Expression | Description |
|------------|-------------|
| `* * * * *` | Every minute |
| `0 * * * *` | Every hour |
| `0 9 * * *` | Daily at 9:00 AM |
| `0 9 * * 1-5` | Weekdays at 9:00 AM |
| `0 9 * * 0` | Sundays at 9:00 AM |
| `0 */2 * * *` | Every 2 hours |
| `*/15 * * * *` | Every 15 minutes |
| `0 9,17 * * *` | At 9:00 AM and 5:00 PM |
| `0 0 1 * *` | First of each month |
| `0 0 * * 1` | Every Monday at midnight |

### Workflow Examples

**Daily code review:**
```bash
codegeass task create \
  --name daily-review \
  --schedule "0 9 * * 1-5" \
  --working-dir /path/to/project \
  --skill code-review
```

**Hourly test runs:**
```bash
codegeass task create \
  --name test-watcher \
  --schedule "0 * * * *" \
  --working-dir /path/to/project \
  --prompt "Run tests and report any failures" \
  --model haiku \
  --timeout 600
```

**Weekly security scan:**
```bash
codegeass task create \
  --name security-scan \
  --schedule "0 2 * * 0" \
  --working-dir /path/to/project \
  --skill security-scan \
  --model opus
```

**Nightly auto-formatting:**
```bash
codegeass task create \
  --name auto-format \
  --schedule "0 3 * * *" \
  --working-dir /path/to/project \
  --prompt "Format all code with prettier and commit changes" \
  --autonomous
```
