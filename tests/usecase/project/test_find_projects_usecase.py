"""Tests for FindProjectsUseCase with UoW support."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dddpy.domain.shared.events import get_event_publisher
from dddpy.infrastructure.sqlite.database import Base
from dddpy.infrastructure.sqlite.uow import SqlAlchemyUnitOfWork
from dddpy.infrastructure.sqlite.outbox.outbox_model import OutboxModel
from dddpy.dto.project import ProjectCreateDto
from dddpy.usecase.project.create_project_usecase import new_create_project_usecase
from dddpy.usecase.project.find_projects_usecase import (
    FindProjectsUseCase,
    new_find_projects_usecase,
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
def find_projects_usecase(test_uow):
    """Create FindProjectsUseCase for testing."""
    return new_find_projects_usecase(test_uow)


@pytest.fixture
def setup_test_projects(test_session_factory):
    """Create test projects for read operations."""
    project_data = [
        ('Test Project Alpha', 'First test project'),
        ('Test Project Beta', 'Second test project'),
        ('Test Project Gamma', 'Third test project'),
    ]

    created_projects = []

    for name, description in project_data:
        # Create new UoW for each project
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
        created_projects.append(result)

    return created_projects


class TestFindProjectsUseCase:
    """Test cases for FindProjectsUseCase with UoW support."""

    def test_find_all_projects_with_empty_database(
        self, find_projects_usecase: FindProjectsUseCase
    ):
        """Test finding projects when database is empty."""
        result = find_projects_usecase.execute()

        assert result == []

    def test_find_all_projects_successfully(
        self, test_session_factory, setup_test_projects
    ):
        """Test successful retrieval of all projects."""
        # Use fresh UoW for read operation
        class TestUoW(SqlAlchemyUnitOfWork):
            def __enter__(self):
                self.session = test_session_factory()
                self.event_publisher = get_event_publisher()
                self.event_publisher.clear_events()
                return self

        uow = TestUoW()
        usecase = new_find_projects_usecase(uow)

        result = usecase.execute()

        # Verify all projects are returned
        assert len(result) == 3

        # Verify project names and descriptions
        project_names = {project.name for project in result}
        expected_names = {'Test Project Alpha', 'Test Project Beta', 'Test Project Gamma'}
        assert project_names == expected_names

        # Verify all projects have expected structure
        for project in result:
            assert project.id is not None
            assert project.name is not None
            assert project.description is not None
            assert isinstance(project.todos, list)
            assert project.created_at is not None
            assert project.updated_at is not None

    def test_find_projects_does_not_create_outbox_entries(
        self, test_session_factory, setup_test_projects
    ):
        """Test that read operations do not create outbox entries."""
        # Before: Check initial outbox count (should be 3 from setup)
        with test_session_factory() as session:
            outbox_count_before = session.query(OutboxModel).count()
            assert outbox_count_before == 3  # From setup_test_projects

        # Use fresh UoW for read operation
        class TestUoW(SqlAlchemyUnitOfWork):
            def __enter__(self):
                self.session = test_session_factory()
                self.event_publisher = get_event_publisher()
                self.event_publisher.clear_events()
                return self

        uow = TestUoW()
        usecase = new_find_projects_usecase(uow)

        # Execute read operation
        result = usecase.execute()
        assert len(result) == 3

        # After: Check outbox count remains the same
        with test_session_factory() as session:
            outbox_count_after = session.query(OutboxModel).count()
            assert outbox_count_after == outbox_count_before  # No new events
            assert outbox_count_after == 3

    def test_find_projects_handles_uow_errors_gracefully(self, test_session_factory):
        """Test that UoW initialization errors are handled properly."""
        # Create UoW that fails to initialize properly
        class FailingUoW(SqlAlchemyUnitOfWork):
            def __enter__(self):
                self.session = None  # Simulate initialization failure
                self.event_publisher = None
                return self

        failing_uow = FailingUoW()
        usecase = new_find_projects_usecase(failing_uow)

        # Should raise RuntimeError for improper initialization
        with pytest.raises(RuntimeError, match='UoW was not properly initialized'):
            usecase.execute()

    def test_find_projects_performance_with_large_dataset(self, test_session_factory):
        """Test performance characteristics with larger dataset."""
        # Create more projects for performance testing
        project_count = 50
        created_projects = []

        for i in range(project_count):
            class TestUoW(SqlAlchemyUnitOfWork):
                def __enter__(self):
                    self.session = test_session_factory()
                    self.event_publisher = get_event_publisher()
                    self.event_publisher.clear_events()
                    return self

            uow = TestUoW()
            create_usecase = new_create_project_usecase(uow)

            dto = ProjectCreateDto(
                name=f'Performance Test Project {i}',
                description=f'Project {i} for performance testing',
            )
            result = create_usecase.execute(dto)
            created_projects.append(result)

        # Now test find operation
        class TestUoW(SqlAlchemyUnitOfWork):
            def __enter__(self):
                self.session = test_session_factory()
                self.event_publisher = get_event_publisher()
                self.event_publisher.clear_events()
                return self

        uow = TestUoW()
        usecase = new_find_projects_usecase(uow)

        # Measure basic performance (this is a simple check, not comprehensive benchmarking)
        import time
        start_time = time.time()
        result = usecase.execute()
        end_time = time.time()

        # Verify results
        assert len(result) == project_count
        execution_time = end_time - start_time

        # Basic performance assertion (should complete within reasonable time)
        assert execution_time < 5.0  # Should complete within 5 seconds

        # Verify all projects are unique
        project_ids = {project.id for project in result}
        assert len(project_ids) == project_count

    def test_find_projects_returns_consistent_data_structure(
        self, test_session_factory, setup_test_projects
    ):
        """Test that returned data structure is consistent and complete."""
        class TestUoW(SqlAlchemyUnitOfWork):
            def __enter__(self):
                self.session = test_session_factory()
                self.event_publisher = get_event_publisher()
                self.event_publisher.clear_events()
                return self

        uow = TestUoW()
        usecase = new_find_projects_usecase(uow)

        result = usecase.execute()

        # Verify each project has all required fields
        for project in result:
            # Required string fields
            assert isinstance(project.id, str)
            assert isinstance(project.name, str)
            assert isinstance(project.description, str)

            # Required list field
            assert isinstance(project.todos, list)

            # Required datetime fields  
            assert project.created_at is not None
            assert project.updated_at is not None

            # Verify ID format (should be UUID string)
            assert len(project.id) > 0
            assert '-' in project.id  # Basic UUID format check

    def test_multiple_find_operations_are_independent(self, test_session_factory, setup_test_projects):
        """Test that multiple find operations are independent and don't interfere."""
        # Execute multiple find operations
        results = []

        for i in range(3):
            class TestUoW(SqlAlchemyUnitOfWork):
                def __enter__(self):
                    self.session = test_session_factory()
                    self.event_publisher = get_event_publisher()
                    self.event_publisher.clear_events()
                    return self

            uow = TestUoW()
            usecase = new_find_projects_usecase(uow)
            
            result = usecase.execute()
            results.append(result)

        # All results should be identical
        assert len(results) == 3
        for result in results:
            assert len(result) == 3

        # Verify consistent project IDs across calls
        first_ids = {p.id for p in results[0]}
        for result in results[1:]:
            result_ids = {p.id for p in result}
            assert result_ids == first_ids
