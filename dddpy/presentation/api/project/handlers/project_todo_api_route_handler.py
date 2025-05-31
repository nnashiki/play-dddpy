"""Project Todo API route handler integrating Todo operations within Project context."""

from typing import List
from uuid import UUID

from fastapi import Depends, FastAPI, status

from dddpy.dto.todo import TodoUpdateDto
from dddpy.infrastructure.di.injection import (
    get_start_todo_usecase,
    get_complete_todo_usecase,
    get_update_todo_usecase,
    get_find_todo_usecase,
    get_find_projects_usecase,
)
from dddpy.presentation.api.project.schemas.project_todo_error_schemas import (
    ErrorMessageTodoNotFound,
    TodoDependencyNotCompletedErrorMessage,
)
from dddpy.presentation.api.error_schemas import ErrorMessageProjectNotFound
from dddpy.presentation.api.project.schemas.project_todo_schema import (
    ProjectTodoSchema,
    ProjectTodoUpdateSchema,
)
from dddpy.usecase.project import (
    StartTodoThroughProjectUseCase,
    CompleteTodoThroughProjectUseCase,
    UpdateTodoThroughProjectUseCase,
    FindProjectsUseCase,
)
from dddpy.usecase.todo.find_todo_usecase import FindTodoThroughProjectUseCase


class ProjectTodoApiRouteHandler:
    """Registers Project Todo-related endpoints with proper aggregate boundaries."""

    def register_routes(self, app: FastAPI) -> None:  # noqa: D401
        """Register all Project Todo routes."""

        # ------------------------------------------------------------------ #
        #  GET /projects/{project_id}/todos  – list todos in project         #
        # ------------------------------------------------------------------ #
        @app.get(
            '/projects/{project_id}/todos',
            response_model=List[ProjectTodoSchema],
            status_code=200,
            responses={
                status.HTTP_404_NOT_FOUND: {'model': ErrorMessageProjectNotFound}
            },
        )
        def get_project_todos(  # pylint: disable=unused-variable
            project_id: UUID,
            usecase: FindProjectsUseCase = Depends(get_find_projects_usecase),
        ):
            # Find the specific project
            from dddpy.domain.project.value_objects import ProjectId
            from dddpy.domain.project.exceptions import ProjectNotFoundError

            _project_id = ProjectId(project_id)
            project_outputs = usecase.execute()

            # Filter to find the specific project
            target_project = None
            for project in project_outputs:
                if project.id == str(project_id):
                    target_project = project
                    break

            if target_project is None:
                raise ProjectNotFoundError()

            return [
                ProjectTodoSchema.from_dto(todo, str(project_id))
                for todo in target_project.todos
            ]

        # ------------------------------------------------------------------ #
        #  GET /projects/{project_id}/todos/{todo_id} – get specific todo     #
        # ------------------------------------------------------------------ #
        @app.get(
            '/projects/{project_id}/todos/{todo_id}',
            response_model=ProjectTodoSchema,
            status_code=200,
            responses={
                status.HTTP_404_NOT_FOUND: {'model': ErrorMessageTodoNotFound},
            },
        )
        def get_project_todo(  # pylint: disable=unused-variable
            project_id: UUID,
            todo_id: UUID,
            usecase: FindTodoThroughProjectUseCase = Depends(get_find_todo_usecase),
        ):
            output = usecase.execute(str(project_id), str(todo_id))
            return ProjectTodoSchema.from_dto(output, str(project_id))

        # ------------------------------------------------------------------ #
        #  PUT /projects/{project_id}/todos/{todo_id} – update todo          #
        # ------------------------------------------------------------------ #
        @app.put(
            '/projects/{project_id}/todos/{todo_id}',
            response_model=ProjectTodoSchema,
            status_code=200,
            responses={
                status.HTTP_404_NOT_FOUND: {'model': ErrorMessageTodoNotFound},
            },
        )
        def update_project_todo(  # pylint: disable=unused-variable
            project_id: UUID,
            todo_id: UUID,
            data: ProjectTodoUpdateSchema,
            usecase: UpdateTodoThroughProjectUseCase = Depends(get_update_todo_usecase),
        ):
            dto = TodoUpdateDto(
                title=data.title,
                description=data.description,
                dependencies=data.dependencies,
            )
            todo_output = usecase.execute(str(project_id), str(todo_id), dto)
            return ProjectTodoSchema.from_dto(todo_output, str(project_id))

        # ------------------------------------------------------------------ #
        #  PATCH /projects/{project_id}/todos/{todo_id}/start – start todo   #
        # ------------------------------------------------------------------ #
        @app.patch(
            '/projects/{project_id}/todos/{todo_id}/start',
            response_model=ProjectTodoSchema,
            status_code=200,
            responses={
                status.HTTP_404_NOT_FOUND: {'model': ErrorMessageTodoNotFound},
                status.HTTP_400_BAD_REQUEST: {
                    'model': TodoDependencyNotCompletedErrorMessage
                },
            },
        )
        def start_project_todo(  # pylint: disable=unused-variable
            project_id: UUID,
            todo_id: UUID,
            usecase: StartTodoThroughProjectUseCase = Depends(get_start_todo_usecase),
        ):
            todo_output = usecase.execute(str(project_id), str(todo_id))
            return ProjectTodoSchema.from_dto(todo_output, str(project_id))

        # ------------------------------------------------------------------ #
        #  PATCH /projects/{project_id}/todos/{todo_id}/complete – complete  #
        # ------------------------------------------------------------------ #
        @app.patch(
            '/projects/{project_id}/todos/{todo_id}/complete',
            response_model=ProjectTodoSchema,
            status_code=200,
            responses={status.HTTP_404_NOT_FOUND: {'model': ErrorMessageTodoNotFound}},
        )
        def complete_project_todo(  # pylint: disable=unused-variable
            project_id: UUID,
            todo_id: UUID,
            usecase: CompleteTodoThroughProjectUseCase = Depends(
                get_complete_todo_usecase
            ),
        ):
            todo_output = usecase.execute(str(project_id), str(todo_id))
            return ProjectTodoSchema.from_dto(todo_output, str(project_id))
