"""Test cases for CreateTodoUseCase with dependencies."""

import pytest
from unittest.mock import Mock
from uuid import uuid4

from dddpy.domain.todo.value_objects import TodoDescription, TodoId, TodoTitle
from dddpy.usecase.todo import CreateTodoUseCase, new_create_todo_usecase


class TestCreateTodoUseCaseWithDependencies:
    """Test cases for CreateTodoUseCase with dependency support."""

    def test_create_todo_with_dependencies(self):
        """Test creating a todo with dependencies."""
        # Create dependency IDs
        dep_id1 = TodoId(uuid4())
        dep_id2 = TodoId(uuid4())
        dependencies = [dep_id1, dep_id2]

        # Mock repository
        mock_repo = Mock()

        # Create use case
        usecase = new_create_todo_usecase(mock_repo)

        # Execute
        result = usecase.execute(
            TodoTitle('Task with dependencies'),
            TodoDescription('A task that depends on others'),
            dependencies,
        )

        # Verify
        assert result.title.value == 'Task with dependencies'
        assert result.dependencies.contains(dep_id1)
        assert result.dependencies.contains(dep_id2)
        assert result.dependencies.size() == 2
        mock_repo.save.assert_called_once()

    def test_create_todo_without_dependencies(self):
        """Test creating a todo without dependencies (backward compatibility)."""
        # Mock repository
        mock_repo = Mock()

        # Create use case
        usecase = new_create_todo_usecase(mock_repo)

        # Execute without dependencies
        result = usecase.execute(
            TodoTitle('Independent task'), TodoDescription('A standalone task')
        )

        # Verify
        assert result.title.value == 'Independent task'
        assert result.dependencies.is_empty()
        mock_repo.save.assert_called_once()

    def test_create_todo_with_empty_dependencies_list(self):
        """Test creating a todo with empty dependencies list."""
        # Mock repository
        mock_repo = Mock()

        # Create use case
        usecase = new_create_todo_usecase(mock_repo)

        # Execute with empty dependencies
        result = usecase.execute(TodoTitle('Task with empty deps'), dependencies=[])

        # Verify
        assert result.title.value == 'Task with empty deps'
        assert result.dependencies.is_empty()
        mock_repo.save.assert_called_once()

    def test_create_todo_with_duplicate_dependencies(self):
        """Test creating a todo with duplicate dependencies (should be deduplicated)."""
        # Create dependency ID (duplicated)
        dep_id = TodoId(uuid4())
        dependencies = [dep_id, dep_id, dep_id]  # Same ID repeated

        # Mock repository
        mock_repo = Mock()

        # Create use case
        usecase = new_create_todo_usecase(mock_repo)

        # Execute
        result = usecase.execute(
            TodoTitle('Task with duplicate deps'), dependencies=dependencies
        )

        # Verify that duplicates are removed
        assert result.dependencies.contains(dep_id)
        assert result.dependencies.size() == 1
        mock_repo.save.assert_called_once()
