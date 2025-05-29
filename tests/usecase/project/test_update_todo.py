"""Test cases for UpdateTodoThroughProjectUseCase."""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from dddpy.dto.todo import TodoUpdateDto
from dddpy.domain.project.entities.project import Project
from dddpy.domain.project.exceptions import ProjectNotFoundError
from dddpy.domain.project.repositories import ProjectRepository
from dddpy.domain.todo.value_objects import TodoTitle, TodoId
from dddpy.usecase.project.update_todo_through_project_usecase import (
    UpdateTodoThroughProjectUseCaseImpl
)


def test_update_todo_through_project_success():
    """Test updating a todo through project successfully."""
    # Setup
    mock_repository = Mock(spec=ProjectRepository)
    project = Project.create('Test Project')
    todo = project.add_todo(TodoTitle('Original Title'))
    
    # Configure mock to return the project
    mock_repository.find_by_id.return_value = project
    
    # Create update DTO
    update_dto = TodoUpdateDto(
        title='Updated Title',
        description='Updated Description'
    )
    
    # Execute
    usecase = UpdateTodoThroughProjectUseCaseImpl(mock_repository)
    result = usecase.execute(str(project.id.value), str(todo.id.value), update_dto)
    
    # Verify
    mock_repository.find_by_id.assert_called_once()
    mock_repository.save.assert_called_once_with(project)
    
    assert result.id == str(todo.id.value)
    assert result.title == 'Updated Title'
    assert result.description == 'Updated Description'


def test_update_todo_through_project_todo_not_found():
    """Test updating a non-existent todo raises ProjectNotFoundError."""
    # Setup
    mock_repository = Mock(spec=ProjectRepository)
    todo_id = str(uuid4())
    
    # Configure mock to return None (project not found)
    mock_repository.find_by_id.return_value = None
    
    # Create update DTO
    update_dto = TodoUpdateDto(title='Updated Title')
    
    # Execute & Verify
    usecase = UpdateTodoThroughProjectUseCaseImpl(mock_repository)
    
    with pytest.raises(ProjectNotFoundError):
        usecase.execute(str(uuid4()), todo_id, update_dto)
    
    mock_repository.find_by_id.assert_called_once()
    mock_repository.save.assert_not_called()


def test_update_todo_uses_find_by_id():
    """Test that the usecase uses find_by_id instead of find_project_by_todo_id."""
    # Setup
    mock_repository = Mock(spec=ProjectRepository)
    project = Project.create('Test Project')
    todo = project.add_todo(TodoTitle('Original Title'))
    
    # Configure mock to return the project
    mock_repository.find_by_id.return_value = project
    
    # Create update DTO
    update_dto = TodoUpdateDto(title='Updated Title')
    
    # Execute
    usecase = UpdateTodoThroughProjectUseCaseImpl(mock_repository)
    usecase.execute(str(project.id.value), str(todo.id.value), update_dto)
    
    # Verify that find_by_id was called, not find_project_by_todo_id
    mock_repository.find_by_id.assert_called_once()
    mock_repository.find_all.assert_not_called()


def test_update_todo_with_dependencies():
    """Test updating a todo with dependencies."""
    # Setup
    mock_repository = Mock(spec=ProjectRepository)
    project = Project.create('Test Project')
    
    # Create todos with dependencies
    todo1 = project.add_todo(TodoTitle('Todo 1'))
    todo2 = project.add_todo(TodoTitle('Todo 2'))
    todo3 = project.add_todo(TodoTitle('Todo 3'), dependencies=[todo1.id])
    
    # Configure mock to return the project
    mock_repository.find_by_id.return_value = project
    
    # Create update DTO to change dependencies
    update_dto = TodoUpdateDto(
        title='Updated Todo 3',
        dependencies=[str(todo2.id.value)]
    )
    
    # Execute
    usecase = UpdateTodoThroughProjectUseCaseImpl(mock_repository)
    result = usecase.execute(str(project.id.value), str(todo3.id.value), update_dto)
    
    # Verify
    assert result.title == 'Updated Todo 3'
    assert result.dependencies == [str(todo2.id.value)]
    mock_repository.save.assert_called_once_with(project)
