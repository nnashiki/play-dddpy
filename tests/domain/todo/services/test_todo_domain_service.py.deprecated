"""Tests for TodoDomainService"""

from unittest.mock import Mock
import pytest

from dddpy.domain.todo.exceptions import (
    TodoDependencyNotFoundError,
    TodoCircularDependencyError,
)
from dddpy.domain.todo.services.todo_domain_service import TodoDomainService
from dddpy.domain.todo.value_objects import TodoId, TodoDependencies


def test_validate_dependencies_exist_should_raise_error_when_dependency_not_found():
    """Test that validate_dependencies_exist raises TodoDependencyNotFoundError when dependency is not found"""
    # Arrange
    mock_repo = Mock()
    mock_repo.find_by_id.return_value = None  # Dependency not found

    dep_id = TodoId.generate()
    dependency_ids = [dep_id]

    # Act & Assert
    with pytest.raises(TodoDependencyNotFoundError) as exc_info:
        TodoDomainService.validate_dependencies_exist(dependency_ids, mock_repo)

    assert str(dep_id.value) in str(exc_info.value)


def test_validate_dependencies_exist_should_pass_when_all_dependencies_exist():
    """Test that validate_dependencies_exist passes when all dependencies exist"""
    # Arrange
    mock_repo = Mock()
    mock_todo = Mock()
    mock_repo.find_by_id.return_value = mock_todo  # Dependency exists

    dep_id = TodoId.generate()
    dependency_ids = [dep_id]

    # Act - should not raise any exception
    TodoDomainService.validate_dependencies_exist(dependency_ids, mock_repo)

    # Assert
    mock_repo.find_by_id.assert_called_once_with(dep_id)


def test_validate_no_circular_dependency_should_raise_error_when_circular_dependency_exists():
    """Test that validate_no_circular_dependency raises TodoCircularDependencyError when circular dependency exists"""
    # Arrange
    mock_repo = Mock()
    mock_todo = Mock()
    mock_todo.id = TodoId.generate()

    # Create a dependency that would create circular dependency: todo -> dep1 -> todo
    dep1_id = TodoId.generate()
    dep1_todo = Mock()
    dep1_todo.dependencies.values = {mock_todo.id}  # dep1 depends on todo

    mock_repo.find_by_id.side_effect = lambda todo_id: (
        dep1_todo if todo_id == dep1_id else None
    )

    new_dependencies = [dep1_id]

    # Act & Assert
    with pytest.raises(TodoCircularDependencyError):
        TodoDomainService.validate_no_circular_dependency(
            mock_todo, new_dependencies, mock_repo
        )


def test_validate_no_circular_dependency_should_pass_when_no_circular_dependency():
    """Test that validate_no_circular_dependency passes when no circular dependency exists"""
    # Arrange
    mock_repo = Mock()
    mock_todo = Mock()
    mock_todo.id = TodoId.generate()

    dep_id = TodoId.generate()
    new_dependencies = [dep_id]

    # Mock a dependency todo that doesn't create circular dependency
    dep_todo = Mock()
    dep_todo.dependencies.values = set()  # Empty dependencies

    mock_repo.find_by_id.side_effect = lambda todo_id: (
        dep_todo if todo_id == dep_id else None
    )

    # Act - should not raise any exception
    TodoDomainService.validate_no_circular_dependency(
        mock_todo, new_dependencies, mock_repo
    )
