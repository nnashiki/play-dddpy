"""Test utilities for Unit of Work pattern."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dddpy.domain.shared.events import get_event_publisher
from dddpy.infrastructure.sqlite.uow import SqlAlchemyUnitOfWork


class TestUnitOfWork(SqlAlchemyUnitOfWork):
    """Test-specific Unit of Work implementation using in-memory SQLite."""

    def __init__(self, session_factory=None):
        super().__init__()
        if session_factory is None:
            # Use in-memory SQLite for testing
            test_engine = create_engine('sqlite:///:memory:')
            session_factory = sessionmaker(bind=test_engine)
        self._session_factory = session_factory

    def __enter__(self):
        self.session = self._session_factory()
        self.event_publisher = get_event_publisher()
        self.event_publisher.clear_events()
        self._tx = self.session.begin_nested()  # SAVEPOINT
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type:
            self._tx.rollback()
        else:
            try:
                self._flush_outbox()
                self._tx.commit()
            except Exception:
                self._tx.rollback()
                raise
        self.session.close()
        return False
