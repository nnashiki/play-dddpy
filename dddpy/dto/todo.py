"""DTOs for Todo use cases."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class TodoCreateDto:
    """DTO for creating a new Todo."""

    title: str
    description: str | None = None
    dependencies: list[str] | None = None


@dataclass
class TodoUpdateDto:
    """DTO for updating an existing Todo."""

    title: str | None = None
    description: str | None = None
    dependencies: list[str] | None = None


@dataclass
class TodoOutputDto:
    """DTO for Todo output."""

    id: str
    title: str
    description: str | None
    status: str
    dependencies: list[str]
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


@dataclass
class SetDependenciesDto:
    """DTO for setting dependencies."""

    dependencies: list[str]


__all__ = [
    'TodoCreateDto',
    'TodoUpdateDto',
    'TodoOutputDto',
    'SetDependenciesDto',
]
