"""Unit of Work implementation for SQLAlchemy with Outbox pattern."""

from contextlib import AbstractContextManager
from sqlalchemy.orm import Session
from typing import Iterator

from dddpy.domain.shared.events import DomainEventPublisher
from dddpy.infrastructure.sqlite.database import SessionLocal
from dddpy.infrastructure.sqlite.outbox.outbox_model import OutboxModel


class SqlAlchemyUnitOfWork(AbstractContextManager):
    """Unit of Work implementation using SQLAlchemy with transactional outbox pattern."""

    def __init__(self) -> None:
        self.session: Session | None = None
        self.event_publisher: DomainEventPublisher | None = None

    def __enter__(self) -> 'SqlAlchemyUnitOfWork':
        self.session = SessionLocal()
        # ★ 各 UseCase に渡す publisher
        from dddpy.domain.shared.events import get_event_publisher

        self.event_publisher = get_event_publisher()
        self.event_publisher.clear_events()  # 前回残骸を除去
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:  # type: ignore[override]
        if self.session is None:
            return False

        if exc_type:
            self.session.rollback()
            return False  # 例外を再送出
        try:
            self._flush_outbox()
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        finally:
            self.session.close()
        return True

    # ----------------------------------------------------------
    # INTERNALS
    # ----------------------------------------------------------
    def _flush_outbox(self) -> None:
        """Publisher に貯まった DomainEvent を Outbox テーブルへコピー"""
        if self.session is None or self.event_publisher is None:
            return

        for ev in self.event_publisher.get_events():
            self.session.add(
                OutboxModel(
                    aggregate_id=ev.aggregate_id,
                    event_type=ev.event_type,
                    payload=ev.to_dict(),
                )
            )
