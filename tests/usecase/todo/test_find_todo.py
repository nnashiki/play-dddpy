"""Tests for FindTodoThroughProjectUseCase."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dddpy.domain.shared.events import get_event_publisher
from dddpy.domain.project.exceptions import ProjectNotFoundError
from dddpy.domain.todo.exceptions import TodoNotFoundError
from dddpy.infrastructure.sqlite.database import Base
from dddpy.infrastructure.sqlite.uow import SqlAlchemyUnitOfWork
from dddpy.infrastructure.sqlite.outbox.outbox_model import OutboxModel
from dddpy.dto.project import ProjectCreateDto, AddTodoToProjectDto
from dddpy.usecase.project.create_project_usecase import (
    CreateProjectUseCase,
    new_create_project_usecase,
)
from dddpy.usecase.project.add_todo_to_project_usecase import (
    AddTodoToProjectUseCase,
    new_add_todo_to_project_usecase,
)
from dddpy.usecase.todo.find_todo_usecase import (
    FindTodoThroughProjectUseCase,
    new_find_todo_usecase,
)


@pytest.fixture
def test_engine():
    """Create in-memory SQLite engine for testing."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_session_factory(test_engine):
    """Create session factory for testing."""
    return sessionmaker(bind=test_engine)


@pytest.fixture
def test_uow(test_session_factory):
    """Create test Unit of Work."""

    class TestUoW(SqlAlchemyUnitOfWork):
        def __enter__(self):
            self.session = test_session_factory()
            self.event_publisher = get_event_publisher()
            self.event_publisher.clear_events()
            return self

    return TestUoW()


@pytest.fixture
def create_project_usecase(test_uow):
    """Create CreateProjectUseCase for testing."""
    return new_create_project_usecase(test_uow)


@pytest.fixture
def add_todo_usecase(test_uow):
    """Create AddTodoToProjectUseCase for testing."""
    return new_add_todo_to_project_usecase(test_uow)


@pytest.fixture
def find_todo_usecase(test_uow):
    """Create FindTodoThroughProjectUseCase for testing."""
    return new_find_todo_usecase(test_uow)


class TestFindTodoThroughProjectUseCase:
    """Test cases for FindTodoThroughProjectUseCase."""

    def test_find_todo_through_project_success(
        self,
        create_project_usecase: CreateProjectUseCase,
        add_todo_usecase: AddTodoToProjectUseCase,
        find_todo_usecase: FindTodoThroughProjectUseCase,
        test_session_factory,
    ):
        """Test finding a todo through project successfully."""
        # Create project
        project_dto = ProjectCreateDto(
            name='Find Todo Test Project',
            description='Project for testing todo finding',
        )
        created_project = create_project_usecase.execute(project_dto)

        # Add todo to project
        todo_dto = AddTodoToProjectDto(
            title='Test Todo',
            description='This todo will be found',
            dependencies=[],
        )
        added_todo = add_todo_usecase.execute(created_project.id, todo_dto)

        # Find the todo
        result = find_todo_usecase.execute(created_project.id, added_todo.id)

        # Verify the result
        assert result.id == added_todo.id
        assert result.title == 'Test Todo'
        assert result.description == 'This todo will be found'
        assert result.status == 'not_started'
        assert result.project_id == created_project.id
        assert result.dependencies == []

    def test_find_todo_project_not_found(
        self, find_todo_usecase: FindTodoThroughProjectUseCase
    ):
        """Test finding a todo when project doesn't exist raises ProjectNotFoundError."""
        nonexistent_project_id = '550e8400-e29b-41d4-a716-446655440000'
        nonexistent_todo_id = '550e8400-e29b-41d4-a716-446655440001'

        with pytest.raises(ProjectNotFoundError):
            find_todo_usecase.execute(nonexistent_project_id, nonexistent_todo_id)

    def test_find_todo_not_found(
        self,
        create_project_usecase: CreateProjectUseCase,
        find_todo_usecase: FindTodoThroughProjectUseCase,
    ):
        """Test finding a nonexistent todo raises TodoNotFoundError."""
        # Create project
        project_dto = ProjectCreateDto(
            name='Project for Nonexistent Todo',
            description='Project for testing todo not found',
        )
        created_project = create_project_usecase.execute(project_dto)

        nonexistent_todo_id = '550e8400-e29b-41d4-a716-446655440001'

        with pytest.raises(TodoNotFoundError):
            find_todo_usecase.execute(created_project.id, nonexistent_todo_id)

    def test_find_todo_does_not_create_outbox_entries(
        self,
        create_project_usecase: CreateProjectUseCase,
        add_todo_usecase: AddTodoToProjectUseCase,
        find_todo_usecase: FindTodoThroughProjectUseCase,
        test_session_factory,
    ):
        """Test that finding a todo does not create any outbox entries (Read operation)."""
        # Create project and todo
        project_dto = ProjectCreateDto(
            name='Outbox Test Project',
            description='Project for testing outbox behavior',
        )
        created_project = create_project_usecase.execute(project_dto)

        todo_dto = AddTodoToProjectDto(
            title='Outbox Test Todo',
            description='Todo for testing outbox behavior',
            dependencies=[],
        )
        added_todo = add_todo_usecase.execute(created_project.id, todo_dto)

        # Count outbox entries before find operation
        with test_session_factory() as session:
            outbox_count_before = session.query(OutboxModel).count()
            assert outbox_count_before == 3  # ProjectCreated + TodoCreated + TodoAddedToProject

        # Find the todo (Read operation)
        find_todo_usecase.execute(created_project.id, added_todo.id)

        # Count outbox entries after find operation
        with test_session_factory() as session:
            outbox_count_after = session.query(OutboxModel).count()
            assert outbox_count_after == outbox_count_before  # Should be the same
            assert outbox_count_after == 3

    def test_find_todo_error_handling(
        self,
        create_project_usecase: CreateProjectUseCase,
        test_session_factory,
    ):
        """Test error handling during find operation."""
        # Create project
        project_dto = ProjectCreateDto(
            name='Error Test Project',
            description='Project for testing error handling',
        )
        created_project = create_project_usecase.execute(project_dto)

        # Create UoW that will behave normally but test error path
        class TestUoW(SqlAlchemyUnitOfWork):
            def __enter__(self):
                self.session = test_session_factory()
                self.event_publisher = get_event_publisher()
                self.event_publisher.clear_events()
                return self

        uow = TestUoW()
        find_usecase = new_find_todo_usecase(uow)

        # Try to find nonexistent todo
        nonexistent_todo_id = '550e8400-e29b-41d4-a716-446655440001'

        # Should raise TodoNotFoundError properly
        with pytest.raises(TodoNotFoundError):
            find_usecase.execute(created_project.id, nonexistent_todo_id)

        # Verify no outbox pollution occurred
        with test_session_factory() as session:
            outbox_count = session.query(OutboxModel).count()
            assert outbox_count == 1  # Only ProjectCreated event

    def test_find_todo_data_consistency(
        self,
        create_project_usecase: CreateProjectUseCase,
        add_todo_usecase: AddTodoToProjectUseCase,
        find_todo_usecase: FindTodoThroughProjectUseCase,
    ):
        """Test that find operation returns consistent data."""
        # Create project
        project_dto = ProjectCreateDto(
            name='Consistency Test Project',
            description='Testing data consistency',
        )
        created_project = create_project_usecase.execute(project_dto)

        # Add todo with dependencies
        dependency_dto = AddTodoToProjectDto(
            title='Dependency Todo',
            description='This is a dependency',
            dependencies=[],
        )
        dependency_todo = add_todo_usecase.execute(created_project.id, dependency_dto)

        main_dto = AddTodoToProjectDto(
            title='Main Todo',
            description='This todo has dependencies',
            dependencies=[dependency_todo.id],
        )
        main_todo = add_todo_usecase.execute(created_project.id, main_dto)

        # Find the main todo
        result = find_todo_usecase.execute(created_project.id, main_todo.id)

        # Verify all data is consistent
        assert result.id == main_todo.id
        assert result.title == 'Main Todo'
        assert result.description == 'This todo has dependencies'
        assert result.project_id == created_project.id
        assert len(result.dependencies) == 1
        assert result.dependencies[0] == dependency_todo.id
        assert result.status == 'not_started'
