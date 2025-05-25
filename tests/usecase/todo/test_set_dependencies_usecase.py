"""Test cases for SetDependenciesUseCase."""

import pytest
from unittest.mock import Mock
from uuid import uuid4

from dddpy.domain.todo.entities import Todo
from dddpy.domain.todo.exceptions import TodoNotFoundError, TodoCircularDependencyError
from dddpy.domain.todo.value_objects import TodoId, TodoTitle
from dddpy.usecase.todo import SetDependenciesUseCase, new_set_dependencies_usecase


class TestSetDependenciesUseCase:
    """Test cases for SetDependenciesUseCase."""

    def test_set_dependencies_success(self):
        """Test successfully setting dependencies for a todo."""
        # Create todo
        todo = Todo.create(TodoTitle('Main Task'))

        # Create dependency todos that will exist in repository
        dep_todo1 = Todo.create(TodoTitle('Dep 1'))
        dep_todo2 = Todo.create(TodoTitle('Dep 2'))
        dependencies = [dep_todo1.id, dep_todo2.id]

        # Mock repository
        mock_repo = Mock()

        def mock_find_by_id(todo_id):
            if todo_id == todo.id:
                return todo
            elif todo_id == dep_todo1.id:
                return dep_todo1
            elif todo_id == dep_todo2.id:
                return dep_todo2
            else:
                return None

        mock_repo.find_by_id.side_effect = mock_find_by_id

        # Create use case
        usecase = new_set_dependencies_usecase(mock_repo)

        # Execute
        result = usecase.execute(todo.id, dependencies)

        # Verify
        assert result.dependencies.contains(dep_todo1.id)
        assert result.dependencies.contains(dep_todo2.id)
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

        # Create dependency todos that will exist in repository
        dep_todo1 = Todo.create(TodoTitle('Dep 1'))
        dep_todo2 = Todo.create(TodoTitle('Dep 2'))
        new_dependencies = [dep_todo1.id, dep_todo2.id]

        # Mock repository
        mock_repo = Mock()

        def mock_find_by_id(todo_id):
            if todo_id == todo.id:
                return todo
            elif todo_id == dep_todo1.id:
                return dep_todo1
            elif todo_id == dep_todo2.id:
                return dep_todo2
            else:
                return None

        mock_repo.find_by_id.side_effect = mock_find_by_id

        # Create use case
        usecase = new_set_dependencies_usecase(mock_repo)

        # Execute
        result = usecase.execute(todo.id, new_dependencies)

        # Verify old dependencies are replaced
        assert not result.dependencies.contains(old_dep)
        assert result.dependencies.contains(dep_todo1.id)
        assert result.dependencies.contains(dep_todo2.id)
        assert result.dependencies.size() == 2
        mock_repo.save.assert_called_once_with(todo)

    def test_set_dependencies_circular_dependency_error(self):
        """Test setting dependencies that would create circular dependency."""
        # Create two todos
        todo_a = Todo.create(TodoTitle('Task A'))
        todo_b = Todo.create(TodoTitle('Task B'))

        # A depends on B
        todo_a.add_dependency(todo_b.id)

        # Mock repository
        mock_repo = Mock()
        mock_repo.find_by_id.side_effect = lambda todo_id: (
            todo_a if todo_id == todo_a.id else todo_b if todo_id == todo_b.id else None
        )

        # Create use case
        usecase = new_set_dependencies_usecase(mock_repo)

        # Try to make B depend on A (would create circular dependency)
        with pytest.raises(TodoCircularDependencyError):
            usecase.execute(todo_b.id, [todo_a.id])

        # Verify save was not called
        mock_repo.save.assert_not_called()
