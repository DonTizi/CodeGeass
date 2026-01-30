---
name: security-scan
description: Deep security analysis of codebase. Scans for secrets, vulnerabilities, and insecure patterns.
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob, Bash(git log *), Bash(pip-audit), Bash(npm audit), Bash(find * -name *)
disable-model-invocation: true
---

# Security Scan Instructions

Perform a comprehensive security scan on the codebase.

## 1. Secrets Detection

Search for exposed credentials:
- API keys and tokens (AWS, GCP, Stripe, etc.)
- Passwords and secrets
- Private keys and certificates
- Connection strings
- Environment variable references in code

### Patterns to Search
```
- password=
- api_key=
- secret=
- token=
- private_key
- -----BEGIN.*PRIVATE KEY-----
- AKIA[A-Z0-9]{16}  # AWS Access Key
- sk_live_  # Stripe
- ghp_  # GitHub Personal Token
```

## 2. Dependency Vulnerabilities

Check for vulnerable dependencies:
- Run: `pip-audit` (Python) or `npm audit` (JS)
- Check for CVEs in dependencies
- Identify outdated packages with known vulnerabilities

## 3. Code Vulnerabilities

Scan for:
- **SQL/NoSQL injection**: Unparameterized queries
- **Command injection**: Unsafe shell execution
- **XSS vulnerabilities**: Unsanitized user input in HTML
- **Path traversal**: Unchecked file paths
- **Insecure deserialization**: Unsafe pickle/yaml loading
- **Hardcoded credentials**: Passwords in source

## 4. Configuration Issues

Check for:
- Debug mode in production configs
- Permissive CORS settings
- Missing security headers
- Insecure default values

## Dynamic Context
- Package files: !`find . -name "package.json" -o -name "requirements.txt" -o -name "Gemfile" -o -name "go.mod" 2>/dev/null | head -10`
- Potential secrets: !`grep -r -l "password\|secret\|api_key\|token" --include="*.py" --include="*.js" --include="*.ts" --include="*.env*" 2>/dev/null | head -5`

## Output Format

Return a JSON security report:
```json
{
  "audit_summary": "Overall security assessment",
  "risk_level": "low|medium|high|critical",
  "findings": [
    {
      "id": "SEC-001",
      "title": "Hardcoded API Key Found",
      "severity": "critical",
      "category": "secrets",
      "file": "config/settings.py",
      "line": 15,
      "description": "AWS access key hardcoded in source file",
      "evidence": "AWS_ACCESS_KEY = 'AKIA...'",
      "remediation": "Move to environment variables or secrets manager",
      "cwe": "CWE-798"
    }
  ],
  "recommendations": [
    "Enable secret scanning in CI/CD",
    "Implement dependency vulnerability scanning"
  ],
  "dependencies_checked": true,
  "files_scanned": 42
}
```

## Severity Ratings

- **Critical**: Immediate exploitation risk, data breach potential
- **High**: Significant security weakness, should fix soon
- **Medium**: Security concern, plan to address
- **Low**: Minor issue or best practice suggestion

$ARGUMENTS
