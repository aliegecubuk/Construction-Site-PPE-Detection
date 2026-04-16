"""
REPORT-AI — Sabit Değerler (Constants)
=======================================
Proje genelinde kullanılan sabit değerler.
Bu dosya hiçbir dış bağımlılık içermez.
"""

from typing import Dict, List

# ---------------------------------------------------------------------------
# YOLO Model Sınıfları
# Mevcut PPE Detection modelinin tespit ettiği 10 sınıf.
# Sıralama, modelin class index'leriyle birebir eşleşmelidir.
# ---------------------------------------------------------------------------
DETECTION_CLASSES: List[str] = [
    "Hardhat",
    "Mask",
    "NO-Hardhat",
    "NO-Mask",
    "NO-Safety Vest",
    "Person",
    "Safety Cone",
    "Safety Vest",
    "machinery",
    "vehicle",
]

# Sınıf index'inden isme kolay erişim
CLASS_INDEX_MAP: Dict[int, str] = {i: name for i, name in enumerate(DETECTION_CLASSES)}

# ---------------------------------------------------------------------------
# İhlal (Violation) Sınıfları
# "NO-" ile başlayan sınıflar, KKD eksikliğini temsil eder.
# ---------------------------------------------------------------------------
VIOLATION_CLASSES: List[str] = [
    "NO-Hardhat",
    "NO-Mask",
    "NO-Safety Vest",
]

PPE_REQUIREMENT_TO_DETECTION: Dict[str, Dict[str, str]] = {
    "hardhat": {
        "present": "Hardhat",
        "missing": "NO-Hardhat",
        "label": "Baret Yok",
    },
    "mask": {
        "present": "Mask",
        "missing": "NO-Mask",
        "label": "Maske Yok",
    },
    "safety_vest": {
        "present": "Safety Vest",
        "missing": "NO-Safety Vest",
        "label": "Yelek Yok",
    },
}

# ---------------------------------------------------------------------------
# Varsayılan Eşik Değerleri
# ---------------------------------------------------------------------------
DEFAULT_CONFIDENCE_THRESHOLD: float = 0.5
DEFAULT_IOU_THRESHOLD: float = 0.45
DEFAULT_FRAME_WIDTH: int = 640
DEFAULT_FRAME_HEIGHT: int = 480
DEFAULT_FPS: int = 25

# ---------------------------------------------------------------------------
# IoT Sensör Eşik Değerleri
# ---------------------------------------------------------------------------
IOT_THRESHOLDS = {
    "gas_level": {"warning": 50.0, "critical": 80.0, "unit": "ppm"},
    "temperature": {"warning": 35.0, "critical": 42.0, "unit": "°C"},
    "humidity": {"warning": 70.0, "critical": 85.0, "unit": "%"},
    "noise_level": {"warning": 85.0, "critical": 100.0, "unit": "dB"},
    "vibration": {"warning": 5.0, "critical": 8.0, "unit": "mm/s"},
}
