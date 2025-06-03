"""Outbox model for transactional outbox pattern."""

from sqlalchemy import Boolean, Column, DateTime, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid import uuid4

from dddpy.infrastructure.sqlite.database import Base


class OutboxModel(Base):
    """Outbox table model for storing domain events transactionally."""

    __tablename__ = 'outbox'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    aggregate_id = Column(UUID(as_uuid=True), nullable=False)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    published = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
