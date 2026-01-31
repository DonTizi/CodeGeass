"""Tests for multi-platform skill resolution."""

from pathlib import Path

import pytest

from codegeass.factory.skill_resolver import (
    ChainedSkillRegistry,
    DirectorySkillResolver,
    Platform,
    PlatformConfig,
    PlatformSkillResolver,
    PLATFORMS,
    get_platform,
)
from codegeass.core.exceptions import SkillNotFoundError


class TestPlatformEnum:
    """Tests for Platform enum."""

    def test_platform_values(self):
        """Test that Platform enum has expected values."""
        assert Platform.CLAUDE.value == "claude"
        assert Platform.CODEX.value == "codex"

    def test_get_platform_valid(self):
        """Test get_platform with valid names."""
        assert get_platform("claude") == Platform.CLAUDE
        assert get_platform("codex") == Platform.CODEX
        assert get_platform("CLAUDE") == Platform.CLAUDE  # Case insensitive
        assert get_platform("Codex") == Platform.CODEX

    def test_get_platform_invalid(self):
        """Test get_platform with invalid name raises ValueError."""
        with pytest.raises(ValueError, match="Invalid platform"):
            get_platform("invalid")


class TestPlatformConfig:
    """Tests for PlatformConfig and PLATFORMS constant."""

    def test_platforms_has_expected_configs(self):
        """Test that PLATFORMS dict has Claude and Codex configs."""
        assert Platform.CLAUDE in PLATFORMS
        assert Platform.CODEX in PLATFORMS

    def test_claude_config(self):
        """Test Claude platform configuration."""
        config = PLATFORMS[Platform.CLAUDE]
        assert config.name == "claude"
        assert config.project_subdir == ".claude/skills"
        assert ".claude/skills" in str(config.global_dir)

    def test_codex_config(self):
        """Test Codex platform configuration."""
        config = PLATFORMS[Platform.CODEX]
        assert config.name == "codex"
        assert config.project_subdir == ".codex/skills"
        assert ".codex/skills" in str(config.global_dir)

    def test_config_is_frozen(self):
        """Test that PlatformConfig is immutable."""
        config = PLATFORMS[Platform.CLAUDE]
        with pytest.raises(Exception):  # frozen=True prevents modification
            config.name = "modified"


class TestDirectorySkillResolver:
    """Tests for DirectorySkillResolver."""

    @pytest.fixture
    def skills_dir(self, tmp_path):
        """Create a temporary skills directory with test skills."""
        skills_dir = tmp_path / "skills"

        # Create test skill
        skill_dir = skills_dir / "test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("""---
name: test-skill
description: A test skill
allowed-tools: Read, Grep
---

# Test Skill

Instructions for $ARGUMENTS.
""")

        return skills_dir

    def test_loads_skills_from_directory(self, skills_dir):
        """Test that skills are loaded from directory."""
        resolver = DirectorySkillResolver(skills_dir, source="test")
        skills = resolver.get_all()

        assert len(skills) == 1
        assert resolver.exists("test-skill")

    def test_get_skill(self, skills_dir):
        """Test getting a skill by name."""
        resolver = DirectorySkillResolver(skills_dir, source="test")
        skill = resolver.get("test-skill")

        assert skill is not None
        assert skill.name == "test-skill"
        assert skill.description == "A test skill"

    def test_get_nonexistent_returns_none(self, skills_dir):
        """Test that getting nonexistent skill returns None."""
        resolver = DirectorySkillResolver(skills_dir, source="test")
        skill = resolver.get("nonexistent")

        assert skill is None

    def test_source_property(self, skills_dir):
        """Test source property."""
        resolver = DirectorySkillResolver(skills_dir, source="my-source")
        assert resolver.source == "my-source"

    def test_handles_nonexistent_directory(self, tmp_path):
        """Test handling of nonexistent skills directory."""
        nonexistent = tmp_path / "nonexistent"
        resolver = DirectorySkillResolver(nonexistent, source="test")

        assert resolver.get_all() == []
        assert not resolver.exists("any-skill")


class TestPlatformSkillResolver:
    """Tests for PlatformSkillResolver."""

    @pytest.fixture
    def skills_dir(self, tmp_path):
        """Create a temporary skills directory."""
        skills_dir = tmp_path / ".claude" / "skills"
        skill_dir = skills_dir / "claude-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("""---
name: claude-skill
description: A Claude skill
---

# Claude Skill
""")
        return skills_dir

    def test_source_includes_platform_and_scope(self, skills_dir):
        """Test that source label includes platform and scope."""
        resolver = PlatformSkillResolver(skills_dir, Platform.CLAUDE, scope="project")
        assert resolver.source == "project-claude"

        resolver = PlatformSkillResolver(skills_dir, Platform.CODEX, scope="global")
        assert resolver.source == "global-codex"

    def test_platform_property(self, skills_dir):
        """Test platform property."""
        resolver = PlatformSkillResolver(skills_dir, Platform.CLAUDE, scope="project")
        assert resolver.platform == Platform.CLAUDE

    def test_scope_property(self, skills_dir):
        """Test scope property."""
        resolver = PlatformSkillResolver(skills_dir, Platform.CLAUDE, scope="project")
        assert resolver.scope == "project"


class TestChainedSkillRegistryMultiplatform:
    """Tests for ChainedSkillRegistry with multi-platform support."""

    @pytest.fixture
    def multi_platform_project(self, tmp_path):
        """Create a project with skills from multiple platforms."""
        project_dir = tmp_path / "project"

        # Create Claude project skill
        claude_skills = project_dir / ".claude" / "skills"
        claude_skill = claude_skills / "shared-skill"
        claude_skill.mkdir(parents=True)
        (claude_skill / "SKILL.md").write_text("""---
name: shared-skill
description: Shared skill from Claude (project)
---
# Claude version
""")

        # Create Claude-only project skill
        claude_only = claude_skills / "claude-only"
        claude_only.mkdir(parents=True)
        (claude_only / "SKILL.md").write_text("""---
name: claude-only
description: Claude-only skill
---
# Claude only
""")

        # Create Codex project skill (same name - should be lower priority)
        codex_skills = project_dir / ".codex" / "skills"
        codex_shared = codex_skills / "shared-skill"
        codex_shared.mkdir(parents=True)
        (codex_shared / "SKILL.md").write_text("""---
name: shared-skill
description: Shared skill from Codex (project)
---
# Codex version
""")

        # Create Codex-only project skill
        codex_only = codex_skills / "codex-only"
        codex_only.mkdir(parents=True)
        (codex_only / "SKILL.md").write_text("""---
name: codex-only
description: Codex-only skill
---
# Codex only
""")

        return project_dir

    def test_multiplatform_init(self, multi_platform_project):
        """Test initialization with multiple platforms."""
        registry = ChainedSkillRegistry(
            project_dir=multi_platform_project,
            platforms=[Platform.CLAUDE, Platform.CODEX],
            include_global=False,
        )

        # Should have 2 resolvers (one per platform for project)
        assert len(registry.resolvers) == 2

    def test_multiplatform_with_global(self, multi_platform_project):
        """Test initialization includes global resolvers."""
        registry = ChainedSkillRegistry(
            project_dir=multi_platform_project,
            platforms=[Platform.CLAUDE, Platform.CODEX],
            include_global=True,
        )

        # Should have 4 resolvers (project + global for each platform)
        assert len(registry.resolvers) == 4

    def test_priority_order(self, multi_platform_project):
        """Test that Claude project skills take priority over Codex."""
        registry = ChainedSkillRegistry(
            project_dir=multi_platform_project,
            platforms=[Platform.CLAUDE, Platform.CODEX],
            include_global=False,
        )

        # shared-skill exists in both - Claude should win
        skill = registry.get("shared-skill")
        assert skill.description == "Shared skill from Claude (project)"

    def test_get_source(self, multi_platform_project):
        """Test get_source returns correct platform and scope."""
        registry = ChainedSkillRegistry(
            project_dir=multi_platform_project,
            platforms=[Platform.CLAUDE, Platform.CODEX],
            include_global=False,
        )

        assert registry.get_source("shared-skill") == "project-claude"
        assert registry.get_source("claude-only") == "project-claude"
        assert registry.get_source("codex-only") == "project-codex"

    def test_get_all_deduplicates(self, multi_platform_project):
        """Test that get_all deduplicates by name."""
        registry = ChainedSkillRegistry(
            project_dir=multi_platform_project,
            platforms=[Platform.CLAUDE, Platform.CODEX],
            include_global=False,
        )

        skills = registry.get_all()
        names = [s.name for s in skills]

        # shared-skill should only appear once
        assert names.count("shared-skill") == 1
        # All unique skills should be present
        assert "claude-only" in names
        assert "codex-only" in names

    def test_get_all_with_source(self, multi_platform_project):
        """Test get_all_with_source returns tuples with source."""
        registry = ChainedSkillRegistry(
            project_dir=multi_platform_project,
            platforms=[Platform.CLAUDE, Platform.CODEX],
            include_global=False,
        )

        skills_with_source = registry.get_all_with_source()
        sources = {name: source for (skill, source) in skills_with_source for name in [skill.name]}

        assert sources["shared-skill"] == "project-claude"
        assert sources["claude-only"] == "project-claude"
        assert sources["codex-only"] == "project-codex"

    def test_single_platform(self, multi_platform_project):
        """Test with only Claude platform enabled."""
        registry = ChainedSkillRegistry(
            project_dir=multi_platform_project,
            platforms=[Platform.CLAUDE],
            include_global=False,
        )

        assert registry.exists("claude-only")
        assert registry.exists("shared-skill")
        assert not registry.exists("codex-only")  # Codex not enabled

    def test_get_skills_by_platform(self, multi_platform_project):
        """Test filtering skills by platform."""
        registry = ChainedSkillRegistry(
            project_dir=multi_platform_project,
            platforms=[Platform.CLAUDE, Platform.CODEX],
            include_global=False,
        )

        claude_skills = registry.get_skills_by_platform(Platform.CLAUDE)
        claude_names = [s.name for s in claude_skills]
        assert "claude-only" in claude_names
        assert "shared-skill" in claude_names
        assert "codex-only" not in claude_names

        codex_skills = registry.get_skills_by_platform(Platform.CODEX)
        codex_names = [s.name for s in codex_skills]
        assert "codex-only" in codex_names
        # shared-skill is deduplicated - Claude version wins globally

    def test_get_skills_by_scope(self, multi_platform_project):
        """Test filtering skills by scope."""
        registry = ChainedSkillRegistry(
            project_dir=multi_platform_project,
            platforms=[Platform.CLAUDE, Platform.CODEX],
            include_global=False,
        )

        project_skills = registry.get_skills_by_scope("project")
        project_names = [s.name for s in project_skills]

        assert "claude-only" in project_names
        assert "codex-only" in project_names
        assert "shared-skill" in project_names

    def test_platforms_property(self, multi_platform_project):
        """Test platforms property returns configured platforms."""
        registry = ChainedSkillRegistry(
            project_dir=multi_platform_project,
            platforms=[Platform.CLAUDE],
            include_global=False,
        )

        assert registry.platforms == [Platform.CLAUDE]


class TestChainedSkillRegistryLegacy:
    """Tests for ChainedSkillRegistry backward compatibility."""

    @pytest.fixture
    def legacy_project(self, tmp_path):
        """Create a legacy project structure."""
        project_skills = tmp_path / ".claude" / "skills"
        shared_skills = tmp_path / "shared" / "skills"

        # Create project skill
        proj_skill = project_skills / "project-skill"
        proj_skill.mkdir(parents=True)
        (proj_skill / "SKILL.md").write_text("""---
name: project-skill
description: Project skill
---
# Project skill
""")

        # Create shared skill
        shared_skill = shared_skills / "shared-skill"
        shared_skill.mkdir(parents=True)
        (shared_skill / "SKILL.md").write_text("""---
name: shared-skill
description: Shared skill
---
# Shared skill
""")

        return project_skills, shared_skills

    def test_legacy_mode(self, legacy_project):
        """Test legacy initialization still works."""
        project_skills, shared_skills = legacy_project

        registry = ChainedSkillRegistry(
            project_skills_dir=project_skills,
            shared_skills_dir=shared_skills,
            use_shared=True,
        )

        assert registry.exists("project-skill")
        assert registry.exists("shared-skill")

    def test_legacy_mode_no_shared(self, legacy_project):
        """Test legacy mode with shared skills disabled."""
        project_skills, shared_skills = legacy_project

        registry = ChainedSkillRegistry(
            project_skills_dir=project_skills,
            shared_skills_dir=shared_skills,
            use_shared=False,
        )

        assert registry.exists("project-skill")
        assert not registry.exists("shared-skill")

    def test_legacy_source_labels(self, legacy_project):
        """Test that legacy mode uses correct source labels."""
        project_skills, shared_skills = legacy_project

        registry = ChainedSkillRegistry(
            project_skills_dir=project_skills,
            shared_skills_dir=shared_skills,
            use_shared=True,
        )

        assert registry.get_source("project-skill") == "project"
        assert registry.get_source("shared-skill") == "shared"


class TestChainedSkillRegistryCommon:
    """Common tests for ChainedSkillRegistry."""

    @pytest.fixture
    def simple_registry(self, tmp_path):
        """Create a simple registry with one skill."""
        project_dir = tmp_path / "project"
        skills_dir = project_dir / ".claude" / "skills"
        skill_dir = skills_dir / "test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("""---
name: test-skill
description: Test skill
---
# Test
""")

        return ChainedSkillRegistry(
            project_dir=project_dir,
            platforms=[Platform.CLAUDE],
            include_global=False,
        )

    def test_get_raises_on_not_found(self, simple_registry):
        """Test that get() raises SkillNotFoundError."""
        with pytest.raises(SkillNotFoundError):
            simple_registry.get("nonexistent")

    def test_get_optional_returns_none(self, simple_registry):
        """Test that get_optional() returns None for missing skill."""
        result = simple_registry.get_optional("nonexistent")
        assert result is None

    def test_exists(self, simple_registry):
        """Test exists() method."""
        assert simple_registry.exists("test-skill")
        assert not simple_registry.exists("nonexistent")

    def test_len(self, simple_registry):
        """Test __len__ returns skill count."""
        assert len(simple_registry) == 1

    def test_iter(self, simple_registry):
        """Test __iter__ allows iteration."""
        skills = list(simple_registry)
        assert len(skills) == 1
        assert skills[0].name == "test-skill"

    def test_reload(self, tmp_path):
        """Test reload picks up new skills."""
        project_dir = tmp_path / "project"
        skills_dir = project_dir / ".claude" / "skills"
        skill_dir = skills_dir / "initial-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("""---
name: initial-skill
description: Initial
---
# Initial
""")

        registry = ChainedSkillRegistry(
            project_dir=project_dir,
            platforms=[Platform.CLAUDE],
            include_global=False,
        )

        assert len(registry) == 1

        # Add new skill
        new_skill = skills_dir / "new-skill"
        new_skill.mkdir(parents=True)
        (new_skill / "SKILL.md").write_text("""---
name: new-skill
description: New
---
# New
""")

        registry.reload()
        assert len(registry) == 2
        assert registry.exists("new-skill")
