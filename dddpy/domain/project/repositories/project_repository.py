"""Repository interface for Project entities."""

from abc import ABC, abstractmethod

from dddpy.domain.project.entities import Project
from dddpy.domain.project.value_objects import ProjectId


class ProjectRepository(ABC):
    """Interface for Project repository"""

    @abstractmethod
    def save(self, project: Project) -> None:
        """Save a Project"""

    @abstractmethod
    def find_by_id(self, project_id: ProjectId) -> Project | None:
        """Find a Project by ID"""

    @abstractmethod
    def find_all(self, limit: int | None = None) -> list[Project]:
        """Get all Projects with optional limit"""

    @abstractmethod
    def delete(self, project_id: ProjectId) -> None:
        """Delete a Project by ID"""
