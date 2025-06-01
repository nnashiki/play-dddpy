"""This module provides use case for updating a Todo through Project aggregate."""

from abc import ABC, abstractmethod
from uuid import UUID

from dddpy.domain.project.exceptions import ProjectNotFoundError
from dddpy.domain.project.repositories import ProjectRepository
from dddpy.domain.todo.value_objects import (
    TodoDescription,
    TodoId,
    TodoTitle,
)
from dddpy.dto.todo import TodoOutputDto, TodoUpdateDto
from dddpy.usecase.converter.todo_converter import TodoConverter


class UpdateTodoThroughProjectUseCase(ABC):
    """UpdateTodoThroughProjectUseCase defines an interface for updating a Todo through Project."""

    @abstractmethod
    def execute(
        self, project_id: str, todo_id: str, dto: TodoUpdateDto
    ) -> TodoOutputDto:
        """execute updates a Todo through Project aggregate."""


class UpdateTodoThroughProjectUseCaseImpl(UpdateTodoThroughProjectUseCase):
    """UpdateTodoThroughProjectUseCaseImpl implements the use case for updating a Todo through Project."""

    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository

    def execute(
        self, project_id: str, todo_id: str, dto: TodoUpdateDto
    ) -> TodoOutputDto:
        """execute updates a Todo through Project aggregate."""
        from dddpy.domain.project.value_objects import ProjectId

        _project_id = ProjectId(UUID(project_id))
        _todo_id = TodoId(UUID(todo_id))

        # Find the project by ID
        project = self.project_repository.find_by_id(_project_id)

        if project is None:
            raise ProjectNotFoundError()

        # Convert DTO to domain objects
        title = TodoTitle(dto.title) if dto.title is not None else None
        description = (
            TodoDescription(dto.description) if dto.description is not None else None
        )
        dependencies = (
            [TodoId(UUID(dep_id)) for dep_id in dto.dependencies]
            if dto.dependencies is not None
            else None
        )

        # Update todo through project
        updated_todo = project.update_todo_by_id(
            _todo_id, title, description, dependencies
        )

        # Save project with updated todo
        self.project_repository.save(project)

        # Convert to output DTO using Converter (Application 層)
        return TodoConverter.to_output_dto(updated_todo)


def new_update_todo_through_project_usecase(
    project_repository: ProjectRepository,
) -> UpdateTodoThroughProjectUseCase:
    """Create a new instance of UpdateTodoThroughProjectUseCase."""
    return UpdateTodoThroughProjectUseCaseImpl(project_repository)
