"""Test cases for StartTodoUseCase with dependencies."""

import pytest
from unittest.mock import Mock
from uuid import uuid4

from dddpy.domain.todo.entities import Todo
from dddpy.domain.todo.exceptions import TodoDependencyNotCompletedError
from dddpy.domain.todo.value_objects import TodoId, TodoTitle
from dddpy.usecase.todo import StartTodoUseCase, new_start_todo_usecase


class TestStartTodoUseCaseWithDependencies:
    """Test cases for StartTodoUseCase with dependency checking."""

    def test_start_todo_with_completed_dependencies(self):
        """Test starting a todo when all dependencies are completed."""
        # Create a completed dependency todo
        dep_todo = Todo.create(TodoTitle('Dependency Task'))
        dep_todo.complete()

        # Create main todo with dependency
        main_todo = Todo.create(TodoTitle('Main Task'))
        main_todo.add_dependency(dep_todo.id)

        # Mock repository
        mock_repo = Mock()
        mock_repo.find_by_id.side_effect = lambda todo_id: (
            main_todo
            if todo_id == main_todo.id
            else dep_todo
            if todo_id == dep_todo.id
            else None
        )

        # Create use case
        usecase = new_start_todo_usecase(mock_repo)

        # Execute
        result = usecase.execute(main_todo.id)

        # Verify
        assert result.status.value == 'in_progress'
        mock_repo.save.assert_called_once_with(main_todo)

    def test_start_todo_with_incomplete_dependencies(self):
        """Test starting a todo when dependencies are not completed."""
        # Create an incomplete dependency todo
        dep_todo = Todo.create(TodoTitle('Incomplete Dependency'))
        # Don't complete it

        # Create main todo with dependency
        main_todo = Todo.create(TodoTitle('Main Task'))
        main_todo.add_dependency(dep_todo.id)

        # Mock repository
        mock_repo = Mock()
        mock_repo.find_by_id.side_effect = lambda todo_id: (
            main_todo
            if todo_id == main_todo.id
            else dep_todo
            if todo_id == dep_todo.id
            else None
        )

        # Create use case
        usecase = new_start_todo_usecase(mock_repo)

        # Execute and expect error
        with pytest.raises(TodoDependencyNotCompletedError):
            usecase.execute(main_todo.id)

        # Verify save was not called
        mock_repo.save.assert_not_called()

    def test_start_todo_with_missing_dependencies(self):
        """Test starting a todo when dependency todos don't exist."""
        # Create main todo with dependency to non-existent todo
        missing_id = TodoId(uuid4())
        main_todo = Todo.create(TodoTitle('Main Task'))
        main_todo.add_dependency(missing_id)

        # Mock repository
        mock_repo = Mock()
        mock_repo.find_by_id.side_effect = lambda todo_id: (
            main_todo if todo_id == main_todo.id else None
        )

        # Create use case
        usecase = new_start_todo_usecase(mock_repo)

        # Execute and expect error
        with pytest.raises(TodoDependencyNotCompletedError):
            usecase.execute(main_todo.id)

        # Verify save was not called
        mock_repo.save.assert_not_called()

    def test_start_todo_without_dependencies(self):
        """Test starting a todo without any dependencies (should work as before)."""
        # Create todo without dependencies
        todo = Todo.create(TodoTitle('Independent Task'))

        # Mock repository
        mock_repo = Mock()
        mock_repo.find_by_id.return_value = todo

        # Create use case
        usecase = new_start_todo_usecase(mock_repo)

        # Execute
        result = usecase.execute(todo.id)

        # Verify
        assert result.status.value == 'in_progress'
        mock_repo.save.assert_called_once_with(todo)
