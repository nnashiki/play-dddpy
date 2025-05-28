"""Value objects for Project name."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectName:
    """Value object representing the name of a Project"""

    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError('Project name is required')
        if len(self.value) > 100:
            raise ValueError('Project name must be 100 characters or less')

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ProjectName):
            return self.value == other.value
        return False
