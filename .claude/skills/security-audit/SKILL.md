---
name: security-audit
description: Deep security analysis of codebase. Checks for OWASP vulnerabilities, secrets exposure, and insecure patterns. Use for comprehensive security reviews.
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob, Bash(git log *), Bash(find * -name *)
disable-model-invocation: true
---

# Security Audit

Perform a comprehensive security audit on the project at `$ARGUMENTS`.

## Audit Scope

### 1. Secrets Detection
Search for exposed credentials:
- API keys and tokens
- Passwords and secrets
- Private keys and certificates
- Connection strings
- Environment variable references

### 2. OWASP Top 10 Vulnerabilities
Check for:
- **Injection**: SQL, NoSQL, OS command, LDAP
- **Broken Authentication**: Weak session management, credential exposure
- **Sensitive Data Exposure**: Unencrypted data, weak crypto
- **XML External Entities (XXE)**: Unsafe XML parsing
- **Broken Access Control**: Missing authorization checks
- **Security Misconfiguration**: Default configs, verbose errors
- **Cross-Site Scripting (XSS)**: Unsanitized output
- **Insecure Deserialization**: Unsafe object handling
- **Using Components with Known Vulnerabilities**: Outdated dependencies
- **Insufficient Logging**: Missing audit trails

### 3. Dependency Analysis
- Check package files for vulnerable dependencies
- Identify outdated packages

## Dynamic Context
- Package files: !`find . -name "package.json" -o -name "requirements.txt" -o -name "Gemfile" -o -name "go.mod" 2>/dev/null | head -10`
- Potential secrets: !`grep -r -l "password\|secret\|api_key\|token" --include="*.py" --include="*.js" --include="*.ts" --include="*.env*" 2>/dev/null | head -5`

## Instructions

1. **Scan for Secrets**
   ```
   # Patterns to search:
   - password=
   - api_key=
   - secret=
   - token=
   - private_key
   - -----BEGIN.*PRIVATE KEY-----
   ```

2. **Check Authentication Code**
   - Look for login/auth handlers
   - Verify password hashing (bcrypt, argon2)
   - Check session management

3. **Analyze Input Handling**
   - Find user input entry points
   - Check for validation/sanitization
   - Look for SQL query construction

4. **Review Access Control**
   - Check authorization decorators/middleware
   - Look for role-based access control

5. **Assess Dependencies**
   - Review package.json / requirements.txt
   - Note any obviously outdated versions

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
