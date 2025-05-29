"""Test cases for the Project entity."""

from datetime import datetime

import pytest

from dddpy.domain.project.entities.project import Project
from dddpy.domain.project.value_objects import ProjectId, ProjectName, ProjectDescription
from dddpy.domain.project.exceptions import (
    TodoRemovalNotAllowedError,
    DuplicateTodoTitleError,
    TooManyTodosError,
)
from dddpy.domain.shared.clock import FixedClock
from dddpy.domain.todo.value_objects import TodoTitle, TodoDescription as TodoDescriptionVO, TodoId
from dddpy.domain.todo.exceptions import (
    TodoCircularDependencyError,
    TodoDependencyNotCompletedError,
    TodoDependencyNotFoundError,
    TodoNotFoundError,
)


def test_create_project():
    """Test creating a new Project."""
    project = Project.create('Test Project', 'Test Description')

    assert isinstance(project.id, ProjectId)
    assert project.name.value == 'Test Project'
    assert project.description.value == 'Test Description'
    assert len(project.todos) == 0
    assert isinstance(project.created_at, datetime)
    assert isinstance(project.updated_at, datetime)


def test_create_project_without_description():
    """Test creating a Project without description."""
    project = Project.create('Test Project')

    assert project.name.value == 'Test Project'
    assert project.description.value is None


def test_create_project_validates_name():
    """Test that project creation validates name."""
    with pytest.raises(ValueError, match='Project name is required'):
        Project.create('')
    
    with pytest.raises(ValueError, match='Project name must be 100 characters or less'):
        Project.create('a' * 101)


def test_add_todo_to_project():
    """Test adding a Todo to a project."""
    project = Project.create('Test Project')
    title = TodoTitle('Test Todo')
    description = TodoDescriptionVO('Test Description')
    
    todo = project.add_todo(title, description)
    
    assert len(project.todos) == 1
    assert todo.title == title
    assert todo.description == description
    assert todo.project_id == project.id


def test_add_todo_with_dependencies():
    """Test adding a Todo with dependencies."""
    project = Project.create('Test Project')
    
    # Add first todo
    todo1 = project.add_todo(TodoTitle('Todo 1'))
    
    # Add second todo that depends on first
    todo2 = project.add_todo(TodoTitle('Todo 2'), dependencies=[todo1.id])
    
    assert len(project.todos) == 2
    assert todo2.dependencies.contains(todo1.id)


def test_add_todo_with_missing_dependency():
    """Test adding a Todo with non-existent dependency raises error."""
    project = Project.create('Test Project')
    missing_id = TodoId.generate()
    
    with pytest.raises(TodoDependencyNotFoundError):
        project.add_todo(TodoTitle('Todo with missing dep'), dependencies=[missing_id])


def test_add_todo_with_circular_dependency():
    """Test adding a Todo that would create circular dependency."""
    project = Project.create('Test Project')
    
    # Add first todo
    todo1 = project.add_todo(TodoTitle('Todo 1'))
    
    # Add second todo that depends on first
    todo2 = project.add_todo(TodoTitle('Todo 2'), dependencies=[todo1.id])
    
    # Try to make todo1 depend on todo2 (would create circular dependency)
    with pytest.raises(TodoCircularDependencyError):
        project.update_todo_by_id(todo1.id, dependencies=[todo2.id])


def test_remove_todo_from_project():
    """Test removing a Todo from a project."""
    project = Project.create('Test Project')
    todo = project.add_todo(TodoTitle('Test Todo'))
    
    project.remove_todo(todo.id)
    
    assert len(project.todos) == 0


def test_remove_todo_with_dependents():
    """Test removing a Todo that has dependents raises error."""
    project = Project.create('Test Project')
    
    # Add todos with dependency
    todo1 = project.add_todo(TodoTitle('Todo 1'))
    todo2 = project.add_todo(TodoTitle('Todo 2'), dependencies=[todo1.id])
    
    # Try to remove todo1 (it has dependents)
    with pytest.raises(TodoRemovalNotAllowedError):
        project.remove_todo(todo1.id)


def test_get_todo_from_project():
    """Test getting a Todo from a project."""
    project = Project.create('Test Project')
    todo = project.add_todo(TodoTitle('Test Todo'))
    
    retrieved_todo = project.get_todo(todo.id)
    
    assert retrieved_todo == todo


def test_get_nonexistent_todo_raises_error():
    """Test getting a non-existent Todo raises error."""
    project = Project.create('Test Project')
    missing_id = TodoId.generate()
    
    with pytest.raises(TodoNotFoundError):
        project.get_todo(missing_id)


def test_start_todo_in_project():
    """Test starting a Todo through the project."""
    project = Project.create('Test Project')
    todo = project.add_todo(TodoTitle('Test Todo'))
    
    project.start_todo_by_id(todo.id)
    
    retrieved_todo = project.get_todo(todo.id)
    assert retrieved_todo.status.value == 'in_progress'


def test_start_todo_with_incomplete_dependencies():
    """Test starting a Todo with incomplete dependencies raises error."""
    project = Project.create('Test Project')
    
    # Add todos with dependency
    todo1 = project.add_todo(TodoTitle('Todo 1'))
    todo2 = project.add_todo(TodoTitle('Todo 2'), dependencies=[todo1.id])
    
    # Try to start todo2 without completing todo1
    with pytest.raises(TodoDependencyNotCompletedError):
        project.start_todo_by_id(todo2.id)


def test_start_todo_with_completed_dependencies():
    """Test starting a Todo with all dependencies completed."""
    project = Project.create('Test Project')
    
    # Add todos with dependency
    todo1 = project.add_todo(TodoTitle('Todo 1'))
    todo2 = project.add_todo(TodoTitle('Todo 2'), dependencies=[todo1.id])
    
    # Complete todo1 first
    project.start_todo_by_id(todo1.id)
    project.complete_todo_by_id(todo1.id)
    
    # Now start todo2 should work
    project.start_todo_by_id(todo2.id)
    
    retrieved_todo = project.get_todo(todo2.id)
    assert retrieved_todo.status.value == 'in_progress'


def test_complete_todo_in_project():
    """Test completing a Todo through the project."""
    project = Project.create('Test Project')
    todo = project.add_todo(TodoTitle('Test Todo'))
    
    # Start then complete
    project.start_todo_by_id(todo.id)
    project.complete_todo_by_id(todo.id)
    
    retrieved_todo = project.get_todo(todo.id)
    assert retrieved_todo.status.value == 'completed'
    assert retrieved_todo.is_completed


def test_update_project_name():
    """Test updating project name."""
    project = Project.create('Original Name')
    
    project.update_name(ProjectName('Updated Name'))
    
    assert project.name.value == 'Updated Name'
    assert project.updated_at > project.created_at


def test_update_project_description():
    """Test updating project description."""
    project = Project.create('Test Project', 'Original Description')
    
    project.update_description(ProjectDescription('Updated Description'))
    
    assert project.description.value == 'Updated Description'
    assert project.updated_at > project.created_at


def test_project_equality():
    """Test Project equality comparison."""
    project_id = ProjectId.generate()
    current_time = datetime.now()
    
    # Create projects with same ID but different properties
    project1 = Project(
        id=project_id,
        name=ProjectName('Test Project'),
        description=ProjectDescription('Test Description'),
        todos={},
        created_at=current_time,
        updated_at=current_time
    )
    project2 = Project(
        id=project_id,
        name=ProjectName('Different Name'),
        description=ProjectDescription('Different Description'),
        todos={},
        created_at=current_time,
        updated_at=current_time
    )
    project3 = Project(
        id=ProjectId.generate(),
        name=ProjectName('Test Project'),
        description=ProjectDescription('Test Description'),
        todos={},
        created_at=current_time,
        updated_at=current_time
    )
    
    assert project1 == project2  # Same ID
    assert project1 != project3  # Different ID
    assert project1 != 'not a project'  # Different type


def test_add_todo_with_duplicate_title_raises_error():
    """Test adding a Todo with duplicate title raises error."""
    project = Project.create('Test Project')
    title = 'Duplicate Title'
    
    # Add first todo
    project.add_todo(TodoTitle(title))
    
    # Try to add second todo with same title
    with pytest.raises(DuplicateTodoTitleError) as exc_info:
        project.add_todo(TodoTitle(title))
    
    assert exc_info.value.title == title


def test_update_todo_with_duplicate_title_raises_error():
    """Test updating a Todo with duplicate title raises error."""
    project = Project.create('Test Project')
    
    # Add two todos
    todo1 = project.add_todo(TodoTitle('Todo 1'))
    todo2 = project.add_todo(TodoTitle('Todo 2'))
    
    # Try to update todo2 with todo1's title
    with pytest.raises(DuplicateTodoTitleError) as exc_info:
        project.update_todo_by_id(todo2.id, title=TodoTitle('Todo 1'))
    
    assert exc_info.value.title == 'Todo 1'


def test_update_todo_with_same_title_succeeds():
    """Test updating a Todo with its own title succeeds."""
    project = Project.create('Test Project')
    
    # Add todo
    todo = project.add_todo(TodoTitle('Original Title'))
    
    # Update with same title should succeed
    updated_todo = project.update_todo_by_id(todo.id, title=TodoTitle('Original Title'))
    
    assert updated_todo.title.value == 'Original Title'


def test_add_todo_exceeding_limit_raises_error():
    """Test adding more todos than the limit raises error."""
    project = Project.create('Test Project')
    
    # Mock the MAX_TODO_COUNT to a small number for testing
    original_max = Project.MAX_TODO_COUNT
    Project.MAX_TODO_COUNT = 2
    
    try:
        # Add todos up to the limit
        project.add_todo(TodoTitle('Todo 1'))
        project.add_todo(TodoTitle('Todo 2'))
        
        # Try to add one more
        with pytest.raises(TooManyTodosError) as exc_info:
            project.add_todo(TodoTitle('Todo 3'))
        
        assert exc_info.value.current_count == 2
        assert exc_info.value.max_count == 2
    finally:
        # Restore original limit
        Project.MAX_TODO_COUNT = original_max


def test_max_todo_count_constant():
    """Test that MAX_TODO_COUNT is set to expected value."""
    assert Project.MAX_TODO_COUNT == 1000


def test_project_with_fixed_clock():
    """Test Project behavior with FixedClock for predictable time testing."""
    fixed_time = datetime(2023, 1, 1, 12, 0, 0)
    clock = FixedClock(fixed_time)
    
    # Create project with fixed clock
    project = Project(
        id=ProjectId.generate(),
        name=ProjectName('Test Project'),
        description=ProjectDescription('Test Description'),
        clock=clock
    )
    
    # All timestamps should use the fixed time
    assert project.created_at == fixed_time
    assert project.updated_at == fixed_time
    
    # Update operations should also use fixed time
    project.update_name(ProjectName('Updated Name'))
    assert project.updated_at == fixed_time
    
    # Add todo should also use fixed time
    todo = project.add_todo(TodoTitle('Test Todo'))
    assert todo.created_at == fixed_time
    assert todo.updated_at == fixed_time


def test_todo_completion_with_fixed_clock():
    """Test Todo completion timestamp with FixedClock."""
    fixed_time = datetime(2023, 6, 15, 14, 30, 45)
    clock = FixedClock(fixed_time)
    
    project = Project(
        id=ProjectId.generate(),
        name=ProjectName('Test Project'),
        clock=clock
    )
    
    # Add and complete a todo
    todo = project.add_todo(TodoTitle('Test Todo'))
    project.start_todo_by_id(todo.id)
    project.complete_todo_by_id(todo.id)
    
    # All operations should use the same fixed time
    completed_todo = project.get_todo(todo.id)
    assert completed_todo.created_at == fixed_time
    assert completed_todo.updated_at == fixed_time
    assert completed_todo.completed_at == fixed_time
