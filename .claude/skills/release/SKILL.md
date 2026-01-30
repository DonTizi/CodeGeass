---
name: release
description: Release a new version to PyPI - updates version, changelog, commits, tags, and pushes
allowed-tools: Read, Edit, Write, Bash(git *), Bash(cat *)
---

# Release CodeGeass v$ARGUMENTS

Release version **$ARGUMENTS** to PyPI.

## Current State
- Version in pyproject.toml: !`grep -Po '(?<=^version = ")[^"]+' pyproject.toml 2>/dev/null || echo "unknown"`
- Git status: !`git status --short 2>/dev/null | head -5`
- Latest tag: !`git describe --tags --abbrev=0 2>/dev/null || echo "no tags"`

## Steps

### 1. Update Version
Edit `pyproject.toml`:
```toml
version = "$ARGUMENTS"
```

### 2. Update CHANGELOG.md
Add section for v$ARGUMENTS with today's date. Move items from [Unreleased].

### 3. Commit and Tag
```bash
git add pyproject.toml CHANGELOG.md
git commit -m "Release v$ARGUMENTS"
git push origin main
git tag v$ARGUMENTS
git push origin v$ARGUMENTS
```

### 4. Verify
- GitHub Actions: https://github.com/DonTizi/CodeGeass/actions
- PyPI: https://pypi.org/project/codegeass/

$ARGUMENTS
