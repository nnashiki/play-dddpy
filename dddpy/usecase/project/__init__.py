"""This package provides use cases for Project entity operations."""

from dddpy.usecase.project.create_project_usecase import (
    CreateProjectUseCase,
    new_create_project_usecase,
)
from dddpy.usecase.project.add_todo_to_project_usecase import (
    AddTodoToProjectUseCase,
    new_add_todo_to_project_usecase,
)
from dddpy.usecase.project.find_projects_usecase import (
    FindProjectsUseCase,
    new_find_projects_usecase,
)
from dddpy.usecase.project.start_todo_through_project_usecase import (
    StartTodoThroughProjectUseCase,
    new_start_todo_through_project_usecase,
)
from dddpy.usecase.project.complete_todo_through_project_usecase import (
    CompleteTodoThroughProjectUseCase,
    new_complete_todo_through_project_usecase,
)
from dddpy.usecase.project.update_todo_through_project_usecase import (
    UpdateTodoThroughProjectUseCase,
    new_update_todo_through_project_usecase,
)
from dddpy.usecase.project.delete_project_usecase import (
    DeleteProjectUseCase,
    new_delete_project_usecase,
)

__all__ = [
    'CreateProjectUseCase',
    'AddTodoToProjectUseCase',
    'FindProjectsUseCase',
    'StartTodoThroughProjectUseCase',
    'CompleteTodoThroughProjectUseCase',
    'UpdateTodoThroughProjectUseCase',
    'DeleteProjectUseCase',
    'new_create_project_usecase',
    'new_add_todo_to_project_usecase',
    'new_find_projects_usecase',
    'new_start_todo_through_project_usecase',
    'new_complete_todo_through_project_usecase',
    'new_update_todo_through_project_usecase',
    'new_delete_project_usecase',
]
