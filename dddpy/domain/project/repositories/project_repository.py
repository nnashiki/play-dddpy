"""Repository interface for Project entities."""

from abc import ABC, abstractmethod
from typing import List, Optional

from dddpy.domain.project.entities import Project
from dddpy.domain.project.value_objects import ProjectId
from dddpy.domain.todo.value_objects import TodoId


class ProjectRepository(ABC):
    """Interface for Project repository"""

    @abstractmethod
    def save(self, project: Project) -> None:
        """Save a Project"""

    @abstractmethod
    def find_by_id(self, project_id: ProjectId) -> Optional[Project]:
        """Find a Project by ID"""

    @abstractmethod
    def find_all(self, limit: Optional[int] = None) -> List[Project]:
        """Get all Projects with optional limit"""

    @abstractmethod
    def delete(self, project_id: ProjectId) -> None:
        """Delete a Project by ID"""

    @abstractmethod
    def find_project_by_todo_id(self, todo_id: TodoId) -> Optional[Project]:
        """Find a Project that contains the specified Todo.
        
        .. deprecated:: 2.0.0
            This method violates DDD aggregate boundaries. 
            Use find_by_id(project_id) instead and access todos through the Project aggregate.
        """
