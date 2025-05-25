"""Test cases for Todo dependencies functionality."""

import pytest
from uuid import uuid4
from unittest.mock import Mock

from dddpy.domain.todo.entities import Todo
from dddpy.domain.todo.services.todo_domain_service import TodoDomainService
from dddpy.domain.todo.value_objects import (
    TodoDependencies,
    TodoDescription,
    TodoId,
    TodoTitle,
)


class TestTodoDependencies:
    """Test cases for Todo dependencies."""

    def test_todo_create_with_dependencies(self):
        """Test creating a Todo with dependencies."""
        # Create dependency todo
        dep_id = TodoId(uuid4())
        dependencies = TodoDependencies.from_list([dep_id])

        # Create todo with dependencies
        todo = Todo.create(
            TodoTitle('Task with dependency'),
            TodoDescription('A task that depends on another'),
            dependencies,
        )

        assert todo.dependencies.contains(dep_id)
        assert todo.dependencies.size() == 1

    def test_todo_add_dependency(self):
        """Test adding a dependency to a Todo."""
        todo = Todo.create(TodoTitle('Main Task'))
        dep_id = TodoId(uuid4())

        # Add dependency
        todo.add_dependency(dep_id)

        assert todo.dependencies.contains(dep_id)
        assert todo.dependencies.size() == 1

    def test_todo_add_duplicate_dependency(self):
        """Test adding duplicate dependency (should be ignored)."""
        todo = Todo.create(TodoTitle('Main Task'))
        dep_id = TodoId(uuid4())

        # Add same dependency twice
        todo.add_dependency(dep_id)
        todo.add_dependency(dep_id)  # Should be ignored

        assert todo.dependencies.size() == 1

    def test_todo_add_self_dependency_error(self):
        """Test that adding self as dependency raises error."""
        todo = Todo.create(TodoTitle('Self Dependent Task'))

        with pytest.raises(ValueError, match='Cannot add self as dependency'):
            todo.add_dependency(todo.id)

    def test_todo_remove_dependency(self):
        """Test removing a dependency from a Todo."""
        dep_id = TodoId(uuid4())
        dependencies = TodoDependencies.from_list([dep_id])
        todo = Todo.create(TodoTitle('Task'), dependencies=dependencies)

        # Remove dependency
        todo.remove_dependency(dep_id)

        assert not todo.dependencies.contains(dep_id)
        assert todo.dependencies.size() == 0

    def test_todo_set_dependencies(self):
        """Test setting dependencies for a Todo."""
        todo = Todo.create(TodoTitle('Main Task'))
        dep_id1 = TodoId(uuid4())
        dep_id2 = TodoId(uuid4())

        dependencies = TodoDependencies.from_list([dep_id1, dep_id2])
        todo.set_dependencies(dependencies)

        assert todo.dependencies.contains(dep_id1)
        assert todo.dependencies.contains(dep_id2)
        assert todo.dependencies.size() == 2

    def test_todo_set_self_dependency_error(self):
        """Test that setting self as dependency raises error."""
        todo = Todo.create(TodoTitle('Self Dependent Task'))
        dependencies = TodoDependencies.from_list([todo.id])

        with pytest.raises(ValueError, match='Cannot add self as dependency'):
            todo.set_dependencies(dependencies)

    def test_todo_can_start_no_dependencies(self):
        """Test that Todo without dependencies can always start."""
        todo = Todo.create(TodoTitle('Independent Task'))

        # Mock repository
        mock_repository = Mock()

        # Should be able to start without dependencies
        assert TodoDomainService.can_start(todo, mock_repository)

    def test_todo_can_start_with_completed_dependencies(self):
        """Test that Todo can start when all dependencies are completed."""
        dep_todo = Todo.create(TodoTitle('Dependency Task'))
        dep_todo.start()  # Start before completing
        dep_todo.complete()  # Complete the dependency

        todo = Todo.create(TodoTitle('Main Task'))
        todo.add_dependency(dep_todo.id)

        # Mock repository
        mock_repository = Mock()
        mock_repository.find_by_id.return_value = dep_todo

        assert TodoDomainService.can_start(todo, mock_repository)

    def test_todo_cannot_start_with_incomplete_dependencies(self):
        """Test that Todo cannot start when dependencies are incomplete."""
        dep_todo = Todo.create(TodoTitle('Incomplete Dependency'))
        # Don't complete the dependency

        todo = Todo.create(TodoTitle('Main Task'))
        todo.add_dependency(dep_todo.id)

        # Mock repository
        mock_repository = Mock()
        mock_repository.find_by_id.return_value = dep_todo

        assert not TodoDomainService.can_start(todo, mock_repository)

    def test_todo_cannot_start_with_missing_dependencies(self):
        """Test that Todo cannot start when dependency todos are not found."""
        missing_id = TodoId(uuid4())

        todo = Todo.create(TodoTitle('Main Task'))
        todo.add_dependency(missing_id)

        # Mock repository
        mock_repository = Mock()
        mock_repository.find_by_id.return_value = None  # Simulate missing todo

        assert not TodoDomainService.can_start(todo, mock_repository)

    def test_todo_can_start_multiple_dependencies(self):
        """Test Todo with multiple dependencies."""
        dep1 = Todo.create(TodoTitle('Dependency 1'))
        dep2 = Todo.create(TodoTitle('Dependency 2'))

        todo = Todo.create(TodoTitle('Main Task'))
        todo.add_dependency(dep1.id)
        todo.add_dependency(dep2.id)

        # Mock repository
        mock_repository = Mock()

        def mock_find_by_id(todo_id):
            if todo_id == dep1.id:
                return dep1
            elif todo_id == dep2.id:
                return dep2
            return None

        mock_repository.find_by_id.side_effect = mock_find_by_id

        # Neither completed - cannot start
        assert not TodoDomainService.can_start(todo, mock_repository)

        # One completed - still cannot start
        dep1.start()  # Start before completing
        dep1.complete()
        assert not TodoDomainService.can_start(todo, mock_repository)

        # Both completed - can start
        dep2.start()  # Start before completing
        dep2.complete()
        assert TodoDomainService.can_start(todo, mock_repository)


class TestTodoDependenciesValueObject:
    """Test cases for TodoDependencies value object."""

    def test_empty_dependencies(self):
        """Test creating empty dependencies."""
        deps = TodoDependencies.empty()
        assert deps.is_empty()
        assert deps.size() == 0

    def test_dependencies_from_list(self):
        """Test creating dependencies from list."""
        ids = [TodoId(uuid4()), TodoId(uuid4())]
        deps = TodoDependencies.from_list(ids)

        assert deps.size() == 2
        assert deps.contains(ids[0])
        assert deps.contains(ids[1])

    def test_dependencies_from_list_with_duplicates(self):
        """Test that duplicates are removed when creating from list."""
        id1 = TodoId(uuid4())
        ids = [id1, id1, id1]  # Same ID repeated
        deps = TodoDependencies.from_list(ids)

        assert deps.size() == 1
        assert deps.contains(id1)

    def test_dependencies_add(self):
        """Test adding dependency to dependencies."""
        deps = TodoDependencies.empty()
        id1 = TodoId(uuid4())

        new_deps = deps.add(id1)

        assert deps.is_empty()  # Original unchanged
        assert new_deps.contains(id1)
        assert new_deps.size() == 1

    def test_dependencies_remove(self):
        """Test removing dependency from dependencies."""
        id1 = TodoId(uuid4())
        deps = TodoDependencies.from_list([id1])

        new_deps = deps.remove(id1)

        assert deps.contains(id1)  # Original unchanged
        assert not new_deps.contains(id1)
        assert new_deps.is_empty()

    def test_dependencies_to_list(self):
        """Test converting dependencies to list."""
        ids = [TodoId(uuid4()), TodoId(uuid4())]
        deps = TodoDependencies.from_list(ids)

        result_list = deps.to_list()

        assert len(result_list) == 2
        assert all(id in result_list for id in ids)

    def test_dependencies_max_limit(self):
        """Test that too many dependencies raises error."""
        # Create 101 dependencies (over the limit of 100)
        ids = [TodoId(uuid4()) for _ in range(101)]

        with pytest.raises(ValueError, match='Too many dependencies'):
            TodoDependencies.from_list(ids)
