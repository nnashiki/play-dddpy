"""Value objects for Project identifier."""

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ProjectId:
    """Value object representing the identifier of a Project"""

    value: UUID

    @staticmethod
    def generate() -> 'ProjectId':
        """Generate a new ID"""
        return ProjectId(uuid4())

    def __str__(self) -> str:
        return str(self.value)

    def __hash__(self) -> int:
        return hash(self.value)
