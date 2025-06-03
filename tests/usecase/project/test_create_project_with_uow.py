"""Tests for CreateProjectWithUoWUseCase."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dddpy.domain.shared.events import get_event_publisher
from dddpy.infrastructure.sqlite.database import Base
from dddpy.infrastructure.sqlite.uow import SqlAlchemyUnitOfWork
from dddpy.infrastructure.sqlite.outbox.outbox_model import OutboxModel
from dddpy.dto.project import ProjectCreateDto
from dddpy.usecase.project.create_project_with_uow_usecase import (
    CreateProjectWithUoWUseCase,
    new_create_project_with_uow_usecase,
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
    """Create CreateProjectWithUoWUseCase for testing."""
    return new_create_project_with_uow_usecase(test_uow)


class TestCreateProjectWithUoWUseCase:
    """Test cases for CreateProjectWithUoWUseCase matching demo scripts."""

    def test_create_project_successfully_saves_to_outbox(
        self, create_project_usecase: CreateProjectWithUoWUseCase, test_session_factory
    ):
        """Test successful project creation saves event to outbox (demo_outbox.py equivalent)."""
        # Before: Check outbox is empty
        with test_session_factory() as session:
            outbox_count_before = session.query(OutboxModel).count()
            assert outbox_count_before == 0

        # Create project DTO
        dto = ProjectCreateDto(
            name='Test Outbox Project',
            description='Project created to test outbox pattern',
        )

        # Execute UseCase
        result = create_project_usecase.execute(dto)

        # Verify project was created successfully
        assert result.name == 'Test Outbox Project'
        assert result.description == 'Project created to test outbox pattern'
        assert result.id is not None
        assert result.todos == []  # New project has no todos

        # After: Check outbox has events
        with test_session_factory() as session:
            outbox_entries = session.query(OutboxModel).all()
            assert len(outbox_entries) == 1

            entry = outbox_entries[0]
            assert entry.event_type == 'ProjectCreated'
            assert str(entry.aggregate_id) == result.id
            assert entry.published is False
            assert entry.created_at is not None

            # Verify payload contains expected data
            payload = entry.payload
            assert payload['event_type'] == 'ProjectCreated'
            assert payload['project_id'] == result.id
            assert payload['name'] == 'Test Outbox Project'
            assert payload['description'] == 'Project created to test outbox pattern'

    def test_duplicate_project_name_fails_and_rolls_back_outbox(
        self, create_project_usecase: CreateProjectWithUoWUseCase, test_session_factory
    ):
        """Test duplicate project creation fails and rolls back outbox (demo_rollback.py equivalent)."""
        # Create first project successfully
        dto1 = ProjectCreateDto(
            name='Duplicate Test Project', description='First project'
        )

        result1 = create_project_usecase.execute(dto1)
        assert result1.name == 'Duplicate Test Project'

        # Before: Check outbox has one entry
        with test_session_factory() as session:
            outbox_count_before = session.query(OutboxModel).count()
            assert outbox_count_before == 1

        # Try to create project with duplicate name
        dto2 = ProjectCreateDto(
            name='Duplicate Test Project',  # Same name as first project
            description='This should fail and rollback',
        )

        # Should raise ValueError for duplicate name
        with pytest.raises(ValueError) as exc_info:
            create_project_usecase.execute(dto2)

        assert "Project name 'Duplicate Test Project' already exists" in str(
            exc_info.value
        )

        # After: Check outbox count remains the same (rollback worked)
        with test_session_factory() as session:
            outbox_count_after = session.query(OutboxModel).count()
            assert outbox_count_after == outbox_count_before  # No new events added
            assert outbox_count_after == 1

    def test_multiple_projects_create_multiple_outbox_entries(
        self, test_session_factory
    ):
        """Test creating multiple projects creates multiple outbox entries."""
        project_data = [
            ('Test Project 1', 'Description 1'),
            ('Test Project 2', 'Description 2'),
            ('Test Project 3', 'Description 3'),
        ]

        created_projects = []

        for i, (name, description) in enumerate(project_data, 1):
            # Create new UoW for each project
            class TestUoW(SqlAlchemyUnitOfWork):
                def __enter__(self):
                    self.session = test_session_factory()
                    self.event_publisher = get_event_publisher()
                    self.event_publisher.clear_events()
                    return self

            uow = TestUoW()
            usecase = new_create_project_with_uow_usecase(uow)

            dto = ProjectCreateDto(name=name, description=description)
            result = usecase.execute(dto)

            created_projects.append(result)
            assert result.name == name
            assert result.description == description

            # Verify outbox entry count increases with each project
            with test_session_factory() as session:
                outbox_count = session.query(OutboxModel).count()
                assert outbox_count == i

        # Final verification: all events are in outbox
        with test_session_factory() as session:
            outbox_entries = session.query(OutboxModel).all()
            assert len(outbox_entries) == 3

            # Verify all project names are present in payloads
            saved_names = {entry.payload['name'] for entry in outbox_entries}
            expected_names = {name for name, _ in project_data}
            assert saved_names == expected_names

            # Verify all entries are unpublished
            for entry in outbox_entries:
                assert entry.published is False
                assert entry.event_type == 'ProjectCreated'

    def test_outbox_entries_contain_complete_event_data(
        self, create_project_usecase: CreateProjectWithUoWUseCase, test_session_factory
    ):
        """Test that outbox entries contain all necessary event data."""
        dto = ProjectCreateDto(
            name='Complete Data Test Project', description='Testing complete event data'
        )

        result = create_project_usecase.execute(dto)

        with test_session_factory() as session:
            outbox_entry = session.query(OutboxModel).first()
            assert outbox_entry is not None

            payload = outbox_entry.payload

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
            assert payload['event_type'] == 'ProjectCreated'
            assert payload['project_id'] == result.id
            assert payload['aggregate_id'] == result.id
            assert payload['name'] == 'Complete Data Test Project'
            assert payload['description'] == 'Testing complete event data'

    def test_error_during_save_rolls_back_outbox(self, test_session_factory):
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
                raise RuntimeError('Simulated database error')

        failing_uow = FailingUoW()
        usecase = new_create_project_with_uow_usecase(failing_uow)

        dto = ProjectCreateDto(name='Failing Project', description='This should fail')

        # Should raise the simulated error
        with pytest.raises(RuntimeError, match='Simulated database error'):
            usecase.execute(dto)

        # Verify no outbox entries were saved due to rollback
        with test_session_factory() as session:
            outbox_count = session.query(OutboxModel).count()
            assert outbox_count == 0
