---
name: release
description: Release a new version to PyPI (commit, tag, push, publish)
---

# Release CodeGeass v$ARGUMENTS to PyPI

You are releasing version **$ARGUMENTS** of CodeGeass.

## Pre-flight Checks

1. **Verify version format** - Must be semver (e.g., `0.2.0`, `1.0.0`)
2. **Check current version** in `pyproject.toml`
3. **Ensure working directory is clean** - No uncommitted changes (except version bump)

## Release Steps

### Step 1: Update Version

Edit `pyproject.toml` and change:
```toml
version = "$ARGUMENTS"
```

### Step 2: Update CHANGELOG.md

Add a new section for this version:
```markdown
## [$ARGUMENTS] - YYYY-MM-DD

### Added
- (list new features)

### Changed
- (list changes)

### Fixed
- (list fixes)
```

Move items from `[Unreleased]` to the new version section.

Update the links at the bottom:
```markdown
[Unreleased]: https://github.com/DonTizi/CodeGeass/compare/v$ARGUMENTS...HEAD
[$ARGUMENTS]: https://github.com/DonTizi/CodeGeass/compare/vPREVIOUS...v$ARGUMENTS
```

### Step 3: Commit Changes

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "Release v$ARGUMENTS"
```

### Step 4: Push to Main

```bash
git push origin main
```

### Step 5: Create and Push Tag

```bash
git tag v$ARGUMENTS
git push origin v$ARGUMENTS
```

## Post-Release

After pushing the tag, GitHub Actions will automatically:
1. Build the package
2. Run tests
3. Publish to PyPI
4. Create GitHub Release
5. Deploy documentation

**Monitor the release**: https://github.com/DonTizi/CodeGeass/actions

**Verify on PyPI**: https://pypi.org/project/codegeass/

## Rollback (if needed)

If the release fails:
```bash
# Delete remote tag
git push origin :refs/tags/v$ARGUMENTS

# Delete local tag
git tag -d v$ARGUMENTS

# Fix issues and retry
```
