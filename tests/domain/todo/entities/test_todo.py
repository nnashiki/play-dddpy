"""Test cases for the Todo entity."""

from datetime import datetime, timedelta

import pytest

from dddpy.domain.todo.entities.todo import Todo
from dddpy.domain.todo.exceptions import (
    TodoAlreadyCompletedError,
    TodoAlreadyStartedError,
    TodoNotStartedError,
)
from dddpy.domain.todo.value_objects import (
    TodoDescription,
    TodoId,
    TodoStatus,
    TodoTitle,
)
from dddpy.domain.project.value_objects import ProjectId


@pytest.fixture
def project_id():
    """Create a sample ProjectId for testing."""
    return ProjectId.generate()


def test_create_todo(project_id):
    """Test creating a new Todo."""
    title = TodoTitle('Test Todo')
    description = TodoDescription('Test Description')
    todo = Todo.create(title, project_id, description)

    assert isinstance(todo.id, TodoId)
    assert todo.title == title
    assert todo.description == description
    assert todo.project_id == project_id
    assert todo.status == TodoStatus.NOT_STARTED
    assert isinstance(todo.created_at, datetime)
    assert isinstance(todo.updated_at, datetime)
    assert todo.completed_at is None


def test_todo_properties(project_id):
    """Test Todo properties."""
    todo_id = TodoId.generate()
    title = TodoTitle('Test Todo')
    description = TodoDescription('Test Description')
    created_at = datetime.now()
    updated_at = datetime.now()

    todo = Todo(
        id=todo_id,
        title=title,
        project_id=project_id,
        description=description,
        status=TodoStatus.NOT_STARTED,
        created_at=created_at,
        updated_at=updated_at,
    )

    assert todo.id == todo_id
    assert todo.title == title
    assert todo.project_id == project_id
    assert todo.description == description
    assert todo.status == TodoStatus.NOT_STARTED
    assert todo.created_at == created_at
    assert todo.updated_at == updated_at
    assert todo.completed_at is None


def test_update_title(project_id):
    """Test updating Todo title."""
    todo = Todo.create(TodoTitle('Original Title'), project_id)
    new_title = TodoTitle('Updated Title')

    todo.update_title(new_title)

    assert todo.title == new_title
    assert todo.updated_at > todo.created_at


def test_update_description(project_id):
    """Test updating Todo description."""
    todo = Todo.create(TodoTitle('Test Todo'), project_id)
    new_description = TodoDescription('Updated Description')

    todo.update_description(new_description)

    assert todo.description == new_description
    assert todo.updated_at > todo.created_at


def test_clear_description(project_id):
    """Test clearing Todo description."""
    todo = Todo.create(TodoTitle('Test Todo'), project_id, TodoDescription('Original Description'))

    todo.update_description(None)

    assert todo.description is None
    assert todo.updated_at > todo.created_at


def test_start_todo(project_id):
    """Test starting a Todo."""
    todo = Todo.create(TodoTitle('Test Todo'), project_id)

    todo.start()

    assert todo.status == TodoStatus.IN_PROGRESS
    assert todo.updated_at > todo.created_at


def test_complete_todo(project_id):
    """Test completing a Todo."""
    todo = Todo.create(TodoTitle('Test Todo'), project_id)
    todo.start()  # Need to start before completing

    todo.complete()

    assert todo.status == TodoStatus.COMPLETED
    assert todo.is_completed
    assert todo.completed_at is not None
    assert todo.updated_at == todo.completed_at


def test_complete_already_completed_todo(project_id):
    """Test attempting to complete an already completed Todo."""
    todo = Todo.create(TodoTitle('Test Todo'), project_id)
    todo.start()  # Need to start before completing
    todo.complete()

    with pytest.raises(TodoAlreadyCompletedError):
        todo.complete()


def test_is_overdue(project_id):
    """Test checking if a Todo is overdue."""
    # Create a todo with specific timestamps
    created_at = datetime(2025, 3, 22)  # 2 days before deadline
    deadline = datetime(2025, 3, 24)  # deadline
    current_time = datetime(2025, 3, 23)  # 1 day before deadline

    # Test case 1: Not completed todo should not be overdue before deadline
    todo = Todo(
        id=TodoId.generate(),
        title=TodoTitle('Test Todo'),
        project_id=project_id,
        created_at=created_at,
        updated_at=created_at,
    )
    assert not todo.is_overdue(deadline, current_time)

    # Test case 2: Not completed todo should be overdue after deadline
    current_time = datetime(2025, 3, 25)  # 1 day after deadline
    assert todo.is_overdue(deadline, current_time)

    # Test case 3: Completed todo should never be overdue, even if completed after deadline
    todo.start()  # Need to start before completing
    todo.complete()
    assert not todo.is_overdue(deadline, current_time)

    # Test case 4: Completed todo should never be overdue when completed before deadline
    todo = Todo(
        id=TodoId.generate(),
        title=TodoTitle('Test Todo'),
        project_id=project_id,
        created_at=created_at,
        updated_at=created_at,
    )
    todo.start()  # Need to start before completing
    todo.complete()
    assert not todo.is_overdue(deadline, current_time)


def test_todo_equality(project_id):
    """Test Todo equality comparison."""
    todo_id = TodoId.generate()
    todo1 = Todo.create(TodoTitle('Test Todo'), project_id)
    todo2 = Todo.create(TodoTitle('Test Todo'), project_id)
    todo3 = Todo(
        id=todo_id,
        title=TodoTitle('Test Todo'),
        project_id=project_id,
        status=TodoStatus.NOT_STARTED,
    )
    todo4 = Todo(
        id=todo_id,
        title=TodoTitle('Different Title'),
        project_id=project_id,
        status=TodoStatus.NOT_STARTED,
    )

    assert todo1 != todo2  # Different IDs
    assert todo3 == todo4  # Same ID, different titles
    assert todo1 != 'not a todo'  # Different type


def test_start_already_started_todo_should_raise_error(project_id):
    """Test that starting an already started Todo raises TodoAlreadyStartedError."""
    todo = Todo.create(TodoTitle('Test Todo'), project_id)
    todo.start()

    with pytest.raises(TodoAlreadyStartedError):
        todo.start()


def test_start_completed_todo_should_raise_error(project_id):
    """Test that starting a completed Todo raises TodoAlreadyStartedError."""
    todo = Todo.create(TodoTitle('Test Todo'), project_id)
    todo.start()
    todo.complete()

    with pytest.raises(TodoAlreadyStartedError):
        todo.start()


def test_complete_not_started_todo_should_raise_error(project_id):
    """Test that completing a not started Todo raises TodoNotStartedError."""
    todo = Todo.create(TodoTitle('Test Todo'), project_id)

    with pytest.raises(TodoNotStartedError):
        todo.complete()
