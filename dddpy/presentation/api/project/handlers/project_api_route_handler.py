"""Controller for handling Project-related HTTP requests."""

from uuid import UUID

from fastapi import Depends, FastAPI, status

from dddpy.dto.project import AddTodoToProjectDto, ProjectCreateDto
from dddpy.infrastructure.di.injection import (
    get_add_todo_to_project_usecase,
    get_create_project_usecase,
    get_delete_project_usecase,
    get_find_projects_usecase,
)
from dddpy.presentation.api.project.schemas import (
    AddTodoToProjectSchema,
    ProjectCreateSchema,
    ProjectSchema,
)
from dddpy.presentation.assembler.project_assembler import ProjectAssembler
from dddpy.usecase.project import (
    AddTodoToProjectUseCase,
    CreateProjectUseCase,
    FindProjectsUseCase,
)

from dddpy.usecase.project.delete_project_usecase import DeleteProjectUseCase


class ProjectApiRouteHandler:
    """Handler class for handling Project-related HTTP endpoints."""

    def register_routes(self, app: FastAPI):
        """Register Project-related routes to the FastAPI application."""

        @app.get(
            '/projects',
            response_model=list[ProjectSchema],
            status_code=200,
        )
        def get_projects(
            usecase: FindProjectsUseCase = Depends(get_find_projects_usecase),
        ):
            project_outputs = usecase.execute()
            return [ProjectAssembler.to_schema(project) for project in project_outputs]

        @app.delete('/projects/{project_id}', status_code=204)
        def delete_project(
            project_id: UUID,
            usecase: DeleteProjectUseCase = Depends(get_delete_project_usecase),
        ):
            usecase.execute(str(project_id))

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

            project_output = usecase.execute(dto)
            return ProjectAssembler.to_schema(project_output)



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

            todo_output = usecase.execute(str(project_id), dto)
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
