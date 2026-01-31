# provider

Manage code execution providers.

## Overview

CodeGeass supports multiple code execution providers, enabling you to use different AI coding assistants beyond Claude Code. The provider system uses an adapter pattern to normalize outputs across different tools.

## Usage

```bash
codegeass provider [OPTIONS] COMMAND [ARGS]...
```

## Commands

### list

List all available providers.

```bash
codegeass provider list
```

**Example output:**

```
┌───────────────┬──────────┬─────────────────────────────────────────────┐
│ Provider      │ Status   │ Description                                 │
├───────────────┼──────────┼─────────────────────────────────────────────┤
│ claude-code   │ Active   │ Claude Code (Anthropic) - default           │
│ codex         │ Available│ OpenAI Codex                                │
└───────────────┴──────────┴─────────────────────────────────────────────┘
```

### info

Show detailed information about a specific provider.

```bash
codegeass provider info <provider-name>
```

**Example:**

```bash
codegeass provider info claude-code
```

**Output:**

```
Provider: claude-code
Description: Claude Code by Anthropic
Status: Active (default)

Capabilities:
  - File Operations: Yes
  - Shell Commands: Yes
  - Web Search: Yes
  - MCP Support: Yes

Supported Models:
  - haiku (fast, cost-effective)
  - sonnet (balanced)
  - opus (most capable)

Configuration:
  - Subscription Mode: Uses Pro/Max subscription
  - API Mode: Requires ANTHROPIC_API_KEY
```

## Using Providers with Tasks

### Creating Tasks with a Specific Provider

Use the `--code-source` flag when creating tasks:

```bash
# Create task using OpenAI Codex
codegeass task create \
  --name codex-review \
  --schedule "0 9 * * *" \
  --prompt "Review the latest changes" \
  --code-source codex

# Create task using Claude Code (default)
codegeass task create \
  --name claude-review \
  --schedule "0 10 * * *" \
  --prompt "Analyze code quality"
```

### Running Tasks with a Different Provider

```bash
# Override provider for a single run
codegeass task run my-task --code-source codex
```

## Available Providers

| Provider | ID | Status | Description |
|----------|-----|--------|-------------|
| **Claude Code** | `claude-code` | Default | Anthropic's Claude Code CLI |
| **OpenAI Codex** | `codex` | Experimental | OpenAI's Codex API |

## Provider Configuration

Providers may require additional configuration via environment variables or credentials.

### Claude Code

Uses the Claude CLI. No additional configuration needed if Claude CLI is installed.

```bash
# Check Claude CLI installation
claude --version
```

### OpenAI Codex

Requires OpenAI API credentials:

```bash
# Set OpenAI API key
export OPENAI_API_KEY="sk-..."
```

Or add to credentials file (`~/.codegeass/credentials.yaml`):

```yaml
openai:
  api_key: "sk-..."
```

## Provider Capabilities

Different providers have different capabilities:

| Capability | Claude Code | Codex |
|------------|-------------|-------|
| Read files | Yes | Yes |
| Write files | Yes | Yes |
| Run commands | Yes | Limited |
| Web search | Yes | No |
| MCP tools | Yes | No |
| Plan mode | Yes | No |

## Dashboard Integration

The Dashboard includes a provider selector in the task creation form, allowing you to choose the execution provider visually.

## API Endpoint

The API exposes provider information at:

```
GET /api/providers
```

Returns a list of available providers with their capabilities.

## Related

- [Task Management](task.md) - Creating and managing tasks
- [Execution Modes](../concepts/execution.md) - Understanding execution strategies
