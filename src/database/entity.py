import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database.db import Base


class BaseEntity(Base):
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Идентификатор",
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=sa.func.current_timestamp(),
        server_default=sa.func.now(),
        comment="Дата создания",
    )

    updated_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=sa.func.current_timestamp(),
        server_default=sa.func.now(),
        onupdate=sa.func.current_timestamp(),
        comment="Дата обновления",
    )
