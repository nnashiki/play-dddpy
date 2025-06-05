"""DTOs for Todo use cases."""

from dataclasses import dataclass
from datetime import datetime
from typing import Union


@dataclass
class TodoCreateDto:
    """DTO for creating a new Todo."""

    title: str
    description: Union[str, None] = None
    dependencies: Union[list[str], None] = None


@dataclass
class TodoUpdateDto:
    """DTO for updating an existing Todo."""

    title: Union[str, None] = None
    description: Union[str, None] = None
    dependencies: Union[list[str], None] = None


@dataclass
class TodoOutputDto:
    """DTO for Todo output."""

    id: str
    title: str
    description: Union[str, None]
    status: str
    dependencies: list[str]
    project_id: str
    created_at: datetime
    updated_at: datetime
    completed_at: Union[datetime, None]


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
