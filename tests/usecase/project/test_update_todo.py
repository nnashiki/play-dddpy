"""Tests for UpdateTodoThroughProjectUseCase with UoW."""

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
from dddpy.dto.todo import TodoUpdateDto
from dddpy.usecase.project.create_project_usecase import (
    new_create_project_usecase,
)
from dddpy.usecase.project.add_todo_to_project_usecase import (
    new_add_todo_to_project_usecase,
)
from dddpy.usecase.project.update_todo_through_project_usecase import (
    UpdateTodoThroughProjectUseCase,
    new_update_todo_through_project_usecase,
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
def update_todo_usecase(test_uow):
    """Create UpdateTodoThroughProjectUseCase for testing."""
    return new_update_todo_through_project_usecase(test_uow)


@pytest.fixture
def test_project_with_todo(test_session_factory):
    """Create a test project with a todo for update operations."""
    class TestUoW(SqlAlchemyUnitOfWork):
        def __enter__(self):
            self.session = test_session_factory()
            self.event_publisher = get_event_publisher()
            self.event_publisher.clear_events()
            return self

    # Create project
    uow1 = TestUoW()
    create_usecase = new_create_project_usecase(uow1)
    
    project_dto = ProjectCreateDto(
        name='Test Project for Update',
        description='A project for testing todo updates'
    )
    project = create_usecase.execute(project_dto)

    # Add todo to project
    uow2 = TestUoW()
    add_todo_usecase = new_add_todo_to_project_usecase(uow2)
    
    todo_dto = AddTodoToProjectDto(
        title='Original Todo Title',
        description='Original description',
        dependencies=[]
    )
    todo = add_todo_usecase.execute(project.id, todo_dto)

    return {
        'project': project,
        'todo': todo
    }


class TestUpdateTodoThroughProjectUseCase:
    """Test cases for UpdateTodoThroughProjectUseCase."""

    def test_update_todo_successfully_saves_to_outbox(
        self, update_todo_usecase: UpdateTodoThroughProjectUseCase, 
        test_project_with_todo, test_session_factory
    ):
        """Test successful todo update saves event to outbox."""
        project = test_project_with_todo['project']
        todo = test_project_with_todo['todo']

        # Before: Check current outbox entries
        with test_session_factory() as session:
            outbox_count_before = session.query(OutboxModel).count()

        # Create update DTO
        update_dto = TodoUpdateDto(
            title='Updated Todo Title',
            description='Updated description',
            dependencies=[]
        )

        # Execute UseCase
        result = update_todo_usecase.execute(project.id, todo.id, update_dto)

        # Verify todo was updated successfully
        assert result.title == 'Updated Todo Title'
        assert result.description == 'Updated description'
        assert result.id == todo.id
        assert result.dependencies == []

        # After: Check outbox has new events
        with test_session_factory() as session:
            outbox_entries = session.query(OutboxModel).all()
            # Should have original events + todo updated event
            assert len(outbox_entries) >= outbox_count_before + 1

            # Find todo updated event
            todo_updated_events = [e for e in outbox_entries if e.event_type == 'TodoUpdated']
            assert len(todo_updated_events) == 1

            todo_event = todo_updated_events[0]
            assert todo_event.published is False
            assert todo_event.created_at is not None

            # Verify payload contains expected data
            payload = todo_event.payload
            assert payload['event_type'] == 'TodoUpdated'
            assert payload['title'] == 'Updated Todo Title'
            assert payload['description'] == 'Updated description'

    def test_update_todo_in_nonexistent_project_fails_and_rolls_back_outbox(
        self, update_todo_usecase: UpdateTodoThroughProjectUseCase, 
        test_project_with_todo, test_session_factory
    ):
        """Test updating todo in non-existent project fails and rolls back outbox."""
        todo = test_project_with_todo['todo']

        # Before: Check current outbox count
        with test_session_factory() as session:
            outbox_count_before = session.query(OutboxModel).count()

        # Create update DTO
        update_dto = TodoUpdateDto(
            title='This Should Fail',
            description='Update attempt on non-existent project',
            dependencies=[]
        )

        # Use non-existent project ID
        fake_project_id = str(uuid4())

        # Should raise ProjectNotFoundError
        with pytest.raises(ProjectNotFoundError):
            update_todo_usecase.execute(fake_project_id, todo.id, update_dto)

        # After: Check outbox count remains the same (rollback worked)
        with test_session_factory() as session:
            outbox_count_after = session.query(OutboxModel).count()
            assert outbox_count_after == outbox_count_before  # No new events added

    def test_update_todo_with_dependencies_saves_to_outbox(
        self, test_session_factory
    ):
        """Test updating todo with dependencies saves complete event data to outbox."""
        # Create project with multiple todos
        class TestUoW(SqlAlchemyUnitOfWork):
            def __enter__(self):
                self.session = test_session_factory()
                self.event_publisher = get_event_publisher()
                self.event_publisher.clear_events()
                return self

        # Create project
        uow1 = TestUoW()
        create_usecase = new_create_project_usecase(uow1)
        project = create_usecase.execute(ProjectCreateDto(
            name='Project with Dependencies',
            description='For testing dependency updates'
        ))

        # Create first todo
        uow2 = TestUoW()
        add_todo_usecase1 = new_add_todo_to_project_usecase(uow2)
        todo1 = add_todo_usecase1.execute(project.id, AddTodoToProjectDto(
            title='Dependency Todo',
            description='Todo to be depended upon',
            dependencies=[]
        ))

        # Create second todo
        uow3 = TestUoW()
        add_todo_usecase2 = new_add_todo_to_project_usecase(uow3)
        todo2 = add_todo_usecase2.execute(project.id, AddTodoToProjectDto(
            title='Main Todo',
            description='Todo to be updated with dependencies',
            dependencies=[]
        ))

        # Update second todo to depend on first todo
        uow4 = TestUoW()
        update_usecase = new_update_todo_through_project_usecase(uow4)
        
        update_dto = TodoUpdateDto(
            title='Updated Main Todo',
            description='Now depends on first todo',
            dependencies=[todo1.id]
        )
        
        result = update_usecase.execute(project.id, todo2.id, update_dto)

        # Verify update was successful
        assert result.title == 'Updated Main Todo'
        assert result.description == 'Now depends on first todo'
        assert result.dependencies == [todo1.id]

        # Verify outbox entry for todo update
        with test_session_factory() as session:
            todo_updated_events = session.query(OutboxModel).filter_by(event_type='TodoUpdated').all()
            assert len(todo_updated_events) == 1

            update_event = todo_updated_events[0]
            payload = update_event.payload
            assert payload['title'] == 'Updated Main Todo'
            assert payload['description'] == 'Now depends on first todo'

    def test_partial_todo_update_saves_to_outbox(
        self, update_todo_usecase: UpdateTodoThroughProjectUseCase,
        test_project_with_todo, test_session_factory
    ):
        """Test partial todo update (only title) saves event to outbox."""
        project = test_project_with_todo['project']
        todo = test_project_with_todo['todo']

        # Update only title
        update_dto = TodoUpdateDto(
            title='Only Title Updated',
            description=None,  # Keep original
            dependencies=None  # Keep original
        )

        result = update_todo_usecase.execute(project.id, todo.id, update_dto)

        # Verify partial update
        assert result.title == 'Only Title Updated'
        assert result.description == 'Original description'  # Unchanged
        assert result.dependencies == []  # Unchanged

        # Verify outbox entry
        with test_session_factory() as session:
            todo_updated_events = session.query(OutboxModel).filter_by(event_type='TodoUpdated').all()
            assert len(todo_updated_events) == 1

            update_event = todo_updated_events[0]
            payload = update_event.payload
            assert payload['title'] == 'Only Title Updated'

    def test_error_during_save_rolls_back_outbox(
        self, test_project_with_todo, test_session_factory
    ):
        """Test that errors during save operation roll back outbox entries."""
        project = test_project_with_todo['project']
        todo = test_project_with_todo['todo']

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
                raise RuntimeError('Simulated database error during todo update')

        # Get initial outbox count
        with test_session_factory() as session:
            outbox_count_before = session.query(OutboxModel).count()

        failing_uow = FailingUoW()
        usecase = new_update_todo_through_project_usecase(failing_uow)

        update_dto = TodoUpdateDto(
            title='Failing Update',
            description='This should fail',
            dependencies=[]
        )

        # Should raise the simulated error
        with pytest.raises(RuntimeError, match='Simulated database error during todo update'):
            usecase.execute(project.id, todo.id, update_dto)

        # Verify no new outbox entries were saved due to rollback
        with test_session_factory() as session:
            outbox_count_after = session.query(OutboxModel).count()
            assert outbox_count_after == outbox_count_before  # No new events

    def test_multiple_todo_updates_create_multiple_outbox_entries(
        self, test_project_with_todo, test_session_factory
    ):
        """Test multiple todo updates create multiple outbox entries."""
        project = test_project_with_todo['project']
        todo = test_project_with_todo['todo']

        update_data = [
            ('First Update', 'First update description'),
            ('Second Update', 'Second update description'),
            ('Third Update', 'Third update description'),
        ]

        initial_todo_updated_count = 0
        with test_session_factory() as session:
            initial_todo_updated_count = session.query(OutboxModel).filter_by(event_type='TodoUpdated').count()

        for i, (title, description) in enumerate(update_data, 1):
            # Create new UoW for each update
            class TestUoW(SqlAlchemyUnitOfWork):
                def __enter__(self):
                    self.session = test_session_factory()
                    self.event_publisher = get_event_publisher()
                    self.event_publisher.clear_events()
                    return self

            uow = TestUoW()
            usecase = new_update_todo_through_project_usecase(uow)

            update_dto = TodoUpdateDto(
                title=title,
                description=description,
                dependencies=[]
            )
            result = usecase.execute(project.id, todo.id, update_dto)

            assert result.title == title
            assert result.description == description

            # Verify outbox event count increases with each update
            with test_session_factory() as session:
                todo_updated_count = session.query(OutboxModel).filter_by(event_type='TodoUpdated').count()
                assert todo_updated_count == initial_todo_updated_count + i

        # Final verification: all updates are in outbox
        with test_session_factory() as session:
            todo_updated_events = session.query(OutboxModel).filter_by(event_type='TodoUpdated').all()
            assert len(todo_updated_events) == len(update_data)

            # Verify all update titles are present in payloads
            saved_titles = {event.payload['title'] for event in todo_updated_events}
            expected_titles = {title for title, _ in update_data}
            assert saved_titles == expected_titles

            # Verify all entries are unpublished
            for event in todo_updated_events:
                assert event.published is False
                assert event.event_type == 'TodoUpdated'
