"""Test cases for SetDependenciesUseCase."""

import pytest
from unittest.mock import Mock
from uuid import uuid4

from dddpy.domain.todo.entities import Todo
from dddpy.domain.todo.exceptions import TodoNotFoundError
from dddpy.domain.todo.value_objects import TodoId, TodoTitle
from dddpy.usecase.todo import SetDependenciesUseCase, new_set_dependencies_usecase


class TestSetDependenciesUseCase:
    """Test cases for SetDependenciesUseCase."""

    def test_set_dependencies_success(self):
        """Test successfully setting dependencies for a todo."""
        # Create todo
        todo = Todo.create(TodoTitle('Main Task'))

        # Create dependency IDs
        dep_id1 = TodoId(uuid4())
        dep_id2 = TodoId(uuid4())
        dependencies = [dep_id1, dep_id2]

        # Mock repository
        mock_repo = Mock()
        mock_repo.find_by_id.return_value = todo

        # Create use case
        usecase = new_set_dependencies_usecase(mock_repo)

        # Execute
        result = usecase.execute(todo.id, dependencies)

        # Verify
        assert result.dependencies.contains(dep_id1)
        assert result.dependencies.contains(dep_id2)
        assert result.dependencies.size() == 2
        mock_repo.save.assert_called_once_with(todo)

    def test_set_dependencies_todo_not_found(self):
        """Test setting dependencies for non-existent todo."""
        # Mock repository
        mock_repo = Mock()
        mock_repo.find_by_id.return_value = None

        # Create use case
        usecase = new_set_dependencies_usecase(mock_repo)

        # Execute and expect error
        non_existent_id = TodoId(uuid4())
        with pytest.raises(TodoNotFoundError):
            usecase.execute(non_existent_id, [])

        # Verify save was not called
        mock_repo.save.assert_not_called()

    def test_set_empty_dependencies(self):
        """Test setting empty dependencies (clearing dependencies)."""
        # Create todo with existing dependencies
        existing_dep = TodoId(uuid4())
        todo = Todo.create(TodoTitle('Task with deps'))
        todo.add_dependency(existing_dep)

        # Mock repository
        mock_repo = Mock()
        mock_repo.find_by_id.return_value = todo

        # Create use case
        usecase = new_set_dependencies_usecase(mock_repo)

        # Execute with empty dependencies
        result = usecase.execute(todo.id, [])

        # Verify dependencies are cleared
        assert result.dependencies.is_empty()
        mock_repo.save.assert_called_once_with(todo)

    def test_set_dependencies_with_self_reference(self):
        """Test setting dependencies that include self-reference (should fail)."""
        # Create todo
        todo = Todo.create(TodoTitle('Self-referencing task'))

        # Mock repository
        mock_repo = Mock()
        mock_repo.find_by_id.return_value = todo

        # Create use case
        usecase = new_set_dependencies_usecase(mock_repo)

        # Execute with self-reference and expect error
        with pytest.raises(ValueError, match='Cannot add self .* as dependency'):
            usecase.execute(todo.id, [todo.id])

        # Verify save was not called
        mock_repo.save.assert_not_called()

    def test_set_dependencies_replace_existing(self):
        """Test replacing existing dependencies with new ones."""
        # Create todo with existing dependencies
        old_dep = TodoId(uuid4())
        todo = Todo.create(TodoTitle('Task'))
        todo.add_dependency(old_dep)

        # New dependencies
        new_dep1 = TodoId(uuid4())
        new_dep2 = TodoId(uuid4())
        new_dependencies = [new_dep1, new_dep2]

        # Mock repository
        mock_repo = Mock()
        mock_repo.find_by_id.return_value = todo

        # Create use case
        usecase = new_set_dependencies_usecase(mock_repo)

        # Execute
        result = usecase.execute(todo.id, new_dependencies)

        # Verify old dependencies are replaced
        assert not result.dependencies.contains(old_dep)
        assert result.dependencies.contains(new_dep1)
        assert result.dependencies.contains(new_dep2)
        assert result.dependencies.size() == 2
        mock_repo.save.assert_called_once_with(todo)
