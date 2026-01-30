# project

Manage multiple CodeGeass projects from a single installation.

## Overview

The `project` command group allows you to register, configure, and switch between multiple projects. Each project has its own tasks, skills, and configuration.

## Commands

::: mkdocs-click
    :module: codegeass.cli.commands.project
    :command: project
    :prog_name: codegeass project
    :depth: 2

## Examples

### Register Your First Project

```bash
# Register the current directory
cd /path/to/my-project
codegeass project add .

# Or specify the path
codegeass project add /path/to/my-project --set-default
```

### Add Multiple Projects

```bash
# Add several projects
codegeass project add ~/projects/api --name api-server
codegeass project add ~/projects/frontend --name web-app
codegeass project add ~/projects/mobile --name mobile-app

# List all
codegeass project list
```

### Configure Project Defaults

```bash
# Set default model and timeout
codegeass project add ~/projects/ml-pipeline \
  --name ml-pipeline \
  --model opus \
  --timeout 600 \
  --autonomous
```

### Work with Shared Skills

```bash
# Shared skills are enabled by default
codegeass project add ~/project

# Disable shared skills for a project when adding
codegeass project add ~/project --no-shared-skills

# Or toggle later with update
codegeass project update my-project --no-shared-skills
codegeass project update my-project --shared-skills
```

### Switch Between Projects

```bash
# Set default project
codegeass project set-default api-server

# Run commands against specific project (--project must come before the command)
codegeass --project web-app task list
codegeass --project api-server task run daily-review
```

### Initialize a New Project

```bash
# Create project structure in new directory
mkdir ~/projects/new-app
codegeass project init ~/projects/new-app

# Register it
codegeass project add ~/projects/new-app --set-default
```

## Project Structure

When you initialize a project, it creates:

```
project/
├── config/
│   ├── schedules.yaml     # Task definitions
│   └── settings.yaml      # Project settings
├── data/
│   ├── logs/              # Execution logs
│   └── sessions/          # Session data
└── .claude/
    └── skills/            # Project-specific skills
```

## See Also

- [Projects Concept](../concepts/projects.md) - Understanding multi-project support
- [Skills](../concepts/skills.md) - Shared and project skills
- [Configuration](../getting-started/configuration.md) - Configuration files
