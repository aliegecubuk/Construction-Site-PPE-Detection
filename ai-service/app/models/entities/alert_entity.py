"""
Alert Entity — Alarm/İhlal kayıtları tablosu ORM modeli.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.entities.base import Base


class AlertEntity(Base):
    """Alarm/ihlal kayıtları tablosu."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    alert_type: Mapped[str] = mapped_column(String(30), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), default="")
    camera_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sensor_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    violations: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
