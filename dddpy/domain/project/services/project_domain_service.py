"""Domain service for Project entity business logic."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dddpy.domain.project.repositories import ProjectRepository
    from dddpy.domain.project.entities import Project

__all__ = ['ProjectDomainService']


class ProjectDomainService:
    """Domain service for Project-related operations that span multiple Projects."""
    
    @staticmethod
    def validate_project_name_uniqueness(
        project_name: str, project_repository: 'ProjectRepository'
    ) -> bool:
        """Check if project name is unique across all projects."""
        # This is a placeholder for future cross-project validation
        # For now, we allow duplicate names as it's not a strict requirement
        return True
    
    @staticmethod
    def can_delete_project(project: 'Project') -> bool:
        """Check if a project can be deleted."""
        # For now, any project can be deleted
        # Future requirements might include checking for dependencies
        return True
