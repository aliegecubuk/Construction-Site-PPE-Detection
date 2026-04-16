"""
Detection Entity — Tespit kayıtları tablosu ORM modeli.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.entities.base import Base


class DetectionEntity(Base):
    """Tespit log tablosu — her frame analizi bir satır."""

    __tablename__ = "detections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    camera_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    frame_number: Mapped[int] = mapped_column(Integer, default=0)
    person_count: Mapped[int] = mapped_column(Integer, default=0)
    violation_count: Mapped[int] = mapped_column(Integer, default=0)
    detections_json: Mapped[dict] = mapped_column(JSON, default=list)
    confidence_avg: Mapped[float] = mapped_column(Float, default=0.0)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
