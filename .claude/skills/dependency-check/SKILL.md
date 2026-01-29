---
name: dependency-check
description: Analyze project dependencies for outdated packages, security vulnerabilities, and licensing issues. Use for dependency audits and maintenance.
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob, Bash(npm audit *), Bash(pip-audit *), Bash(npm outdated *), Bash(pip list --outdated *)
disable-model-invocation: true
---

# Dependency Check

Analyze dependencies for the project at `$ARGUMENTS`.

## Analysis Scope

### 1. Outdated Packages
Identify packages with available updates:
- Major version updates (breaking changes likely)
- Minor version updates (new features)
- Patch updates (bug fixes)

### 2. Security Vulnerabilities
Check for known vulnerabilities:
- CVE references
- Severity ratings
- Affected versions

### 3. License Compliance
Review dependency licenses:
- Identify restrictive licenses (GPL, AGPL)
- Flag license incompatibilities
- Note unknown licenses

## Dynamic Context
- Package files: !`find . -maxdepth 3 -name "package.json" -o -name "requirements.txt" -o -name "Pipfile" -o -name "go.mod" -o -name "Cargo.toml" 2>/dev/null | head -5`
- Lock files: !`find . -maxdepth 3 -name "package-lock.json" -o -name "yarn.lock" -o -name "Pipfile.lock" -o -name "poetry.lock" 2>/dev/null | head -5`

## Instructions

### For Node.js Projects

1. **Check outdated packages**:
   ```bash
   npm outdated --json 2>/dev/null || echo "{}"
   ```

2. **Run security audit**:
   ```bash
   npm audit --json 2>/dev/null || echo "{}"
   ```

### For Python Projects

1. **Check outdated packages**:
   ```bash
   pip list --outdated --format=json 2>/dev/null || echo "[]"
   ```

2. **Run security audit** (if pip-audit installed):
   ```bash
   pip-audit --format=json 2>/dev/null || echo "pip-audit not installed"
   ```

### General Checks

1. Read the dependency manifest files
2. Identify direct vs transitive dependencies
3. Check for duplicate dependencies
4. Note any pinned versions that may be outdated

## Output Format

Return a JSON dependency report:
```json
{
  "project_type": "nodejs",
  "manifest_files": ["package.json"],
  "summary": {
    "total_dependencies": 45,
    "direct": 12,
    "dev": 8,
    "outdated": 5,
    "vulnerable": 2
  },
  "outdated": [
    {
      "package": "lodash",
      "current": "4.17.15",
      "wanted": "4.17.21",
      "latest": "4.17.21",
      "type": "patch",
      "breaking_changes": false
    },
    {
      "package": "react",
      "current": "17.0.2",
      "wanted": "17.0.2",
      "latest": "18.2.0",
      "type": "major",
      "breaking_changes": true
    }
  ],
  "vulnerabilities": [
    {
      "package": "minimist",
      "severity": "high",
      "cve": "CVE-2021-44906",
      "description": "Prototype pollution",
      "fixed_in": "1.2.6",
      "recommendation": "Update to ^1.2.6"
    }
  ],
  "license_issues": [
    {
      "package": "gpl-library",
      "license": "GPL-3.0",
      "concern": "Copyleft license may require open-sourcing your code"
    }
  ],
  "recommendations": [
    "Update lodash to patch security vulnerability",
    "Consider upgrading to React 18 (breaking changes)",
    "Review GPL-licensed dependency compatibility"
  ]
}
```

## Priority Actions

1. **Critical**: Security vulnerabilities with available fixes
2. **High**: Major version updates for security fixes
3. **Medium**: Outdated packages with minor updates
4. **Low**: Patch updates, license reviews

## Notes

- Always test thoroughly after updating dependencies
- Consider using lockfiles for reproducible builds
- Set up automated dependency scanning in CI/CD
