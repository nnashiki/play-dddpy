"""DTOs for Project use cases."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Union

from dddpy.dto.todo import TodoOutputDto


@dataclass
class ProjectCreateDto:
    """DTO for creating a new Project."""

    name: str
    description: Union[str, None] = None


@dataclass
class ProjectUpdateDto:
    """DTO for updating an existing Project."""

    name: Union[str, None] = None
    description: Union[str, None] = None


@dataclass
class ProjectOutputDto:
    """DTO for Project output."""

    id: str
    name: str
    description: Union[str, None]
    todos: list[TodoOutputDto]
    created_at: datetime
    updated_at: datetime


@dataclass
class AddTodoToProjectDto:
    """DTO for adding a Todo to a Project."""

    title: str
    description: Union[str, None] = None
    dependencies: Union[list[str], None] = None


__all__ = [
    'ProjectCreateDto',
    'ProjectUpdateDto',
    'ProjectOutputDto',
    'AddTodoToProjectDto',
]
