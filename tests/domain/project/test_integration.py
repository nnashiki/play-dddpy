"""Simple test for basic Project functionality to verify our changes work."""

import pytest
from dddpy.domain.project.entities.project import Project
from dddpy.domain.project.value_objects import ProjectName, ProjectDescription
from dddpy.domain.todo.value_objects import TodoTitle


def test_project_basic_functionality():
    """Test that basic Project functionality works with our changes."""
    # Create project
    project = Project.create('Test Project', 'Test Description')

    # Verify project properties
    assert project.name.value == 'Test Project'
    assert project.description.value == 'Test Description'
    assert len(project.todos) == 0

    # Add a todo
    todo = project.add_todo(TodoTitle('Test Todo'))
    assert len(project.todos) == 1
    assert todo.title.value == 'Test Todo'

    # Start and complete todo
    project.start_todo_by_id(todo.id)
    retrieved_todo = project.get_todo(todo.id)
    assert retrieved_todo.status.value == 'in_progress'

    project.complete_todo_by_id(todo.id)
    retrieved_todo = project.get_todo(todo.id)
    assert retrieved_todo.status.value == 'completed'
    assert retrieved_todo.is_completed


def test_project_value_objects():
    """Test that Value Objects work correctly."""
    # Test ProjectName
    name = ProjectName('Test Name')
    assert name.value == 'Test Name'

    # Test ProjectDescription
    desc = ProjectDescription('Test Description')
    assert desc.value == 'Test Description'

    # Test None description
    desc_none = ProjectDescription(None)
    assert desc_none.value is None


def test_project_name_validation():
    """Test that ProjectName validation works."""
    # Empty name should raise error
    with pytest.raises(ValueError):
        ProjectName('')

    # Too long name should raise error
    with pytest.raises(ValueError):
        ProjectName('a' * 101)


def test_project_description_validation():
    """Test that ProjectDescription validation works."""
    # Too long description should raise error
    with pytest.raises(ValueError):
        ProjectDescription('a' * 1001)
