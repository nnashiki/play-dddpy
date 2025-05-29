"""Test cases for FindTodoThroughProjectUseCase."""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from dddpy.domain.project.entities.project import Project
from dddpy.domain.project.exceptions import ProjectNotFoundError
from dddpy.domain.project.repositories import ProjectRepository
from dddpy.domain.todo.value_objects import TodoTitle
from dddpy.usecase.todo.find_todo_usecase import FindTodoThroughProjectUseCaseImpl


def test_find_todo_through_project_success():
    """Test finding a todo through project successfully."""
    # Setup
    mock_repository = Mock(spec=ProjectRepository)
    project = Project.create('Test Project')
    todo = project.add_todo(TodoTitle('Test Todo'))
    
    # Configure mock to return the project
    mock_repository.find_by_id.return_value = project
    
    # Execute
    usecase = FindTodoThroughProjectUseCaseImpl(mock_repository)
    result = usecase.execute(str(project.id.value), str(todo.id.value))
    
    # Verify
    mock_repository.find_by_id.assert_called_once()
    
    assert result.id == str(todo.id.value)
    assert result.title == 'Test Todo'
    assert result.status == 'not_started'


def test_find_todo_project_not_found():
    """Test finding a todo when project doesn't exist raises ProjectNotFoundError."""
    # Setup
    mock_repository = Mock(spec=ProjectRepository)
    project_id = str(uuid4())
    todo_id = str(uuid4())
    
    # Configure mock to return None (project not found)
    mock_repository.find_by_id.return_value = None
    
    # Execute & Verify
    usecase = FindTodoThroughProjectUseCaseImpl(mock_repository)
    
    with pytest.raises(ProjectNotFoundError):
        usecase.execute(project_id, todo_id)
    
    mock_repository.find_by_id.assert_called_once()


def test_find_todo_uses_find_by_id():
    """Test that the usecase uses find_by_id."""
    # Setup
    mock_repository = Mock(spec=ProjectRepository)
    project = Project.create('Test Project')
    todo = project.add_todo(TodoTitle('Test Todo'))
    
    # Configure mock to return the project
    mock_repository.find_by_id.return_value = project
    
    # Execute
    usecase = FindTodoThroughProjectUseCaseImpl(mock_repository)
    usecase.execute(str(project.id.value), str(todo.id.value))
    
    # Verify that find_by_id was called
    mock_repository.find_by_id.assert_called_once()
    mock_repository.find_all.assert_not_called()
