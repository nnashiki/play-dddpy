"""DTOs for Todo use cases."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class TodoCreateDto:
    """DTO for creating a new Todo."""

    title: str
    description: Optional[str] = None
    dependencies: Optional[List[str]] = None


@dataclass
class TodoUpdateDto:
    """DTO for updating an existing Todo."""

    title: Optional[str] = None
    description: Optional[str] = None
    dependencies: Optional[List[str]] = None


@dataclass
class TodoOutputDto:
    """DTO for Todo output."""

    id: str
    title: str
    description: Optional[str]
    status: str
    dependencies: List[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]


@dataclass
class SetDependenciesDto:
    """DTO for setting dependencies."""

    dependencies: List[str]


__all__ = [
    'TodoCreateDto',
    'TodoUpdateDto',
    'TodoOutputDto',
    'SetDependenciesDto',
]
