"""Test cases for CompleteTodoThroughProjectUseCase."""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from dddpy.domain.project.entities.project import Project
from dddpy.domain.project.exceptions import ProjectNotFoundError
from dddpy.domain.project.repositories import ProjectRepository
from dddpy.domain.todo.value_objects import TodoTitle, TodoId
from dddpy.usecase.project.complete_todo_through_project_usecase import (
    CompleteTodoThroughProjectUseCaseImpl
)


def test_complete_todo_through_project_success():
    """Test completing a todo through project successfully."""
    # Setup
    mock_repository = Mock(spec=ProjectRepository)
    project = Project.create('Test Project')
    todo = project.add_todo(TodoTitle('Test Todo'))
    
    # Start the todo first (required before completion)
    project.start_todo_by_id(todo.id)
    
    # Configure mock to return the project
    mock_repository.find_project_by_todo_id.return_value = project
    
    # Execute
    usecase = CompleteTodoThroughProjectUseCaseImpl(mock_repository)
    result = usecase.execute(str(todo.id.value))
    
    # Verify
    mock_repository.find_project_by_todo_id.assert_called_once_with(todo.id)
    mock_repository.save.assert_called_once_with(project)
    
    assert result.id == str(todo.id.value)
    assert result.status == 'completed'
    assert result.title == 'Test Todo'


def test_complete_todo_through_project_todo_not_found():
    """Test completing a non-existent todo raises ProjectNotFoundError."""
    # Setup
    mock_repository = Mock(spec=ProjectRepository)
    todo_id = str(uuid4())
    
    # Configure mock to return None (todo not found)
    mock_repository.find_project_by_todo_id.return_value = None
    
    # Execute & Verify
    usecase = CompleteTodoThroughProjectUseCaseImpl(mock_repository)
    
    with pytest.raises(ProjectNotFoundError):
        usecase.execute(todo_id)
    
    mock_repository.find_project_by_todo_id.assert_called_once()
    mock_repository.save.assert_not_called()


def test_complete_todo_uses_find_project_by_todo_id():
    """Test that the usecase uses find_project_by_todo_id instead of find_all."""
    # Setup
    mock_repository = Mock(spec=ProjectRepository)
    project = Project.create('Test Project')
    todo = project.add_todo(TodoTitle('Test Todo'))
    
    # Start the todo first
    project.start_todo_by_id(todo.id)
    
    # Configure mock to return the project
    mock_repository.find_project_by_todo_id.return_value = project
    
    # Execute
    usecase = CompleteTodoThroughProjectUseCaseImpl(mock_repository)
    usecase.execute(str(todo.id.value))
    
    # Verify that find_project_by_todo_id was called, not find_all
    mock_repository.find_project_by_todo_id.assert_called_once_with(todo.id)
    mock_repository.find_all.assert_not_called()
