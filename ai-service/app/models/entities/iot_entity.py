"""
IoT Entity — Sensör okumaları tablosu ORM modeli.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.entities.base import Base


class IoTReadingEntity(Base):
    """IoT sensör okumaları tablosu."""

    __tablename__ = "iot_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sensor_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    sensor_type: Mapped[str] = mapped_column(String(30), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(10), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="normal")
    location: Mapped[str] = mapped_column(String(100), default="Genel Alan")
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
