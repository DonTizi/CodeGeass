# provider

Manage code execution providers.

CodeGeass supports multiple code execution providers, allowing you to run tasks with different AI coding assistants.

## Usage

```bash
codegeass provider [OPTIONS] COMMAND [ARGS]...
```

## Commands

| Command | Description |
|---------|-------------|
| `list` | List all registered code execution providers |
| `info` | Show detailed information about a provider |
| `check` | Check availability of all providers |

## Available Providers

| Provider | Display Name | Capabilities |
|----------|-------------|--------------|
| `claude` | Claude Code | plan, resume, auto, stream |
| `codex` | OpenAI Codex | auto, stream |

### Capabilities

- **plan** - Supports plan mode (approval before execution)
- **resume** - Supports session resume
- **auto** - Supports autonomous mode
- **stream** - Supports streaming output

## Commands Detail

### list

List all available code execution providers.

```bash
codegeass provider list
```

Output shows:
- Provider name
- Availability status (✓ available, ✗ not found)
- Short description

### info

Show detailed information about a specific provider.

```bash
codegeass provider info <provider-name>
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `provider-name` | Name of the provider (e.g., `claude`, `codex`) |

**Output includes:**

- Provider name and description
- Executable path
- Available models
- Supported capabilities (headless, autonomous, skill, plan-mode)
- Configuration requirements

### check

Check availability of all providers.

```bash
codegeass provider check
```

## Examples

### List Available Providers

```bash
$ codegeass provider list

Available Providers
┏━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Name    ┃ Available ┃ Description                              ┃
┡━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ claude  │ ✓         │ Anthropic's Claude Code CLI              │
│ codex   │ ✓         │ OpenAI Codex CLI                         │
└─────────┴───────────┴──────────────────────────────────────────┘
```

### Get Provider Details

```bash
$ codegeass provider info claude

Provider: claude
Description: Anthropic's Claude Code CLI
Executable: /usr/local/bin/claude
Available: ✓

Models:
  - opus
  - sonnet
  - haiku

Capabilities:
  ✓ headless
  ✓ autonomous
  ✓ skill
  ✓ plan_mode
```

## Supported Providers

| Provider | CLI Tool | Description |
|----------|----------|-------------|
| `claude` | `claude` | Anthropic's Claude Code - default provider |
| `codex` | `codex` | OpenAI Codex CLI for code generation |

## Using Providers with Tasks

When creating or updating a task, specify the provider with `--code-source`:

```bash
# Create task with Claude (default)
codegeass task create \
  --name daily-review \
  --schedule "0 9 * * *" \
  --prompt "Review code changes" \
  --code-source claude

# Create task with Codex
codegeass task create \
  --name codex-task \
  --schedule "0 10 * * *" \
  --prompt "Analyze dependencies" \
  --code-source codex
```

## Provider Requirements

### Claude Code

- **Requirement**: Claude CLI installed (`claude` command available)
- **Installation**: See [Claude Code documentation](https://claude.ai/code)
- **Default**: Used when no provider is specified

### OpenAI Codex

- **Requirement**: Codex CLI installed (`codex` command available)
- **Status**: Experimental support

## Related

- [Execution Modes](../concepts/execution.md) - Provider capabilities
- [Tasks](task.md) - Using providers with tasks
