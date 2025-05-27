"""Controller for handling Project-related HTTP requests."""

from typing import List
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status

from dddpy.dto.project import ProjectCreateDto, AddTodoToProjectDto
from dddpy.domain.project.exceptions import (
    ProjectNotFoundError,
    ProjectDeletionNotAllowedError,
    TodoRemovalNotAllowedError,
)
from dddpy.domain.todo.exceptions import (
    TodoCircularDependencyError,
    TodoDependencyNotFoundError,
)
from dddpy.infrastructure.di.injection import (
    get_create_project_usecase,
    get_add_todo_to_project_usecase,
    get_find_projects_usecase,
    get_delete_project_usecase,
)
from dddpy.presentation.api.project.schemas import (
    ProjectCreateSchema,
    ProjectSchema,
    AddTodoToProjectSchema,
)
from dddpy.usecase.project import (
    CreateProjectUseCase,
    AddTodoToProjectUseCase,
    FindProjectsUseCase,
)
from dddpy.usecase.project.delete_project_usecase import DeleteProjectUseCase


class ProjectApiRouteHandler:
    """Handler class for handling Project-related HTTP endpoints."""

    def register_routes(self, app: FastAPI):
        """Register Project-related routes to the FastAPI application."""

        @app.get(
            '/projects',
            response_model=List[ProjectSchema],
            status_code=200,
        )
        def get_projects(
            usecase: FindProjectsUseCase = Depends(get_find_projects_usecase),
        ):
            try:
                project_outputs = usecase.execute()
                return [ProjectSchema.from_dto(project) for project in project_outputs]
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                ) from e

        @app.delete('/projects/{project_id}', status_code=204)
        def delete_project(
            project_id: UUID,
            usecase: DeleteProjectUseCase = Depends(get_delete_project_usecase),
        ):
            try:
                usecase.execute(str(project_id))
            except ProjectNotFoundError as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=e.message,
                ) from e
            except ProjectDeletionNotAllowedError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=e.message,
                ) from e
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                ) from e

        @app.post(
            '/projects',
            response_model=ProjectSchema,
            status_code=201,
        )
        def create_project(
            data: ProjectCreateSchema,
            usecase: CreateProjectUseCase = Depends(get_create_project_usecase),
        ):
            # Convert request schema to DTO
            dto = ProjectCreateDto(
                name=data.name,
                description=data.description,
            )

            try:
                project_output = usecase.execute(dto)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e),
                ) from e
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                ) from e

            return ProjectSchema.from_dto(project_output)

        @app.post(
            '/projects/{project_id}/todos',
            response_model=dict,  # Todo schema
            status_code=201,
            responses={
                status.HTTP_404_NOT_FOUND: {
                    'description': 'Project not found',
                },
                status.HTTP_400_BAD_REQUEST: {
                    'description': 'Invalid dependencies or circular dependency',
                },
            },
        )
        def add_todo_to_project(
            project_id: UUID,
            data: AddTodoToProjectSchema,
            usecase: AddTodoToProjectUseCase = Depends(get_add_todo_to_project_usecase),
        ):
            # Convert request schema to DTO
            dto = AddTodoToProjectDto(
                title=data.title,
                description=data.description,
                dependencies=data.dependencies,
            )

            try:
                todo_output = usecase.execute(str(project_id), dto)
                return {
                    'id': todo_output.id,
                    'title': todo_output.title,
                    'description': todo_output.description,
                    'status': todo_output.status,
                    'dependencies': todo_output.dependencies,
                    'created_at': int(todo_output.created_at.timestamp() * 1000),
                    'updated_at': int(todo_output.updated_at.timestamp() * 1000),
                    'completed_at': int(todo_output.completed_at.timestamp() * 1000) if todo_output.completed_at else None,
                }
            except ProjectNotFoundError as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=e.message,
                ) from e
            except (TodoDependencyNotFoundError, TodoCircularDependencyError) as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e),
                ) from e
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                ) from e
