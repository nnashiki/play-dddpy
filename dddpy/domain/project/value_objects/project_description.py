"""Value objects for Project description."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ProjectDescription:
    """Value object representing the description of a Project"""

    value: Optional[str]

    def __post_init__(self):
        if self.value is not None and len(self.value) > 1000:
            raise ValueError('Project description must be 1000 characters or less')

    def __str__(self) -> str:
        return self.value or ''
