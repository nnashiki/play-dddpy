"""Test cases for Todo dependencies functionality."""

import pytest
from uuid import uuid4
from unittest.mock import Mock

from dddpy.domain.todo.entities import Todo
from dddpy.domain.todo.value_objects import (
    TodoDependencies,
    TodoDescription,
    TodoId,
    TodoTitle,
)
from dddpy.domain.todo.exceptions import TooManyDependenciesError
from dddpy.domain.project.value_objects import ProjectId


@pytest.fixture
def project_id():
    """Create a sample ProjectId for testing."""
    return ProjectId.generate()


class TestTodoDependencies:
    """Test cases for Todo dependencies."""

    def test_todo_create_with_dependencies(self, project_id):
        """Test creating a Todo with dependencies."""
        # Create dependency todo
        dep_id = TodoId(uuid4())
        dependencies = TodoDependencies.from_list([dep_id])

        # Create todo with dependencies
        todo = Todo.create(
            TodoTitle('Task with dependency'),
            project_id,
            TodoDescription('A task that depends on another'),
            dependencies,
        )

        assert todo.dependencies.contains(dep_id)
        assert todo.dependencies.size() == 1


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

        with pytest.raises(TooManyDependenciesError):
            TodoDependencies.from_list(ids)
