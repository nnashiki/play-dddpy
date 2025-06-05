"""Tests for AddTodoToProjectWithUoWUseCase."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from dddpy.domain.shared.events import get_event_publisher
from dddpy.domain.project.exceptions import ProjectNotFoundError
from dddpy.infrastructure.sqlite.database import Base
from dddpy.infrastructure.sqlite.uow import SqlAlchemyUnitOfWork
from dddpy.infrastructure.sqlite.outbox.outbox_model import OutboxModel
from dddpy.dto.project import ProjectCreateDto, AddTodoToProjectDto
from dddpy.usecase.project.create_project_usecase import (
    new_create_project_usecase,
)
from dddpy.usecase.project.add_todo_to_project_usecase import (
    AddTodoToProjectUseCase,
    new_add_todo_to_project_usecase,
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
def add_todo_usecase(test_uow):
    """Create AddTodoToProjectUseCase for testing."""
    return new_add_todo_to_project_usecase(test_uow)


@pytest.fixture
def test_project(test_session_factory):
    """Create a test project for todo operations."""
    class TestUoW(SqlAlchemyUnitOfWork):
        def __enter__(self):
            self.session = test_session_factory()
            self.event_publisher = get_event_publisher()
            self.event_publisher.clear_events()
            return self

    uow = TestUoW()
    create_usecase = new_create_project_usecase(uow)
    
    dto = ProjectCreateDto(
        name='Test Project for Todos',
        description='A project for testing todo operations'
    )
    
    return create_usecase.execute(dto)


class TestAddTodoToProjectUseCase:
    """Test cases for AddTodoToProjectUseCase."""

    def test_add_todo_successfully_saves_to_outbox(
        self, add_todo_usecase: AddTodoToProjectUseCase, test_project, test_session_factory
    ):
        """Test successful todo addition saves event to outbox."""
        # Before: Check current outbox entries
        with test_session_factory() as session:
            outbox_count_before = session.query(OutboxModel).count()

        # Create todo DTO
        dto = AddTodoToProjectDto(
            title='Test Todo',
            description='A test todo item',
            dependencies=[]
        )

        # Execute UseCase
        result = add_todo_usecase.execute(test_project.id, dto)

        # Verify todo was created successfully
        assert result.title == 'Test Todo'
        assert result.description == 'A test todo item'
        assert result.id is not None
        assert result.status == 'not_started'
        assert result.dependencies == []

        # After: Check outbox has new events (project creation + todo creation)
        with test_session_factory() as session:
            outbox_entries = session.query(OutboxModel).all()
            # Should have project creation event + todo creation event
            assert len(outbox_entries) >= outbox_count_before + 1

            # Find todo creation event
            todo_events = [e for e in outbox_entries if e.event_type == 'TodoCreated']
            assert len(todo_events) == 1

            todo_event = todo_events[0]
            assert todo_event.published is False
            assert todo_event.created_at is not None

            # Verify payload contains expected data
            payload = todo_event.payload
            assert payload['event_type'] == 'TodoCreated'
            assert payload['title'] == 'Test Todo'
            assert payload['description'] == 'A test todo item'

    def test_add_todo_to_nonexistent_project_fails_and_rolls_back_outbox(
        self, add_todo_usecase: AddTodoToProjectUseCase, test_session_factory
    ):
        """Test adding todo to non-existent project fails and rolls back outbox."""
        # Before: Check current outbox count
        with test_session_factory() as session:
            outbox_count_before = session.query(OutboxModel).count()

        # Create todo DTO
        dto = AddTodoToProjectDto(
            title='Todo for Non-existent Project',
            description='This should fail',
            dependencies=[]
        )

        # Use non-existent project ID
        fake_project_id = str(uuid4())

        # Should raise ProjectNotFoundError
        with pytest.raises(ProjectNotFoundError):
            add_todo_usecase.execute(fake_project_id, dto)

        # After: Check outbox count remains the same (rollback worked)
        with test_session_factory() as session:
            outbox_count_after = session.query(OutboxModel).count()
            assert outbox_count_after == outbox_count_before  # No new events added

    def test_multiple_todos_create_multiple_outbox_entries(
        self, test_project, test_session_factory
    ):
        """Test adding multiple todos creates multiple outbox entries."""
        todo_data = [
            ('Todo 1', 'First todo'),
            ('Todo 2', 'Second todo'),
            ('Todo 3', 'Third todo'),
        ]

        created_todos = []

        for i, (title, description) in enumerate(todo_data, 1):
            # Create new UoW for each todo
            class TestUoW(SqlAlchemyUnitOfWork):
                def __enter__(self):
                    self.session = test_session_factory()
                    self.event_publisher = get_event_publisher()
                    self.event_publisher.clear_events()
                    return self

            uow = TestUoW()
            usecase = new_add_todo_to_project_usecase(uow)

            dto = AddTodoToProjectDto(
                title=title,
                description=description,
                dependencies=[]
            )
            result = usecase.execute(test_project.id, dto)

            created_todos.append(result)
            assert result.title == title
            assert result.description == description

        # Final verification: check todo events in outbox
        with test_session_factory() as session:
            todo_events = session.query(OutboxModel).filter_by(event_type='TodoCreated').all()
            assert len(todo_events) == 3

            # Verify all todo titles are present in payloads
            saved_titles = {event.payload['title'] for event in todo_events}
            expected_titles = {title for title, _ in todo_data}
            assert saved_titles == expected_titles

            # Verify all entries are unpublished
            for event in todo_events:
                assert event.published is False
                assert event.event_type == 'TodoCreated'

    def test_add_todo_with_dependencies_saves_to_outbox(
        self, test_project, test_session_factory
    ):
        """Test adding todo with dependencies saves complete event data to outbox."""
        # First create a todo to depend on
        class TestUoW(SqlAlchemyUnitOfWork):
            def __enter__(self):
                self.session = test_session_factory()
                self.event_publisher = get_event_publisher()
                self.event_publisher.clear_events()
                return self

        uow1 = TestUoW()
        usecase1 = new_add_todo_to_project_usecase(uow1)

        dependency_dto = AddTodoToProjectDto(
            title='Dependency Todo',
            description='Todo to be depended upon',
            dependencies=[]
        )
        dependency_todo = usecase1.execute(test_project.id, dependency_dto)

        # Now create a todo that depends on the first one
        uow2 = TestUoW()
        usecase2 = new_add_todo_to_project_usecase(uow2)

        dependent_dto = AddTodoToProjectDto(
            title='Dependent Todo',
            description='Todo with dependencies',
            dependencies=[dependency_todo.id]
        )
        dependent_todo = usecase2.execute(test_project.id, dependent_dto)

        # Verify dependent todo was created with dependencies
        assert dependent_todo.title == 'Dependent Todo'
        assert dependent_todo.dependencies == [dependency_todo.id]

        # Verify outbox entries for both todos
        with test_session_factory() as session:
            todo_events = session.query(OutboxModel).filter_by(event_type='TodoCreated').all()
            assert len(todo_events) == 2

            # Find the dependent todo event
            dependent_events = [
                e for e in todo_events 
                if e.payload.get('title') == 'Dependent Todo'
            ]
            assert len(dependent_events) == 1

            dependent_event = dependent_events[0]
            payload = dependent_event.payload
            assert payload['title'] == 'Dependent Todo'
            assert payload['description'] == 'Todo with dependencies'

    def test_error_during_save_rolls_back_outbox(self, test_project, test_session_factory):
        """Test that errors during save operation roll back outbox entries."""

        # Create a UoW that will fail during flush
        class FailingUoW(SqlAlchemyUnitOfWork):
            def __enter__(self):
                self.session = test_session_factory()
                self.event_publisher = get_event_publisher()
                self.event_publisher.clear_events()
                return self

            def _flush_outbox(self):
                # Call parent to add events to session
                super()._flush_outbox()
                # Then raise an exception to simulate DB error
                raise RuntimeError('Simulated database error during todo save')

        # Get initial outbox count
        with test_session_factory() as session:
            outbox_count_before = session.query(OutboxModel).count()

        failing_uow = FailingUoW()
        usecase = new_add_todo_to_project_usecase(failing_uow)

        dto = AddTodoToProjectDto(
            title='Failing Todo',
            description='This should fail',
            dependencies=[]
        )

        # Should raise the simulated error
        with pytest.raises(RuntimeError, match='Simulated database error during todo save'):
            usecase.execute(test_project.id, dto)

        # Verify no new outbox entries were saved due to rollback
        with test_session_factory() as session:
            outbox_count_after = session.query(OutboxModel).count()
            assert outbox_count_after == outbox_count_before  # No new events
