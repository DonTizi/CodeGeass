"""Tests for factory layer."""

from pathlib import Path
import pytest

from codegeass.core.entities import Skill, Template
from codegeass.core.exceptions import SkillNotFoundError, TemplateNotFoundError, ValidationError
from codegeass.factory.registry import SkillRegistry, TemplateRegistry
from codegeass.factory.task_builder import TaskBuilder
from codegeass.factory.task_factory import TaskFactory


class TestSkillRegistry:
    """Tests for SkillRegistry."""

    @pytest.fixture
    def skills_dir(self, tmp_path):
        """Create a temporary skills directory with test skills."""
        skills_dir = tmp_path / ".claude" / "skills"

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

        # Create another skill
        skill2_dir = skills_dir / "another-skill"
        skill2_dir.mkdir(parents=True)
        (skill2_dir / "SKILL.md").write_text("""---
name: another-skill
description: Another test skill
---

# Another Skill

Do something with $ARGUMENTS.
""")

        return skills_dir

    def test_loads_skills_from_directory(self, skills_dir):
        SkillRegistry.reset_instance()
        registry = SkillRegistry(skills_dir)
        skills = registry.get_all()

        assert len(skills) == 2
        assert registry.exists("test-skill")
        assert registry.exists("another-skill")

    def test_get_skill(self, skills_dir):
        SkillRegistry.reset_instance()
        registry = SkillRegistry(skills_dir)
        skill = registry.get("test-skill")

        assert skill.name == "test-skill"
        assert skill.description == "A test skill"
        assert "Read" in skill.allowed_tools

    def test_get_nonexistent_raises(self, skills_dir):
        SkillRegistry.reset_instance()
        registry = SkillRegistry(skills_dir)

        with pytest.raises(SkillNotFoundError):
            registry.get("nonexistent")

    def test_reload(self, skills_dir):
        SkillRegistry.reset_instance()
        registry = SkillRegistry(skills_dir)
        initial_count = len(registry.get_all())

        # Add a new skill
        new_skill_dir = skills_dir / "new-skill"
        new_skill_dir.mkdir()
        (new_skill_dir / "SKILL.md").write_text("""---
name: new-skill
description: New skill
---

# New Skill
""")

        registry.reload()
        assert len(registry.get_all()) == initial_count + 1


class TestTemplateRegistry:
    """Tests for TemplateRegistry."""

    def test_register_and_get(self):
        TemplateRegistry.reset_instance()
        registry = TemplateRegistry()

        template = Template(
            name="test-template",
            description="Test template",
            default_skills=["code-review"],
        )
        registry.register(template)

        retrieved = registry.get("test-template")
        assert retrieved.name == "test-template"
        assert retrieved.default_skills == ["code-review"]

    def test_get_nonexistent_raises(self):
        TemplateRegistry.reset_instance()
        registry = TemplateRegistry()

        with pytest.raises(TemplateNotFoundError):
            registry.get("nonexistent")

    def test_register_from_dict(self):
        TemplateRegistry.reset_instance()
        registry = TemplateRegistry()

        data = {
            "name": "from-dict",
            "description": "Created from dict",
            "model": "opus",
        }
        template = registry.register_from_dict(data)

        assert template.name == "from-dict"
        assert template.model == "opus"
        assert registry.exists("from-dict")


class TestTaskBuilder:
    """Tests for TaskBuilder."""

    def test_build_with_skill(self, tmp_path):
        task = (
            TaskBuilder()
            .with_name("test-task")
            .with_schedule("0 9 * * *")
            .with_working_dir(tmp_path)
            .with_skill("code-review")
            .build()
        )

        assert task.name == "test-task"
        assert task.schedule == "0 9 * * *"
        assert task.skill == "code-review"

    def test_build_with_prompt(self, tmp_path):
        task = (
            TaskBuilder()
            .with_name("test-task")
            .with_schedule("0 9 * * *")
            .with_working_dir(tmp_path)
            .with_prompt("Run tests")
            .build()
        )

        assert task.prompt == "Run tests"
        assert task.skill is None

    def test_build_with_all_options(self, tmp_path):
        task = (
            TaskBuilder()
            .with_name("full-task")
            .with_schedule("0 9 * * 1-5")
            .with_working_dir(tmp_path)
            .with_skill("code-review")
            .with_model("opus")
            .with_autonomous()
            .with_timeout(600)
            .with_max_turns(10)
            .with_tools(["Read", "Grep"])
            .with_variable("focus", "security")
            .build()
        )

        assert task.model == "opus"
        assert task.autonomous is True
        assert task.timeout == 600
        assert task.max_turns == 10
        assert "Read" in task.allowed_tools
        assert task.variables["focus"] == "security"

    def test_build_without_required_raises(self, tmp_path):
        with pytest.raises(ValidationError):
            TaskBuilder().with_name("incomplete").build()

    def test_validate_returns_errors(self, tmp_path):
        builder = TaskBuilder()
        errors = builder.validate()

        assert "name is required" in errors
        assert "schedule is required" in errors
        assert "working_dir is required" in errors

    def test_reset(self, tmp_path):
        builder = (
            TaskBuilder()
            .with_name("test")
            .with_schedule("0 9 * * *")
            .reset()
        )

        assert builder._name is None
        assert builder._schedule is None


class TestTaskFactory:
    """Tests for TaskFactory."""

    @pytest.fixture
    def factory(self, tmp_path):
        """Create factory with test registries."""
        # Create skills
        skills_dir = tmp_path / ".claude" / "skills"
        skill_dir = skills_dir / "test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("""---
name: test-skill
description: Test skill
allowed-tools: Read, Grep
---

# Test Skill
""")

        SkillRegistry.reset_instance()
        skill_registry = SkillRegistry(skills_dir)

        TemplateRegistry.reset_instance()
        template_registry = TemplateRegistry()
        template_registry.register(Template(
            name="test-template",
            description="Test template",
            prompt_template="Review {{ project }}",
            default_tools=["Read"],
            model="sonnet",
        ))

        return TaskFactory(skill_registry, template_registry)

    def test_create_from_skill(self, factory, tmp_path):
        task = factory.create_from_skill(
            name="skill-task",
            skill_name="test-skill",
            schedule="0 9 * * *",
            working_dir=tmp_path,
        )

        assert task.skill == "test-skill"
        assert "Read" in task.allowed_tools

    def test_create_from_skill_not_found(self, factory, tmp_path):
        with pytest.raises(SkillNotFoundError):
            factory.create_from_skill(
                name="skill-task",
                skill_name="nonexistent",
                schedule="0 9 * * *",
                working_dir=tmp_path,
            )

    def test_create_from_prompt(self, factory, tmp_path):
        task = factory.create_from_prompt(
            name="prompt-task",
            prompt="Do something",
            schedule="0 9 * * *",
            working_dir=tmp_path,
            model="opus",
        )

        assert task.prompt == "Do something"
        assert task.model == "opus"
