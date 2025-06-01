"""Project history SQLAlchemy model for tracking project lifecycle events."""

from sqlalchemy import Column, String, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

from dddpy.infrastructure.sqlite.database import Base


class ProjectHistoryModel(Base):
    """Project history model for tracking project lifecycle events."""
    
    __tablename__ = "project_histories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    event_type = Column(String(50), nullable=False)  # "CREATED", etc.
    recorded_at = Column(BigInteger, nullable=False)  # timestamp in milliseconds
