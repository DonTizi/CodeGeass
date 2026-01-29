---
name: code-review
description: Automated code review with focus on security, performance, and maintainability. Use when reviewing code changes, PRs, or performing scheduled audits.
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob, Bash(git diff *), Bash(git log *), Bash(git status)
disable-model-invocation: true
---

# Automated Code Review

You are performing an automated code review for the project at `$ARGUMENTS`.

## Focus Areas
- **Security**: Check for vulnerabilities, injection risks, exposed secrets
- **Performance**: Identify inefficient code, N+1 queries, memory leaks
- **Maintainability**: Code clarity, complexity, proper abstractions
- **Best Practices**: Language idioms, design patterns, testing

## Dynamic Context
- Recent changes: !`git diff HEAD~5 --stat 2>/dev/null || echo "No recent changes"`
- Current branch: !`git branch --show-current 2>/dev/null || echo "unknown"`
- Uncommitted changes: !`git status --short 2>/dev/null || echo "Not a git repo"`

## Instructions

1. **Gather Context**
   - Check `git status` for current state
   - Review `git diff` for recent changes
   - Identify the most modified files

2. **Analyze Code**
   - Focus on files with recent changes
   - Check for security issues (hardcoded secrets, SQL injection, XSS)
   - Look for performance problems
   - Evaluate code organization and readability

3. **Provide Feedback**
   - Be specific with file paths and line numbers
   - Explain why something is an issue
   - Suggest concrete fixes
   - Rate severity: low | medium | high | critical

## Output Format

Return a JSON report:
```json
{
  "summary": "Brief overview of code health",
  "files_reviewed": ["list of files"],
  "issues": [
    {
      "file": "path/to/file.py",
      "line": 42,
      "severity": "high",
      "category": "security",
      "description": "SQL query uses string concatenation",
      "suggestion": "Use parameterized queries instead"
    }
  ],
  "recommendations": [
    "General improvement suggestions"
  ],
  "metrics": {
    "total_issues": 5,
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 2
  }
}
```

For detailed report template, see [templates/report.md](templates/report.md).
