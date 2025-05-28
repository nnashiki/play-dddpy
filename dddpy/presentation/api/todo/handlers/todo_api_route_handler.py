"""HTTP routes for Todo operations (project-aggregate aware)."""

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
from dddpy.presentation.api.todo.error_messages import (
    ErrorMessageTodoNotFound,
    TodoDependencyNotCompletedErrorMessage,
)
from dddpy.presentation.api.todo.schemas import (
    TodoSchema,
    TodoUpdateSchema,
)
from dddpy.usecase.project import (
    StartTodoThroughProjectUseCase,
    CompleteTodoThroughProjectUseCase,
    UpdateTodoThroughProjectUseCase,
    FindProjectsUseCase,
)
from dddpy.usecase.todo.find_todo_usecase import FindTodoThroughProjectUseCase


class TodoApiRouteHandler:
    """Registers Todo-related endpoints."""

    def register_routes(self, app: FastAPI) -> None:  # noqa: D401
        # ------------------------------------------------------------------ #
        #  GET /todos  – list all todos                                       #
        # ------------------------------------------------------------------ #
        @app.get('/todos', response_model=List[TodoSchema], status_code=200)
        def get_todos(                             # pylint: disable=unused-variable
            usecase: FindProjectsUseCase = Depends(get_find_projects_usecase),
        ):
            project_outputs = usecase.execute()
            todos = [todo for project in project_outputs for todo in project.todos]
            return [TodoSchema.from_dto(todo) for todo in todos]

        # ------------------------------------------------------------------ #
        #  GET /todos/{todo_id} – retrieve a single todo                      #
        # ------------------------------------------------------------------ #
        @app.get(
            '/todos/{todo_id}',
            response_model=TodoSchema,
            status_code=200,
            responses={status.HTTP_404_NOT_FOUND: {'model': ErrorMessageTodoNotFound}},
        )
        def get_todo(                              # pylint: disable=unused-variable
            todo_id: UUID,
            usecase: FindTodoThroughProjectUseCase = Depends(get_find_todo_usecase),
        ):
            output = usecase.execute(str(todo_id))
            return TodoSchema.from_dto(output)

        # ------------------------------------------------------------------ #
        #  PUT /todos/{todo_id} – update                                      #
        # ------------------------------------------------------------------ #
        @app.put(
            '/todos/{todo_id}',
            response_model=TodoSchema,
            status_code=200,
            responses={
                status.HTTP_404_NOT_FOUND: {'model': ErrorMessageTodoNotFound},
            },
        )
        def update_todo(                           # pylint: disable=unused-variable
            todo_id: UUID,
            data: TodoUpdateSchema,
            usecase: UpdateTodoThroughProjectUseCase = Depends(get_update_todo_usecase),
        ):
            dto = TodoUpdateDto(
                title=data.title,
                description=data.description,
                dependencies=data.dependencies,
            )
            todo_output = usecase.execute(str(todo_id), dto)
            return TodoSchema.from_dto(todo_output)

        # ------------------------------------------------------------------ #
        #  PATCH /todos/{todo_id}/start – start                               #
        # ------------------------------------------------------------------ #
        @app.patch(
            '/todos/{todo_id}/start',
            response_model=TodoSchema,
            status_code=200,
            responses={
                status.HTTP_404_NOT_FOUND: {'model': ErrorMessageTodoNotFound},
                status.HTTP_400_BAD_REQUEST: {'model': TodoDependencyNotCompletedErrorMessage},
            },
        )
        def start_todo(                           # pylint: disable=unused-variable
            todo_id: UUID,
            usecase: StartTodoThroughProjectUseCase = Depends(get_start_todo_usecase),
        ):
            todo_output = usecase.execute(str(todo_id))
            return TodoSchema.from_dto(todo_output)

        # ------------------------------------------------------------------ #
        #  PATCH /todos/{todo_id}/complete – complete                         #
        # ------------------------------------------------------------------ #
        @app.patch(
            '/todos/{todo_id}/complete',
            response_model=TodoSchema,
            status_code=200,
            responses={status.HTTP_404_NOT_FOUND: {'model': ErrorMessageTodoNotFound}},
        )
        def complete_todo(                        # pylint: disable=unused-variable
            todo_id: UUID,
            usecase: CompleteTodoThroughProjectUseCase = Depends(get_complete_todo_usecase),
        ):
            todo_output = usecase.execute(str(todo_id))
            return TodoSchema.from_dto(todo_output)
