"""Test cases for FindTodoThroughProjectUseCase with Unit of Work."""

import time
from uuid import uuid4

import pytest

from dddpy.domain.project.entities.project import Project
from dddpy.domain.project.exceptions import ProjectNotFoundError
from dddpy.domain.project.value_objects import ProjectId
from dddpy.domain.todo.entities.todo import Todo
from dddpy.domain.todo.exceptions import TodoNotFoundError
from dddpy.domain.todo.value_objects import TodoId, TodoTitle
from dddpy.infrastructure.sqlite.project.project_repository import new_project_repository
from dddpy.infrastructure.sqlite.uow import SqlAlchemyUnitOfWork
from dddpy.usecase.todo.find_todo_usecase import (
    FindTodoThroughProjectUseCaseImpl,
    new_find_todo_usecase,
)


class TestFindTodoThroughProjectUseCase:
    """Test cases for UoW-based FindTodoThroughProjectUseCase."""

    def test_find_todo_successfully_retrieves_todo(self):
        """Test successfully finding a todo through project."""
        # Arrange
        uow = SqlAlchemyUnitOfWork()
        usecase = new_find_todo_usecase(uow)

        # Create test data
        with uow as session_uow:
            if session_uow.session is None:
                raise RuntimeError("Session not initialized")
            
            project_repo = new_project_repository(session_uow.session)
            project = Project.create("Test Project")
            todo = project.add_todo(TodoTitle("Test Todo"))
            project_repo.save(project)

        # Act
        result = usecase.execute(str(project.id.value), str(todo.id.value))

        # Assert
        assert result.id == str(todo.id.value)
        assert result.title == "Test Todo"
        assert result.status == "not_started"
        # Description may be None for new todos
        assert result.dependencies == []

    def test_find_todo_raises_project_not_found_error(self):
        """Test finding todo when project doesn't exist."""
        # Arrange
        uow = SqlAlchemyUnitOfWork()
        usecase = new_find_todo_usecase(uow)
        nonexistent_project_id = str(uuid4())
        nonexistent_todo_id = str(uuid4())

        # Act & Assert
        with pytest.raises(ProjectNotFoundError):
            usecase.execute(nonexistent_project_id, nonexistent_todo_id)

    def test_find_todo_raises_todo_not_found_error(self):
        """Test finding todo when todo doesn't exist in project."""
        # Arrange
        uow = SqlAlchemyUnitOfWork()
        usecase = new_find_todo_usecase(uow)

        # Create project without the target todo
        with uow as session_uow:
            if session_uow.session is None:
                raise RuntimeError("Session not initialized")
            
            project_repo = new_project_repository(session_uow.session)
            project = Project.create("Test Project")
            project_repo.save(project)

        nonexistent_todo_id = str(uuid4())

        # Act & Assert
        with pytest.raises(TodoNotFoundError):
            usecase.execute(str(project.id.value), nonexistent_todo_id)

    def test_find_todo_does_not_create_outbox_entries(self):
        """Test that read operation does not create outbox entries."""
        # Arrange
        uow = SqlAlchemyUnitOfWork()
        usecase = new_find_todo_usecase(uow)

        # Create test data
        with uow as session_uow:
            if session_uow.session is None:
                raise RuntimeError("Session not initialized")
            
            project_repo = new_project_repository(session_uow.session)
            project = Project.create("Test Project")
            todo = project.add_todo(TodoTitle("Test Todo"))
            project_repo.save(project)

        # Count outbox entries before
        from sqlalchemy import text
        with uow as session_uow:
            if session_uow.session is None:
                raise RuntimeError("Session not initialized")
            outbox_count_before = session_uow.session.execute(
                text("SELECT COUNT(*) FROM outbox")
            ).scalar() or 0

        # Act
        usecase.execute(str(project.id.value), str(todo.id.value))

        # Count outbox entries after
        with uow as session_uow:
            if session_uow.session is None:
                raise RuntimeError("Session not initialized")
            outbox_count_after = session_uow.session.execute(
                text("SELECT COUNT(*) FROM outbox")
            ).scalar() or 0

        # Assert - no new outbox entries should be created
        assert outbox_count_after == outbox_count_before

    def test_find_todo_handles_database_errors_gracefully(self):
        """Test error handling when database operations fail."""
        # Arrange
        uow = SqlAlchemyUnitOfWork()
        usecase = new_find_todo_usecase(uow)
        invalid_project_id = "invalid-uuid"
        invalid_todo_id = "invalid-uuid"

        # Act & Assert
        with pytest.raises(ValueError):  # UUID parsing error
            usecase.execute(invalid_project_id, invalid_todo_id)

    def test_find_todo_maintains_data_consistency(self):
        """Test that finding todo maintains data consistency."""
        # Arrange
        uow = SqlAlchemyUnitOfWork()
        usecase = new_find_todo_usecase(uow)

        # Create test data with multiple todos
        with uow as session_uow:
            if session_uow.session is None:
                raise RuntimeError("Session not initialized")
            
            project_repo = new_project_repository(session_uow.session)
            project = Project.create("Test Project")
            todo1 = project.add_todo(TodoTitle("Todo 1"))
            todo2 = project.add_todo(TodoTitle("Todo 2"))
            todo3 = project.add_todo(TodoTitle("Todo 3"))
            project_repo.save(project)

        # Act - find different todos
        result1 = usecase.execute(str(project.id.value), str(todo1.id.value))
        result2 = usecase.execute(str(project.id.value), str(todo2.id.value))
        result3 = usecase.execute(str(project.id.value), str(todo3.id.value))

        # Assert - each result should be correct and independent
        assert result1.id == str(todo1.id.value)
        assert result1.title == "Todo 1"
        assert result2.id == str(todo2.id.value)
        assert result2.title == "Todo 2"
        assert result3.id == str(todo3.id.value)
        assert result3.title == "Todo 3"

        # Verify independence
        assert result1.id != result2.id != result3.id
