# provider

Manage code execution providers.

## Usage

```bash
codegeass provider [OPTIONS] COMMAND [ARGS]...
```

## Commands

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

Specify a provider when creating tasks:

```bash
# Use Claude (default)
codegeass task create --name my-task --code-source claude ...

# Use Codex
codegeass task create --name my-task --code-source codex ...
```

## Related

- [Execution Modes](../concepts/execution.md) - Provider capabilities
- [Tasks](task.md) - Using providers with tasks
