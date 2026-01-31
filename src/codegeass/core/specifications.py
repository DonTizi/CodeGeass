"""Specification pattern for composable, testable filters."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from codegeass.core.entities import Task

T = TypeVar("T")


class Specification(ABC, Generic[T]):
    """Base specification for composable filters."""

    @abstractmethod
    def is_satisfied_by(self, entity: T) -> bool:
        """Check if entity satisfies this specification."""

    def __and__(self, other: "Specification[T]") -> "AndSpecification[T]":
        """Combine with AND logic."""
        return AndSpecification(self, other)

    def __or__(self, other: "Specification[T]") -> "OrSpecification[T]":
        """Combine with OR logic."""
        return OrSpecification(self, other)

    def __invert__(self) -> "NotSpecification[T]":
        """Negate this specification."""
        return NotSpecification(self)


class AndSpecification(Specification[T]):
    """Composite specification that requires all specs to be satisfied."""

    def __init__(self, *specs: Specification[T]) -> None:
        self.specs = specs

    def is_satisfied_by(self, entity: T) -> bool:
        return all(spec.is_satisfied_by(entity) for spec in self.specs)


class OrSpecification(Specification[T]):
    """Composite specification that requires any spec to be satisfied."""

    def __init__(self, *specs: Specification[T]) -> None:
        self.specs = specs

    def is_satisfied_by(self, entity: T) -> bool:
        return any(spec.is_satisfied_by(entity) for spec in self.specs)


class NotSpecification(Specification[T]):
    """Specification that negates another specification."""

    def __init__(self, spec: Specification[T]) -> None:
        self.spec = spec

    def is_satisfied_by(self, entity: T) -> bool:
        return not self.spec.is_satisfied_by(entity)


class AlwaysTrueSpec(Specification[T]):
    """Specification that always returns True (identity for AND)."""

    def is_satisfied_by(self, entity: T) -> bool:
        return True


# Task-specific specifications


class NameContainsSpec(Specification["Task"]):
    """Check if task name contains a substring (case-insensitive)."""

    def __init__(self, substring: str) -> None:
        self.substring = substring.lower()

    def is_satisfied_by(self, entity: "Task") -> bool:
        return self.substring in entity.name.lower()


class HasTagSpec(Specification["Task"]):
    """Check if task has a specific tag."""

    def __init__(self, tag: str) -> None:
        self.tag = tag.lower()

    def is_satisfied_by(self, entity: "Task") -> bool:
        return any(t.lower() == self.tag for t in entity.tags)


class HasAnyTagSpec(Specification["Task"]):
    """Check if task has any of the specified tags."""

    def __init__(self, tags: list[str]) -> None:
        self.tags = [t.lower() for t in tags]

    def is_satisfied_by(self, entity: "Task") -> bool:
        entity_tags = [t.lower() for t in entity.tags]
        return any(t in entity_tags for t in self.tags)


class HasAllTagsSpec(Specification["Task"]):
    """Check if task has all of the specified tags."""

    def __init__(self, tags: list[str]) -> None:
        self.tags = [t.lower() for t in tags]

    def is_satisfied_by(self, entity: "Task") -> bool:
        entity_tags = [t.lower() for t in entity.tags]
        return all(t in entity_tags for t in self.tags)


class EnabledSpec(Specification["Task"]):
    """Check if task is enabled or disabled."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled

    def is_satisfied_by(self, entity: "Task") -> bool:
        return entity.enabled == self.enabled


class ModelSpec(Specification["Task"]):
    """Check if task uses a specific model."""

    def __init__(self, model: str) -> None:
        self.model = model.lower()

    def is_satisfied_by(self, entity: "Task") -> bool:
        return entity.model.lower() == self.model


class StatusSpec(Specification["Task"]):
    """Check if task has a specific last_status."""

    def __init__(self, status: str) -> None:
        self.status = status.lower()

    def is_satisfied_by(self, entity: "Task") -> bool:
        if entity.last_status is None:
            return self.status == "never_run"
        return entity.last_status.lower() == self.status


class TextSearchSpec(Specification["Task"]):
    """Full-text search across name, prompt, and skill fields."""

    def __init__(self, query: str) -> None:
        self.query = query.lower()

    def is_satisfied_by(self, entity: "Task") -> bool:
        # Search in name
        if self.query in entity.name.lower():
            return True

        # Search in prompt
        if entity.prompt and self.query in entity.prompt.lower():
            return True

        # Search in skill name
        if entity.skill and self.query in entity.skill.lower():
            return True

        # Search in tags
        if any(self.query in tag.lower() for tag in entity.tags):
            return True

        return False


class PromptContainsSpec(Specification["Task"]):
    """Check if task prompt contains a substring."""

    def __init__(self, substring: str) -> None:
        self.substring = substring.lower()

    def is_satisfied_by(self, entity: "Task") -> bool:
        if entity.prompt is None:
            return False
        return self.substring in entity.prompt.lower()


class SkillSpec(Specification["Task"]):
    """Check if task uses a specific skill."""

    def __init__(self, skill: str) -> None:
        self.skill = skill.lower()

    def is_satisfied_by(self, entity: "Task") -> bool:
        if entity.skill is None:
            return False
        return entity.skill.lower() == self.skill
