"""Test cases for StartTodoThroughProjectUseCase."""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from dddpy.domain.project.entities.project import Project
from dddpy.domain.project.exceptions import ProjectNotFoundError
from dddpy.domain.project.repositories import ProjectRepository
from dddpy.domain.todo.value_objects import TodoTitle, TodoId
from dddpy.usecase.project.start_todo_through_project_usecase import (
    StartTodoThroughProjectUseCaseImpl
)


def test_start_todo_through_project_success():
    """Test starting a todo through project successfully."""
    # Setup
    mock_repository = Mock(spec=ProjectRepository)
    project = Project.create('Test Project')
    todo = project.add_todo(TodoTitle('Test Todo'))
    
    # Configure mock to return the project
    mock_repository.find_by_id.return_value = project
    
    # Execute
    usecase = StartTodoThroughProjectUseCaseImpl(mock_repository)
    result = usecase.execute(str(project.id.value), str(todo.id.value))
    
    # Verify
    mock_repository.find_by_id.assert_called_once()
    mock_repository.save.assert_called_once_with(project)
    
    assert result.id == str(todo.id.value)
    assert result.status == 'in_progress'
    assert result.title == 'Test Todo'


def test_start_todo_through_project_todo_not_found():
    """Test starting a non-existent todo raises ProjectNotFoundError."""
    # Setup
    mock_repository = Mock(spec=ProjectRepository)
    todo_id = str(uuid4())
    
    # Configure mock to return None (project not found)
    mock_repository.find_by_id.return_value = None
    
    # Execute & Verify
    usecase = StartTodoThroughProjectUseCaseImpl(mock_repository)
    
    with pytest.raises(ProjectNotFoundError):
        usecase.execute(str(uuid4()), todo_id)
    
    mock_repository.find_by_id.assert_called_once()
    mock_repository.save.assert_not_called()


def test_start_todo_uses_find_by_id():
    """Test that the usecase uses find_by_id instead of find_project_by_todo_id."""
    # Setup
    mock_repository = Mock(spec=ProjectRepository)
    project = Project.create('Test Project')
    todo = project.add_todo(TodoTitle('Test Todo'))
    
    # Configure mock to return the project
    mock_repository.find_by_id.return_value = project
    
    # Execute
    usecase = StartTodoThroughProjectUseCaseImpl(mock_repository)
    usecase.execute(str(project.id.value), str(todo.id.value))
    
    # Verify that find_by_id was called, not find_project_by_todo_id
    mock_repository.find_by_id.assert_called_once()
    mock_repository.find_all.assert_not_called()
