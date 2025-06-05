"""Tests for Unit of Work and Outbox pattern."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from dddpy.domain.shared.events import get_event_publisher, DomainEvent
from dddpy.infrastructure.sqlite.database import Base
from dddpy.infrastructure.sqlite.uow import SqlAlchemyUnitOfWork
from dddpy.infrastructure.sqlite.outbox.outbox_model import OutboxModel
from dddpy.dto.project import ProjectCreateDto
from dddpy.usecase.project.create_project_usecase import (
    new_create_project_usecase,
)


class MockEvent(DomainEvent):
    """Mock event for unit testing."""

    def __init__(self, aggregate_id):
        super().__init__(aggregate_id)
        self.test_data = 'test_value'

    @property
    def event_type(self) -> str:
        return 'MockEvent'

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({'test_data': self.test_data})
        return base_dict


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


class TestUnitOfWork:
    """Unit tests for SqlAlchemyUnitOfWork."""

    def test_uow_commits_transaction_successfully(self, test_session_factory):
        """Test that UoW commits transaction successfully."""

        # Create test UoW
        class TestUoW(SqlAlchemyUnitOfWork):
            def __enter__(self):
                self.session = test_session_factory()
                self.event_publisher = get_event_publisher()
                self.event_publisher.clear_events()
                return self

        # Test normal commit flow
        with TestUoW() as uow:
            # Add test event
            test_event = MockEvent(uuid4())
            uow.event_publisher.publish(test_event)

            # UoW should flush to outbox and commit
            pass

        # Verify event was saved to outbox
        with test_session_factory() as session:
            outbox_entries = session.query(OutboxModel).all()
            assert len(outbox_entries) == 1
            assert outbox_entries[0].event_type == 'MockEvent'
            assert outbox_entries[0].published is False

    def test_uow_rolls_back_on_exception(self, test_session_factory):
        """Test that UoW rolls back transaction on exception."""

        # Create test UoW
        class TestUoW(SqlAlchemyUnitOfWork):
            def __enter__(self):
                self.session = test_session_factory()
                self.event_publisher = get_event_publisher()
                self.event_publisher.clear_events()
                return self

        # Test rollback flow
        with pytest.raises(ValueError):
            with TestUoW() as uow:
                # Add test event
                test_event = MockEvent(uuid4())
                uow.event_publisher.publish(test_event)

                # Raise exception to trigger rollback
                raise ValueError('Test exception')

        # Verify no events were saved to outbox due to rollback
        with test_session_factory() as session:
            outbox_entries = session.query(OutboxModel).all()
            assert len(outbox_entries) == 0

    def test_uow_flushes_multiple_events(self, test_session_factory):
        """Test that UoW can flush multiple events to outbox."""

        # Create test UoW
        class TestUoW(SqlAlchemyUnitOfWork):
            def __enter__(self):
                self.session = test_session_factory()
                self.event_publisher = get_event_publisher()
                self.event_publisher.clear_events()
                return self

        # Test multiple events
        with TestUoW() as uow:
            # Add multiple test events
            for i in range(3):
                test_event = MockEvent(uuid4())
                test_event.test_data = f'test_value_{i}'
                uow.event_publisher.publish(test_event)

        # Verify all events were saved to outbox
        with test_session_factory() as session:
            outbox_entries = session.query(OutboxModel).all()
            assert len(outbox_entries) == 3

            # Verify events have different data
            test_data_values = {entry.payload['test_data'] for entry in outbox_entries}
            expected_values = {f'test_value_{i}' for i in range(3)}
            assert test_data_values == expected_values

    def test_event_publisher_clears_events_on_enter(self, test_session_factory):
        """Test that event publisher clears events when UoW enters."""

        # Create test UoW
        class TestUoW(SqlAlchemyUnitOfWork):
            def __enter__(self):
                self.session = test_session_factory()
                self.event_publisher = get_event_publisher()
                self.event_publisher.clear_events()
                return self

        # Clear any existing events first
        publisher = get_event_publisher()
        publisher.clear_events()

        # Add some events before UoW
        publisher.publish(MockEvent(uuid4()))
        assert len(publisher.get_events()) == 1

        # UoW should clear events on enter
        with TestUoW() as uow:
            assert len(uow.event_publisher.get_events()) == 0

            # Add new event
            uow.event_publisher.publish(MockEvent(uuid4()))
            assert len(uow.event_publisher.get_events()) == 1

        # Verify only the new event was saved
        with test_session_factory() as session:
            outbox_entries = session.query(OutboxModel).all()
            assert len(outbox_entries) == 1


class TestOutboxModel:
    """Unit tests for OutboxModel."""

    def test_outbox_model_creation(self, test_session_factory):
        """Test OutboxModel can be created and saved."""
        test_aggregate_id = uuid4()

        with test_session_factory() as session:
            outbox_entry = OutboxModel(
                aggregate_id=test_aggregate_id,
                event_type='MockEvent',
                payload={'key': 'value'},
            )
            session.add(outbox_entry)
            session.commit()

            # Verify entry was saved
            saved_entry = session.query(OutboxModel).first()
            assert saved_entry is not None
            assert saved_entry.aggregate_id == test_aggregate_id
            assert saved_entry.event_type == 'MockEvent'
            assert saved_entry.payload == {'key': 'value'}
            assert saved_entry.published is False
            assert saved_entry.created_at is not None

    def test_outbox_model_defaults(self, test_session_factory):
        """Test OutboxModel default values."""
        with test_session_factory() as session:
            outbox_entry = OutboxModel(
                aggregate_id=uuid4(),
                event_type='MockEvent',
                payload={'test': 'data'},
            )
            session.add(outbox_entry)
            session.commit()

            saved_entry = session.query(OutboxModel).first()
            assert saved_entry.id is not None  # UUID generated
            assert saved_entry.published is False  # Default value
            assert saved_entry.created_at is not None  # Auto-generated


class TestCreateProjectIntegration:
    """Integration tests for CreateProjectUseCase."""

    def test_create_project_saves_to_outbox(self, test_session_factory):
        """Test that creating a project saves event to outbox."""

        # Create test UoW
        class TestUoW(SqlAlchemyUnitOfWork):
            def __enter__(self):
                self.session = test_session_factory()
                self.event_publisher = get_event_publisher()
                self.event_publisher.clear_events()
                return self

        # Create UseCase with test UoW
        uow = TestUoW()
        usecase = new_create_project_usecase(uow)

        # Create project
        dto = ProjectCreateDto(name='Test Project', description='Test Description')

        result = usecase.execute(dto)

        # Verify project was created
        assert result.name == 'Test Project'
        assert result.description == 'Test Description'

        # Verify event was saved to outbox
        with test_session_factory() as session:
            outbox_entries = session.query(OutboxModel).all()
            assert len(outbox_entries) == 1

            entry = outbox_entries[0]
            assert entry.event_type == 'ProjectCreated'
            assert entry.aggregate_id.hex == result.id.replace('-', '')
            assert entry.published is False
            assert 'project_id' in entry.payload
            assert 'name' in entry.payload
            assert entry.payload['name'] == 'Test Project'

    def test_create_duplicate_project_rolls_back_outbox(self, test_session_factory):
        """Test that duplicate project creation rolls back outbox entry."""

        # Create test UoW
        class TestUoW(SqlAlchemyUnitOfWork):
            def __enter__(self):
                self.session = test_session_factory()
                self.event_publisher = get_event_publisher()
                self.event_publisher.clear_events()
                return self

        # Create first project successfully
        uow1 = TestUoW()
        usecase1 = new_create_project_usecase(uow1)

        dto = ProjectCreateDto(
            name='Duplicate Test Project', description='First project'
        )

        result1 = usecase1.execute(dto)
        assert result1.name == 'Duplicate Test Project'

        # Verify first event was saved
        with test_session_factory() as session:
            outbox_count_after_first = session.query(OutboxModel).count()
            assert outbox_count_after_first == 1

        # Try to create project with same name (should fail)
        uow2 = TestUoW()
        usecase2 = new_create_project_usecase(uow2)

        dto2 = ProjectCreateDto(
            name='Duplicate Test Project',  # Same name
            description='Second project',
        )

        with pytest.raises(
            ValueError, match="Project name 'Duplicate Test Project' already exists"
        ):
            usecase2.execute(dto2)

        # Verify outbox still has only the first event (rollback worked)
        with test_session_factory() as session:
            outbox_count_after_failure = session.query(OutboxModel).count()
            assert outbox_count_after_failure == 1  # No new events added

    def test_multiple_projects_create_multiple_outbox_entries(
        self, test_session_factory
    ):
        """Test that creating multiple projects creates multiple outbox entries."""

        # Create test UoW
        class TestUoW(SqlAlchemyUnitOfWork):
            def __enter__(self):
                self.session = test_session_factory()
                self.event_publisher = get_event_publisher()
                self.event_publisher.clear_events()
                return self

        project_names = ['Project A', 'Project B', 'Project C']

        for i, name in enumerate(project_names):
            uow = TestUoW()
            usecase = new_create_project_usecase(uow)

            dto = ProjectCreateDto(name=name, description=f'Description for {name}')

            result = usecase.execute(dto)
            assert result.name == name

            # Verify outbox entry count increases
            with test_session_factory() as session:
                outbox_count = session.query(OutboxModel).count()
                assert outbox_count == i + 1

        # Verify all events are in outbox
        with test_session_factory() as session:
            outbox_entries = session.query(OutboxModel).all()
            assert len(outbox_entries) == 3

            saved_names = {entry.payload['name'] for entry in outbox_entries}
            assert saved_names == set(project_names)
