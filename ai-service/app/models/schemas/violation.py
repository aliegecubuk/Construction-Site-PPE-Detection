"""
İhlal olayları — Python servisinden .NET orkestratörüne gönderilen olay sözleşmesi.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ViolationEvent(BaseModel):
    """SignalR üzerinden Angular'a iletilecek tekil ihlal olayı."""

    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(..., alias="eventId")
    camera_id: str = Field(..., alias="cameraId")
    camera_name: str = Field(..., alias="cameraName")
    violation_type: str = Field(..., alias="violationType")
    message: str
    occurred_at: datetime = Field(default_factory=datetime.utcnow, alias="occurredAt")
    frame_number: int = Field(default=0, alias="frameNumber")
