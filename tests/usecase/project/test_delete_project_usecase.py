"""Tests for DeleteProjectUseCase."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dddpy.domain.shared.events import get_event_publisher
from dddpy.domain.project.exceptions import ProjectNotFoundError
from dddpy.infrastructure.sqlite.database import Base
from dddpy.infrastructure.sqlite.uow import SqlAlchemyUnitOfWork
from dddpy.infrastructure.sqlite.outbox.outbox_model import OutboxModel
from dddpy.dto.project import ProjectCreateDto
from dddpy.usecase.project.create_project_usecase import (
    CreateProjectUseCase,
    new_create_project_usecase,
)
from dddpy.usecase.project.delete_project_usecase import (
    DeleteProjectUseCase,
    new_delete_project_usecase,
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
def delete_project_usecase(test_uow):
    """Create DeleteProjectUseCase for testing."""
    return new_delete_project_usecase(test_uow)


class TestDeleteProjectUseCase:
    """Test cases for DeleteProjectUseCase."""

    def test_delete_project_successfully_saves_to_outbox(
        self,
        create_project_usecase: CreateProjectUseCase,
        delete_project_usecase: DeleteProjectUseCase,
        test_session_factory,
    ):
        """Test successful project deletion saves event to outbox."""
        # First, create a project to delete
        create_dto = ProjectCreateDto(
            name='Project to Delete',
            description='This project will be deleted',
        )
        created_project = create_project_usecase.execute(create_dto)

        # Before deletion: Check outbox has creation event only
        with test_session_factory() as session:
            outbox_count_before = session.query(OutboxModel).count()
            assert outbox_count_before == 1  # Only creation event

        # Execute deletion
        delete_project_usecase.execute(created_project.id)

        # After deletion: Check outbox has both creation and deletion events
        with test_session_factory() as session:
            outbox_entries = session.query(OutboxModel).all()
            assert len(outbox_entries) == 2

            # Find the deletion event
            deletion_event = None
            for entry in outbox_entries:
                if entry.event_type == 'ProjectDeleted':
                    deletion_event = entry
                    break

            assert deletion_event is not None
            assert deletion_event.event_type == 'ProjectDeleted'
            assert str(deletion_event.aggregate_id) == created_project.id
            assert deletion_event.published is False
            assert deletion_event.created_at is not None

            # Verify payload contains expected data
            payload = deletion_event.payload
            assert payload['event_type'] == 'ProjectDeleted'
            assert payload['project_id'] == created_project.id
            assert payload['name'] == 'Project to Delete'
            assert payload['description'] == 'This project will be deleted'

    def test_delete_nonexistent_project_fails_and_rolls_back_outbox(
        self, delete_project_usecase: DeleteProjectUseCase, test_session_factory
    ):
        """Test deleting nonexistent project fails and rolls back outbox."""
        nonexistent_id = '550e8400-e29b-41d4-a716-446655440000'

        # Before: Check outbox is empty
        with test_session_factory() as session:
            outbox_count_before = session.query(OutboxModel).count()
            assert outbox_count_before == 0

        # Should raise ProjectNotFoundError
        with pytest.raises(ProjectNotFoundError):
            delete_project_usecase.execute(nonexistent_id)

        # After: Check outbox remains empty (rollback worked)
        with test_session_factory() as session:
            outbox_count_after = session.query(OutboxModel).count()
            assert outbox_count_after == outbox_count_before  # No new events added
            assert outbox_count_after == 0

    def test_multiple_project_deletions_create_multiple_outbox_entries(
        self, test_session_factory
    ):
        """Test deleting multiple projects creates multiple outbox entries."""
        project_data = [
            ('Delete Test Project 1', 'First project to delete'),
            ('Delete Test Project 2', 'Second project to delete'),
            ('Delete Test Project 3', 'Third project to delete'),
        ]

        created_project_ids = []

        # Create projects first
        for name, description in project_data:
            class TestUoW(SqlAlchemyUnitOfWork):
                def __enter__(self):
                    self.session = test_session_factory()
                    self.event_publisher = get_event_publisher()
                    self.event_publisher.clear_events()
                    return self

            uow = TestUoW()
            create_usecase = new_create_project_usecase(uow)
            
            dto = ProjectCreateDto(name=name, description=description)
            result = create_usecase.execute(dto)
            created_project_ids.append(result.id)

        # Count creation events
        with test_session_factory() as session:
            creation_events_count = session.query(OutboxModel).count()
            assert creation_events_count == 3

        # Delete projects one by one
        for i, project_id in enumerate(created_project_ids, 1):
            class TestUoW(SqlAlchemyUnitOfWork):
                def __enter__(self):
                    self.session = test_session_factory()
                    self.event_publisher = get_event_publisher()
                    self.event_publisher.clear_events()
                    return self

            uow = TestUoW()
            delete_usecase = new_delete_project_usecase(uow)
            delete_usecase.execute(project_id)

            # Verify outbox entry count increases with each deletion
            with test_session_factory() as session:
                total_events = session.query(OutboxModel).count()
                expected_count = 3 + i  # 3 creation + i deletion events
                assert total_events == expected_count

        # Final verification: all events are in outbox
        with test_session_factory() as session:
            outbox_entries = session.query(OutboxModel).all()
            assert len(outbox_entries) == 6  # 3 creation + 3 deletion

            # Count event types
            creation_events = [e for e in outbox_entries if e.event_type == 'ProjectCreated']
            deletion_events = [e for e in outbox_entries if e.event_type == 'ProjectDeleted']
            
            assert len(creation_events) == 3
            assert len(deletion_events) == 3

            # Verify all entries are unpublished
            for entry in outbox_entries:
                assert entry.published is False

    def test_outbox_entries_contain_complete_deletion_event_data(
        self,
        create_project_usecase: CreateProjectUseCase,
        delete_project_usecase: DeleteProjectUseCase,
        test_session_factory,
    ):
        """Test that outbox entries contain all necessary deletion event data."""
        # Create project first
        create_dto = ProjectCreateDto(
            name='Complete Data Delete Test',
            description='Testing complete deletion event data',
        )
        created_project = create_project_usecase.execute(create_dto)

        # Delete project
        delete_project_usecase.execute(created_project.id)

        with test_session_factory() as session:
            deletion_entry = None
            for entry in session.query(OutboxModel).all():
                if entry.event_type == 'ProjectDeleted':
                    deletion_entry = entry
                    break

            assert deletion_entry is not None

            payload = deletion_entry.payload

            # Verify all required fields are present
            required_fields = [
                'event_id',
                'event_type',
                'aggregate_id',
                'occurred_at',
                'project_id',
                'name',
                'description',
            ]

            for field in required_fields:
                assert field in payload, f'Missing field: {field}'

            # Verify field values
            assert payload['event_type'] == 'ProjectDeleted'
            assert payload['project_id'] == created_project.id
            assert payload['aggregate_id'] == created_project.id
            assert payload['name'] == 'Complete Data Delete Test'
            assert payload['description'] == 'Testing complete deletion event data'

    def test_error_during_deletion_rolls_back_outbox(self, test_session_factory):
        """Test that errors during deletion operation roll back outbox entries."""
        # Create project first
        class TestUoW(SqlAlchemyUnitOfWork):
            def __enter__(self):
                self.session = test_session_factory()
                self.event_publisher = get_event_publisher()
                self.event_publisher.clear_events()
                return self

        uow = TestUoW()
        create_usecase = new_create_project_usecase(uow)
        
        create_dto = ProjectCreateDto(
            name='Failing Delete Project',
            description='This deletion should fail',
        )
        created_project = create_usecase.execute(create_dto)

        # Verify creation event was saved
        with test_session_factory() as session:
            outbox_count_before = session.query(OutboxModel).count()
            assert outbox_count_before == 1

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
                raise RuntimeError('Simulated deletion database error')

        failing_uow = FailingUoW()
        delete_usecase = new_delete_project_usecase(failing_uow)

        # Should raise the simulated error
        with pytest.raises(RuntimeError, match='Simulated deletion database error'):
            delete_usecase.execute(created_project.id)

        # Verify no new outbox entries were saved due to rollback
        with test_session_factory() as session:
            outbox_count_after = session.query(OutboxModel).count()
            assert outbox_count_after == outbox_count_before  # Still only creation event
            assert outbox_count_after == 1
