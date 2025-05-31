"""Domain service for Project entity business logic."""

from typing import TYPE_CHECKING

from dddpy.domain.project.value_objects import ProjectName

if TYPE_CHECKING:
    from dddpy.domain.project.entities import Project
    from dddpy.domain.project.repositories import ProjectRepository

__all__ = ['ProjectDomainService']


class ProjectDomainService:
    """ドメインサービス:Projectを横断するビジネスロジックを定義"""

    @staticmethod
    def is_project_name_unique(
        name: ProjectName, repository: 'ProjectRepository'
    ) -> bool:
        """既存のプロジェクト名と重複しないか検証する"""
        existing_projects = repository.find_all()
        return all(p.name != name for p in existing_projects)

    @staticmethod
    def can_delete_project(project: 'Project') -> bool:
        """Check if a project can be deleted."""
        # For now, any project can be deleted
        # Future requirements might include checking for dependencies
        return True
