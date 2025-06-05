"""Tests for StartTodoThroughProjectUseCase."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dddpy.domain.shared.events import get_event_publisher
from dddpy.domain.project.exceptions import ProjectNotFoundError
from dddpy.domain.todo.exceptions import TodoDependencyNotCompletedError, TodoNotFoundError, TodoAlreadyStartedError
from dddpy.infrastructure.sqlite.database import Base
from dddpy.infrastructure.sqlite.uow import SqlAlchemyUnitOfWork
from dddpy.infrastructure.sqlite.outbox.outbox_model import OutboxModel
from dddpy.dto.project import ProjectCreateDto
from dddpy.dto.project import AddTodoToProjectDto
from dddpy.usecase.project.create_project_usecase import (
    CreateProjectUseCase,
    new_create_project_usecase,
)
from dddpy.usecase.project.add_todo_to_project_usecase import (
    AddTodoToProjectUseCase,
    new_add_todo_to_project_usecase,
)
from dddpy.usecase.project.start_todo_through_project_usecase import (
    StartTodoThroughProjectUseCase,
    new_start_todo_through_project_usecase,
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
def start_todo_usecase(test_uow):
    """Create StartTodoThroughProjectUseCase for testing."""
    return new_start_todo_through_project_usecase(test_uow)


class TestStartTodoThroughProjectUseCase:
    """Test cases for StartTodoThroughProjectUseCase."""

    def test_start_todo_successfully_saves_to_outbox(
        self,
        create_project_usecase: CreateProjectUseCase,
        add_todo_usecase: AddTodoToProjectUseCase,
        start_todo_usecase: StartTodoThroughProjectUseCase,
        test_session_factory,
    ):
        """Test successful todo start saves event to outbox."""
        # Create project
        project_dto = ProjectCreateDto(
            name='Start Todo Test Project',
            description='Project for testing todo start',
        )
        created_project = create_project_usecase.execute(project_dto)

        # Add todo to project
        todo_dto = AddTodoToProjectDto(
            title='Todo to Start',
            description='This todo will be started',
            dependencies=[],
        )
        added_todo = add_todo_usecase.execute(created_project.id, todo_dto)

        # Before starting: Check outbox has creation events only
        with test_session_factory() as session:
            outbox_count_before = session.query(OutboxModel).count()
            assert outbox_count_before == 3  # ProjectCreated + TodoCreated + TodoAddedToProject

        # Execute start todo
        result = start_todo_usecase.execute(created_project.id, added_todo.id)

        # Verify todo was started successfully
        assert result.id == added_todo.id
        assert result.title == 'Todo to Start'
        assert result.status == 'in_progress'
        assert result.description == 'This todo will be started'

        # After starting: Check outbox has TodoStarted event
        with test_session_factory() as session:
            outbox_entries = session.query(OutboxModel).all()
            assert len(outbox_entries) == 4

            # Find the TodoStarted event
            start_event = None
            for entry in outbox_entries:
                if entry.event_type == 'TodoStarted':
                    start_event = entry
                    break

            assert start_event is not None
            assert start_event.event_type == 'TodoStarted'
            assert str(start_event.aggregate_id) == added_todo.id
            assert start_event.published is False

            # Verify payload contains expected data
            payload = start_event.payload
            assert payload['event_type'] == 'TodoStarted'
            assert payload['todo_id'] == added_todo.id
            assert payload['project_id'] == created_project.id
            assert payload['title'] == 'Todo to Start'

    def test_start_todo_in_nonexistent_project_fails_and_rolls_back_outbox(
        self, start_todo_usecase: StartTodoThroughProjectUseCase, test_session_factory
    ):
        """Test starting todo in nonexistent project fails and rolls back outbox."""
        nonexistent_project_id = '550e8400-e29b-41d4-a716-446655440000'
        nonexistent_todo_id = '550e8400-e29b-41d4-a716-446655440001'

        # Before: Check outbox is empty
        with test_session_factory() as session:
            outbox_count_before = session.query(OutboxModel).count()
            assert outbox_count_before == 0

        # Should raise ProjectNotFoundError
        with pytest.raises(ProjectNotFoundError):
            start_todo_usecase.execute(nonexistent_project_id, nonexistent_todo_id)

        # After: Check outbox remains empty (rollback worked)
        with test_session_factory() as session:
            outbox_count_after = session.query(OutboxModel).count()
            assert outbox_count_after == outbox_count_before
            assert outbox_count_after == 0

    def test_start_nonexistent_todo_fails_and_rolls_back_outbox(
        self,
        create_project_usecase: CreateProjectUseCase,
        start_todo_usecase: StartTodoThroughProjectUseCase,
        test_session_factory,
    ):
        """Test starting nonexistent todo fails and rolls back outbox."""
        # Create project
        project_dto = ProjectCreateDto(
            name='Project for Nonexistent Todo',
            description='Project for testing nonexistent todo start',
        )
        created_project = create_project_usecase.execute(project_dto)

        nonexistent_todo_id = '550e8400-e29b-41d4-a716-446655440001'

        # Before: Check outbox has creation event only
        with test_session_factory() as session:
            outbox_count_before = session.query(OutboxModel).count()
            assert outbox_count_before == 1

        # Should raise TodoNotFoundError
        with pytest.raises(TodoNotFoundError):
            start_todo_usecase.execute(created_project.id, nonexistent_todo_id)

        # After: Check outbox count remains the same (rollback worked)
        with test_session_factory() as session:
            outbox_count_after = session.query(OutboxModel).count()
            assert outbox_count_after == outbox_count_before
            assert outbox_count_after == 1

    def test_start_todo_with_incomplete_dependencies_fails_and_rolls_back(
        self,
        create_project_usecase: CreateProjectUseCase,
        add_todo_usecase: AddTodoToProjectUseCase,
        start_todo_usecase: StartTodoThroughProjectUseCase,
        test_session_factory,
    ):
        """Test starting todo with incomplete dependencies fails and rolls back."""
        # Create project
        project_dto = ProjectCreateDto(
            name='Dependency Test Project',
            description='Project for testing dependencies',
        )
        created_project = create_project_usecase.execute(project_dto)

        # Add first todo (dependency)
        dependency_dto = AddTodoToProjectDto(
            title='Dependency Todo',
            description='This todo must be completed first',
            dependencies=[],
        )
        dependency_todo = add_todo_usecase.execute(created_project.id, dependency_dto)

        # Add second todo that depends on the first
        dependent_dto = AddTodoToProjectDto(
            title='Dependent Todo',
            description='This todo depends on the first',
            dependencies=[dependency_todo.id],
        )
        dependent_todo = add_todo_usecase.execute(created_project.id, dependent_dto)

        # Before: Check outbox has creation events
        with test_session_factory() as session:
            outbox_count_before = session.query(OutboxModel).count()
            assert outbox_count_before == 5  # ProjectCreated + 2*(TodoCreated + TodoAddedToProject)

        # Try to start dependent todo without completing dependency
        with pytest.raises(TodoDependencyNotCompletedError):
            start_todo_usecase.execute(created_project.id, dependent_todo.id)

        # After: Check outbox count remains the same (rollback worked)
        with test_session_factory() as session:
            outbox_count_after = session.query(OutboxModel).count()
            assert outbox_count_after == outbox_count_before
            assert outbox_count_after == 5

    def test_start_already_started_todo_fails_and_rolls_back(
        self,
        create_project_usecase: CreateProjectUseCase,
        add_todo_usecase: AddTodoToProjectUseCase,
        start_todo_usecase: StartTodoThroughProjectUseCase,
        test_session_factory,
    ):
        """Test starting already started todo fails and rolls back."""
        # Create project and todo
        project_dto = ProjectCreateDto(
            name='Already Started Test Project',
            description='Project for testing already started todo',
        )
        created_project = create_project_usecase.execute(project_dto)

        todo_dto = AddTodoToProjectDto(
            title='Todo to Start Twice',
            description='This todo will be started twice',
            dependencies=[],
        )
        added_todo = add_todo_usecase.execute(created_project.id, todo_dto)

        # Start todo first time (should succeed)
        result1 = start_todo_usecase.execute(created_project.id, added_todo.id)
        assert result1.status == 'in_progress'

        # Before second start: Check outbox has 4 events
        with test_session_factory() as session:
            outbox_count_before = session.query(OutboxModel).count()
            assert outbox_count_before == 4  # ProjectCreated + TodoCreated + TodoAddedToProject + TodoStarted

        # Try to start todo second time (should fail)
        with pytest.raises(TodoAlreadyStartedError):
            start_todo_usecase.execute(created_project.id, added_todo.id)

        # After: Check outbox count remains the same (rollback worked)
        with test_session_factory() as session:
            outbox_count_after = session.query(OutboxModel).count()
            assert outbox_count_after == outbox_count_before
            assert outbox_count_after == 4

    def test_multiple_todo_starts_create_multiple_outbox_entries(
        self, test_session_factory
    ):
        """Test starting multiple todos creates multiple outbox entries."""
        todo_data = [
            ('Start Test Todo 1', 'First todo to start'),
            ('Start Test Todo 2', 'Second todo to start'),
            ('Start Test Todo 3', 'Third todo to start'),
        ]

        todo_ids = []

        # Create project and todos, then start them one by one
        for i, (title, description) in enumerate(todo_data, 1):
            # Create new UoW for each operation
            class TestUoW(SqlAlchemyUnitOfWork):
                def __enter__(self):
                    self.session = test_session_factory()
                    self.event_publisher = get_event_publisher()
                    self.event_publisher.clear_events()
                    return self

            # Create project and todo
            uow = TestUoW()
            create_usecase = new_create_project_usecase(uow)
            project_dto = ProjectCreateDto(
                name=f'Start Test Project {i}',
                description=f'Project {i} for testing todo start',
            )
            created_project = create_usecase.execute(project_dto)

            uow = TestUoW()
            add_usecase = new_add_todo_to_project_usecase(uow)
            todo_dto = AddTodoToProjectDto(
                title=title,
                description=description,
                dependencies=[],
            )
            added_todo = add_usecase.execute(created_project.id, todo_dto)

            # Start todo
            uow = TestUoW()
            start_usecase = new_start_todo_through_project_usecase(uow)
            result = start_usecase.execute(created_project.id, added_todo.id)

            todo_ids.append(result.id)
            assert result.status == 'in_progress'

            # Verify outbox entry count increases with each start
            with test_session_factory() as session:
                todo_started_events = session.query(OutboxModel).filter(
                    OutboxModel.event_type == 'TodoStarted'
                ).count()
                assert todo_started_events == i

        # Final verification: all TodoStarted events are in outbox
        with test_session_factory() as session:
            start_events = session.query(OutboxModel).filter(
                OutboxModel.event_type == 'TodoStarted'
            ).all()
            assert len(start_events) == 3

            # Verify all entries are unpublished
            for entry in start_events:
                assert entry.published is False
                assert entry.event_type == 'TodoStarted'

    def test_outbox_entries_contain_complete_start_event_data(
        self,
        create_project_usecase: CreateProjectUseCase,
        add_todo_usecase: AddTodoToProjectUseCase,
        start_todo_usecase: StartTodoThroughProjectUseCase,
        test_session_factory,
    ):
        """Test that outbox entries contain all necessary start event data."""
        # Create project and todo
        project_dto = ProjectCreateDto(
            name='Complete Data Start Test',
            description='Testing complete start event data',
        )
        created_project = create_project_usecase.execute(project_dto)

        todo_dto = AddTodoToProjectDto(
            title='Complete Start Test Todo',
            description='Testing complete start event data',
            dependencies=[],
        )
        added_todo = add_todo_usecase.execute(created_project.id, todo_dto)

        # Start todo
        start_todo_usecase.execute(created_project.id, added_todo.id)

        with test_session_factory() as session:
            start_entry = None
            for entry in session.query(OutboxModel).all():
                if entry.event_type == 'TodoStarted':
                    start_entry = entry
                    break

            assert start_entry is not None

            payload = start_entry.payload

            # Verify all required fields are present
            required_fields = [
                'event_id',
                'event_type',
                'aggregate_id',
                'occurred_at',
                'todo_id',
                'project_id',
                'title',
            ]

            for field in required_fields:
                assert field in payload, f'Missing field: {field}'

            # Verify field values
            assert payload['event_type'] == 'TodoStarted'
            assert payload['todo_id'] == added_todo.id
            assert payload['project_id'] == created_project.id
            assert payload['aggregate_id'] == added_todo.id
            assert payload['title'] == 'Complete Start Test Todo'

    def test_error_during_start_rolls_back_outbox(self, test_session_factory):
        """Test that errors during start operation roll back outbox entries."""
        # Create project and todo first
        class TestUoW(SqlAlchemyUnitOfWork):
            def __enter__(self):
                self.session = test_session_factory()
                self.event_publisher = get_event_publisher()
                self.event_publisher.clear_events()
                return self

        uow = TestUoW()
        create_usecase = new_create_project_usecase(uow)
        project_dto = ProjectCreateDto(
            name='Failing Start Project',
            description='This start should fail',
        )
        created_project = create_usecase.execute(project_dto)

        uow = TestUoW()
        add_usecase = new_add_todo_to_project_usecase(uow)
        todo_dto = AddTodoToProjectDto(
            title='Failing Start Todo',
            description='This start should fail',
            dependencies=[],
        )
        added_todo = add_usecase.execute(created_project.id, todo_dto)

        # Verify creation events were saved
        with test_session_factory() as session:
            outbox_count_before = session.query(OutboxModel).count()
            assert outbox_count_before == 3

        # Create a UoW that will fail during commit
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
                raise RuntimeError('Simulated start database error')

        failing_uow = FailingUoW()
        start_usecase = new_start_todo_through_project_usecase(failing_uow)

        # Should raise the simulated error
        with pytest.raises(RuntimeError, match='Simulated start database error'):
            start_usecase.execute(created_project.id, added_todo.id)

        # Verify no new outbox entries were saved due to rollback
        with test_session_factory() as session:
            outbox_count_after = session.query(OutboxModel).count()
            assert outbox_count_after == outbox_count_before  # Still only creation events
            assert outbox_count_after == 3
