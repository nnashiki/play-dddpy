"""Test cases for UpdateTodoUseCaseImpl."""

from unittest.mock import Mock, patch

import pytest

from dddpy.domain.todo.entities import Todo
from dddpy.domain.todo.exceptions import TodoCircularDependencyError
from dddpy.domain.todo.repositories import TodoRepository
from dddpy.domain.todo.value_objects import TodoDescription, TodoId, TodoTitle
from dddpy.usecase.todo.update_todo_usecase import UpdateTodoUseCaseImpl


@pytest.fixture
def todo_repository_mock():
    """Create a mock TodoRepository."""
    return Mock(spec=TodoRepository)


@pytest.fixture
def update_todo_usecase(todo_repository_mock):
    """Create a UpdateTodoUseCaseImpl instance with mocked repository."""
    return UpdateTodoUseCaseImpl(todo_repository_mock)


@pytest.fixture
def todo():
    """Create a sample Todo for testing."""
    return Todo(
        id=TodoId.generate(),
        title=TodoTitle('Original Title'),
        description=TodoDescription('Original Description'),
    )


def test_update_todo_title_only(update_todo_usecase, todo_repository_mock, todo):
    """Test updating a Todo's title only."""
    # Arrange
    todo_repository_mock.find_by_id.return_value = todo
    new_title = TodoTitle('Updated Title')

    # Act
    result = update_todo_usecase.execute(todo.id, title=new_title)

    # Assert
    assert result.title == new_title
    assert result.description == todo.description
    todo_repository_mock.find_by_id.assert_called_once_with(todo.id)
    todo_repository_mock.save.assert_called_once_with(result)


def test_update_todo_description_only(update_todo_usecase, todo_repository_mock, todo):
    """Test updating a Todo's description only."""
    # Arrange
    todo_repository_mock.find_by_id.return_value = todo
    new_description = TodoDescription('Updated Description')

    # Act
    result = update_todo_usecase.execute(todo.id, description=new_description)

    # Assert
    assert result.title == todo.title
    assert result.description == new_description
    todo_repository_mock.find_by_id.assert_called_once_with(todo.id)
    todo_repository_mock.save.assert_called_once_with(result)


def test_update_todo_both_fields(update_todo_usecase, todo_repository_mock, todo):
    """Test updating both title and description of a Todo."""
    # Arrange
    todo_repository_mock.find_by_id.return_value = todo
    new_title = TodoTitle('Updated Title')
    new_description = TodoDescription('Updated Description')

    # Act
    result = update_todo_usecase.execute(
        todo.id, title=new_title, description=new_description
    )

    # Assert
    assert result.title == new_title
    assert result.description == new_description
    todo_repository_mock.find_by_id.assert_called_once_with(todo.id)
    todo_repository_mock.save.assert_called_once_with(result)


def test_update_todo_not_found(update_todo_usecase, todo_repository_mock):
    """Test updating a non-existent Todo."""
    # Arrange
    todo_id = TodoId.generate()
    todo_repository_mock.find_by_id.return_value = None
    new_title = TodoTitle('Updated Title')

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        update_todo_usecase.execute(todo_id, title=new_title)
    assert 'The Todo you specified does not exist' in str(exc_info.value)


def test_update_todo_dependencies(update_todo_usecase, todo_repository_mock, todo):
    """Test updating a Todo's dependencies."""
    # Arrange
    dep_id1 = TodoId.generate()
    dep_id2 = TodoId.generate()
    dependencies = [dep_id1, dep_id2]

    # Create mock dependency todos with empty dependencies
    dep_todo1 = Todo.create(TodoTitle('Dependency 1'))
    dep_todo2 = Todo.create(TodoTitle('Dependency 2'))

    todo_repository_mock.find_by_id.side_effect = lambda todo_id: (
        todo
        if todo_id == todo.id
        else dep_todo1
        if todo_id == dep_id1
        else dep_todo2
        if todo_id == dep_id2
        else None
    )

    # Act
    result = update_todo_usecase.execute(todo.id, dependencies=dependencies)

    # Assert
    assert result.dependencies.contains(dep_id1)
    assert result.dependencies.contains(dep_id2)
    assert result.dependencies.size() == 2
    todo_repository_mock.save.assert_called_once_with(result)


def test_update_todo_dependencies_circular_error(
    update_todo_usecase, todo_repository_mock, todo
):
    """Test updating a Todo's dependencies with circular dependency."""
    # Arrange
    dep_todo = Todo.create(TodoTitle('Dependency Todo'))
    dep_todo.add_dependency(todo.id)  # dep_todo depends on todo

    # Mock repository to return the circular dependency
    todo_repository_mock.find_by_id.side_effect = lambda todo_id: (
        todo if todo_id == todo.id else dep_todo if todo_id == dep_todo.id else None
    )

    # Act & Assert - try to make todo depend on dep_todo (circular)
    with pytest.raises(TodoCircularDependencyError):
        update_todo_usecase.execute(todo.id, dependencies=[dep_todo.id])

    # Verify save was not called
    todo_repository_mock.save.assert_not_called()
