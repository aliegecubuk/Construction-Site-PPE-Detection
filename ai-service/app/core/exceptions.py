"""
REPORT-AI — Özel Exception Sınıfları
======================================
Domain-spesifik hata türleri.
Service ve AI katmanları bu hataları fırlatır, API katmanı yakalar.
"""


class ReportAIBaseError(Exception):
    """Tüm proje hatalarının temel sınıfı."""

    def __init__(self, message: str = "Bilinmeyen bir hata oluştu."):
        self.message = message
        super().__init__(self.message)


# ---------------------------------------------------------------------------
# Kamera Hataları
# ---------------------------------------------------------------------------
class CameraNotFoundError(ReportAIBaseError):
    """Belirtilen kamera ID'si bulunamadığında fırlatılır."""

    def __init__(self, camera_id: str):
        super().__init__(f"Kamera bulunamadı: {camera_id}")
        self.camera_id = camera_id


class CameraConnectionError(ReportAIBaseError):
    """Kameraya bağlanılamadığında fırlatılır (RTSP timeout vb.)."""

    def __init__(self, camera_id: str, reason: str = ""):
        msg = f"Kamera bağlantı hatası: {camera_id}"
        if reason:
            msg += f" — {reason}"
        super().__init__(msg)


# ---------------------------------------------------------------------------
# Model Hataları
# ---------------------------------------------------------------------------
class ModelLoadError(ReportAIBaseError):
    """Model ağırlıkları yüklenemediğinde fırlatılır."""

    def __init__(self, weights_path: str, reason: str = ""):
        msg = f"Model yüklenemedi: {weights_path}"
        if reason:
            msg += f" — {reason}"
        super().__init__(msg)


class InferenceError(ReportAIBaseError):
    """Model çıkarımı sırasında hata oluştuğunda fırlatılır."""

    def __init__(self, reason: str = "Çıkarım sırasında hata oluştu."):
        super().__init__(reason)


# ---------------------------------------------------------------------------
# IoT Hataları
# ---------------------------------------------------------------------------
class SensorReadError(ReportAIBaseError):
    """Sensör verisi okunamadığında fırlatılır."""

    def __init__(self, sensor_type: str, reason: str = ""):
        msg = f"Sensör okuma hatası: {sensor_type}"
        if reason:
            msg += f" — {reason}"
        super().__init__(msg)
