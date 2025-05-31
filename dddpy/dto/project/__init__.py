"""DTOs for Project use cases."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from dddpy.dto.todo import TodoOutputDto


@dataclass
class ProjectCreateDto:
    """DTO for creating a new Project."""

    name: str
    description: str | None = None


@dataclass
class ProjectUpdateDto:
    """DTO for updating an existing Project."""

    name: str | None = None
    description: str | None = None


@dataclass
class ProjectOutputDto:
    """DTO for Project output."""

    id: str
    name: str
    description: str | None
    todos: list[TodoOutputDto]
    created_at: datetime
    updated_at: datetime


@dataclass
class AddTodoToProjectDto:
    """DTO for adding a Todo to a Project."""

    title: str
    description: str | None = None
    dependencies: list[str] | None = None


__all__ = [
    'ProjectCreateDto',
    'ProjectUpdateDto',
    'ProjectOutputDto',
    'AddTodoToProjectDto',
]
