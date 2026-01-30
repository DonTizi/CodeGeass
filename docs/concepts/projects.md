# Projects

CodeGeass supports managing multiple projects from a single installation through a global project registry.

## Why Multi-Project Support?

If you work on multiple codebases, you can:

- Register each project once and switch between them easily
- Share skills across all projects
- Use project-specific configurations
- Run tasks against any registered project

## How It Works

```
~/.codegeass/
├── projects.yaml         # Global project registry
└── skills/               # Shared skills (available to all projects)

/path/to/project-a/
├── config/
│   └── schedules.yaml    # Project A's tasks
└── .claude/skills/       # Project A's skills

/path/to/project-b/
├── config/
│   └── schedules.yaml    # Project B's tasks
└── .claude/skills/       # Project B's skills
```

## Project Registry

The global registry at `~/.codegeass/projects.yaml` tracks all registered projects:

```yaml
version: 1
default_project: abc12345
shared_skills_dir: ~/.codegeass/skills
projects:
  - id: abc12345
    name: my-app
    path: /home/user/projects/my-app
    description: "Main application"
    default_model: sonnet
    default_timeout: 300
    enabled: true
    use_shared_skills: true
```

## Commands

### Register a Project

```bash
# Add a project from its directory
codegeass project add /path/to/project

# Add with options
codegeass project add /path/to/project \
  --name my-project \
  --description "My awesome project" \
  --model sonnet \
  --set-default
```

### List Projects

```bash
# List enabled projects
codegeass project list

# Include disabled projects
codegeass project list --all
```

### Show Project Details

```bash
codegeass project show my-project
```

### Set Default Project

```bash
codegeass project set-default my-project
```

### Initialize a New Project

```bash
# Initialize in current directory
codegeass project init

# Initialize in specific path
codegeass project init /path/to/new-project
```

### Remove a Project

```bash
# Unregister (doesn't delete files)
codegeass project remove my-project
```

### Update Project Settings

```bash
codegeass project update my-project \
  --model opus \
  --timeout 600 \
  --shared-skills
```

### Enable/Disable Projects

```bash
codegeass project enable my-project
codegeass project disable my-project
```

## Project Auto-Detection

When you run CodeGeass commands without specifying a project:

1. **Current Directory Check**: If your current directory is within a registered project, that project is used
2. **Default Project**: Falls back to the default project if set
3. **Single-Project Mode**: If no projects are registered, uses the current directory

You can always override with the `--project` flag (must come before the command):

```bash
codegeass --project my-other-project task list
```

## Shared Skills

Skills placed in `~/.codegeass/skills/` are available to all projects:

```
~/.codegeass/skills/
├── review/
│   └── SKILL.md
├── security-scan/
│   └── SKILL.md
└── deploy/
    └── SKILL.md
```

### Skill Priority

When a skill is requested, CodeGeass looks in this order:

1. **Project skills** (`.claude/skills/`) - highest priority
2. **Shared skills** (`~/.codegeass/skills/`) - used if not found in project

This allows projects to override shared skills with custom versions.

### Disabling Shared Skills

If a project shouldn't use shared skills:

```bash
# When adding
codegeass project add /path/to/project --no-shared-skills

# Or update later
codegeass project update my-project --no-shared-skills
```

## Project Configuration

Each project can have its own defaults:

| Setting | Description | Default |
|---------|-------------|---------|
| `default_model` | Claude model to use | `sonnet` |
| `default_timeout` | Execution timeout (seconds) | `300` |
| `default_autonomous` | Enable autonomous mode | `false` |
| `use_shared_skills` | Include shared skills | `true` |

These defaults are used when creating new tasks in the project.

## Best Practices

1. **Use descriptive names** - Makes it easy to identify projects in lists
2. **Set a default project** - Saves typing for your most-used project
3. **Leverage shared skills** - Put common skills in `~/.codegeass/skills/`
4. **Project-specific overrides** - Override shared skills when needed
5. **Keep projects organized** - Remove projects you no longer use

## Related

- [Skills](skills.md) - Creating and using skills
- [Configuration](../getting-started/configuration.md) - Configuration files
- [CLI Reference](../cli/project.md) - Full command documentation
