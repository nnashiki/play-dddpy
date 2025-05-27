"""HTTP routes for Project operations (Project aggregate centric)."""

from typing import List
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status

from dddpy.dto.project import ProjectCreateDto, AddTodoToProjectDto
from dddpy.domain.project.exceptions import (
    ProjectNotFoundError,
    ProjectDeletionNotAllowedError,
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
    DeleteProjectUseCase,
)


class ProjectApiRouteHandler:
    """Registers Project-related endpoints."""

    def register_routes(self, app: FastAPI) -> None:  # noqa: D401
        # ------------------------------------------------------------------ #
        #  GET /projects – list                                               #
        # ------------------------------------------------------------------ #
        @app.get('/projects', response_model=List[ProjectSchema], status_code=200)
        def list_projects(                           # pylint: disable=unused-variable
            usecase: FindProjectsUseCase = Depends(get_find_projects_usecase),
        ):
            try:
                project_outputs = usecase.execute()
                return [ProjectSchema.from_dto(p) for p in project_outputs]
            except Exception as exc:                 # pragma: no cover
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                ) from exc

        
        # ------------------------------------------------------------------ #
        #  POST /projects – create                                            #
        # ------------------------------------------------------------------ #
        @app.post('/projects', response_model=ProjectSchema, status_code=201)
        def create_project(                          # pylint: disable=unused-variable
            data: ProjectCreateSchema,
            usecase: CreateProjectUseCase = Depends(get_create_project_usecase),
        ):
            dto = ProjectCreateDto(name=data.name, description=data.description)
            try:
                output = usecase.execute(dto)
                return ProjectSchema.from_dto(output)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(exc),
                ) from exc
            except Exception as exc:                 # pragma: no cover
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                ) from exc

        # ------------------------------------------------------------------ #
        #  DELETE /projects/{project_id} – delete                             #
        # ------------------------------------------------------------------ #
        @app.delete(
            '/projects/{project_id}',
            status_code=204,
            responses={
                status.HTTP_404_NOT_FOUND: {'description': 'Project not found'},
                status.HTTP_400_BAD_REQUEST: {'description': 'Cannot delete project'},
            },
        )
        def delete_project(                          # pylint: disable=unused-variable
            project_id: UUID,
            usecase: DeleteProjectUseCase = Depends(get_delete_project_usecase),
        ):
            try:
                usecase.execute(str(project_id))
            except ProjectNotFoundError as exc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=exc.message,
                ) from exc
            except ProjectDeletionNotAllowedError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=exc.message,
                ) from exc
            except Exception as exc:                 # pragma: no cover
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                ) from exc

        # ------------------------------------------------------------------ #
        #  POST /projects/{project_id}/todos – add Todo                       #
        # ------------------------------------------------------------------ #
        @app.post(
            '/projects/{project_id}/todos',
            response_model=dict,      # → TodoSchema 相当（inline JSON）
            status_code=201,
            responses={
                status.HTTP_404_NOT_FOUND: {'description': 'Project not found'},
                status.HTTP_400_BAD_REQUEST: {
                    'description': 'Invalid or circular dependencies',
                },
            },
        )
        def add_todo(                                 # pylint: disable=unused-variable
            project_id: UUID,
            data: AddTodoToProjectSchema,
            usecase: AddTodoToProjectUseCase = Depends(get_add_todo_to_project_usecase),
        ):
            dto = AddTodoToProjectDto(
                title=data.title,
                description=data.description,
                dependencies=data.dependencies,
            )
            try:
                todo_output = usecase.execute(str(project_id), dto)
                # inline JSON response (keeps ProjectSchema simple)
                return {
                    'id': todo_output.id,
                    'title': todo_output.title,
                    'description': todo_output.description,
                    'status': todo_output.status,
                    'dependencies': todo_output.dependencies,
                    'created_at': int(todo_output.created_at.timestamp() * 1000),
                    'updated_at': int(todo_output.updated_at.timestamp() * 1000),
                    'completed_at': int(todo_output.completed_at.timestamp() * 1000)
                    if todo_output.completed_at
                    else None,
                }
            except ProjectNotFoundError as exc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=exc.message,
                ) from exc
            except (TodoDependencyNotFoundError, TodoCircularDependencyError) as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(exc),
                ) from exc
            except Exception as exc:                  # pragma: no cover
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                ) from exc