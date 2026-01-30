---
name: review
description: Comprehensive code review for PRs or recent changes. Checks correctness, security, performance, maintainability, and tests.
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob, Bash(git diff *), Bash(git log *), Bash(git status), Bash(git show *)
disable-model-invocation: true
---

# Code Review Instructions

Review the code for:
- **Correctness**: Logic errors, edge cases, null handling
- **Security**: Injection, XSS, secrets exposure, auth issues
- **Performance**: N+1 queries, unnecessary loops, memory leaks
- **Maintainability**: Complexity, naming, documentation
- **Tests**: Coverage, edge cases, meaningful assertions

## Dynamic Context
- Recent changes: !`git diff HEAD~5 --stat 2>/dev/null || echo "No recent changes"`
- Current branch: !`git branch --show-current 2>/dev/null || echo "unknown"`
- Uncommitted changes: !`git status --short 2>/dev/null || echo "Not a git repo"`

## Review Process

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
   - Rate severity

## Severity Ratings

Format: Provide feedback as:
- Critical: Must fix before merge
- Important: Should fix, but not blocking
- Suggestion: Nice to have improvements

## Output Format

Return a structured report:
```json
{
  "summary": "Brief overview of code health",
  "files_reviewed": ["list of files"],
  "issues": [
    {
      "file": "path/to/file.py",
      "line": 42,
      "severity": "critical|important|suggestion",
      "category": "security|performance|correctness|maintainability",
      "description": "What's wrong",
      "suggestion": "How to fix it"
    }
  ],
  "recommendations": [
    "General improvement suggestions"
  ],
  "metrics": {
    "total_issues": 5,
    "critical": 0,
    "important": 1,
    "suggestions": 4
  }
}
```

$ARGUMENTS
