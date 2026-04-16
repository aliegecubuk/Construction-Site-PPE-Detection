"""
Risk Engine — Görüntü ihlalleri + IoT verileri → Birleşik Risk Skoru.

Bu modül:
    • Vision (görüntü) kaynaklı ihlalleri (NO-Hardhat, NO-Mask, NO-Vest) skorlar.
    • IoT (çevresel) verileri (gaz, sıcaklık, nem, gürültü, titreşim) skorlar.
    • İki skoru ağırlıklı olarak birleştirir: vision × 0.6 + iot × 0.4.
    • Toplam skora göre risk seviyesi belirler: LOW / MEDIUM / HIGH / CRITICAL.
    • Her faktörü detaylı RiskFactor olarak raporlar.

Ağırlık mantığı:
    İnşaat sahalarında en büyük risk kişilerin KKD kullanmamasıdır (vision),
    ancak çevresel tehlikeler (gaz sızıntısı vb.) de hayati önem taşır.
    Bu nedenle 60/40 dengesi uygulanır.

Katmanlı mimari kuralı:
    Risk Engine bir Service katmanıdır. DetectionService ve IoTService'ten
    veri alır, kendi iş mantığını uygular ve RiskReport üretir.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from loguru import logger

from app.core.config import settings
from app.core.constants import IOT_THRESHOLDS, VIOLATION_CLASSES
from app.models.schemas.detection import DetectionResult
from app.models.schemas.iot import EnvironmentData
from app.models.schemas.risk import (
    RiskCalculateRequest,
    RiskFactor,
    RiskLevel,
    RiskReport,
)


class RiskEngine:
    """
    Görüntü + IoT verilerini birleştiren risk skorlama motoru.

    Kullanım:
        engine = RiskEngine()
        report = engine.calculate(
            detection_results=[...],
            environment=EnvironmentData(...)
        )
        print(f"Risk: {report.total_score}/100 → {report.risk_level}")
    """

    def __init__(
        self,
        vision_weight: float = None,
        iot_weight: float = None,
    ) -> None:
        self._vision_weight = vision_weight or settings.RISK_VISION_WEIGHT
        self._iot_weight = iot_weight or settings.RISK_IOT_WEIGHT

        # Ağırlıkların toplamı 1.0 olmalı
        total = self._vision_weight + self._iot_weight
        if abs(total - 1.0) > 0.01:
            logger.warning(
                f"Risk ağırlıkları toplamı 1.0 değil ({total}). Normalize ediliyor."
            )
            self._vision_weight /= total
            self._iot_weight /= total

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Ana Hesaplama
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def calculate(
        self,
        detection_results: Optional[List[DetectionResult]] = None,
        environment: Optional[EnvironmentData] = None,
        location: str = "Genel Alan",
    ) -> RiskReport:
        """
        Birleşik risk skoru hesaplar.

        Args:
            detection_results: Son tespit sonuçları (birden fazla kameradan).
            environment: Anlık çevresel sensör verileri.
            location: Bölge adı.

        Returns:
            RiskReport — 0–100 skor, seviye ve detay faktörler.
        """
        factors: List[RiskFactor] = []

        # ── Vision Skoru ──
        vision_score, vision_factors, total_violations = self._score_vision(
            detection_results or []
        )
        factors.extend(vision_factors)

        # ── IoT Skoru ──
        iot_score, iot_factors = self._score_iot(environment)
        factors.extend(iot_factors)

        # ── Birleşik Skor ──
        total_score = round(
            (vision_score * self._vision_weight)
            + (iot_score * self._iot_weight),
            1,
        )
        total_score = min(100.0, max(0.0, total_score))

        # ── Seviye Belirleme ──
        risk_level = self._determine_level(total_score)

        # ── Öneri Üretme ──
        recommendation = self._generate_recommendation(
            risk_level, vision_factors, iot_factors
        )

        report = RiskReport(
            total_score=total_score,
            risk_level=risk_level,
            vision_score=round(vision_score, 1),
            iot_score=round(iot_score, 1),
            vision_weight=self._vision_weight,
            iot_weight=self._iot_weight,
            factors=factors,
            location=location,
            camera_count=len(detection_results) if detection_results else 0,
            active_violations=total_violations,
            recommendation=recommendation,
        )

        logger.info(
            f"[RiskEngine] Skor: {total_score}/100 ({risk_level.value}) "
            f"| Vision: {vision_score:.0f} | IoT: {iot_score:.0f} "
            f"| İhlal: {total_violations}"
        )

        return report

    def calculate_from_request(self, request: RiskCalculateRequest) -> RiskReport:
        """
        API'den gelen manuel hesaplama isteğini işler.
        DetectionResult olmadan doğrudan ihlal sayılarından skor üretir.
        """
        factors: List[RiskFactor] = []

        # ── Vision Skoru (ihlal sayılarından) ──
        total_violations = sum(request.violation_counts.values())
        vision_score = self._violations_to_score(total_violations)

        for cls_name, count in request.violation_counts.items():
            if count > 0:
                factors.append(
                    RiskFactor(
                        source="vision",
                        name=cls_name,
                        raw_value=float(count),
                        score=min(100.0, count * 25.0),
                        description=f"{count} adet {cls_name} ihlali",
                    )
                )

        # ── IoT Skoru ──
        env = EnvironmentData(
            gas_level=request.gas_level or 0.0,
            temperature=request.temperature or 0.0,
            humidity=request.humidity or 0.0,
            noise_level=request.noise_level or 0.0,
            vibration=request.vibration or 0.0,
            location=request.location,
        )
        iot_score, iot_factors = self._score_iot(env)
        factors.extend(iot_factors)

        # ── Birleşik Skor ──
        total_score = round(
            (vision_score * self._vision_weight)
            + (iot_score * self._iot_weight),
            1,
        )
        total_score = min(100.0, max(0.0, total_score))
        risk_level = self._determine_level(total_score)

        return RiskReport(
            total_score=total_score,
            risk_level=risk_level,
            vision_score=round(vision_score, 1),
            iot_score=round(iot_score, 1),
            vision_weight=self._vision_weight,
            iot_weight=self._iot_weight,
            factors=factors,
            location=request.location,
            active_violations=total_violations,
            recommendation=self._generate_recommendation(
                risk_level, factors, iot_factors
            ),
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Alt Skorlama Fonksiyonları (Private)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _score_vision(
        self, results: List[DetectionResult]
    ) -> tuple[float, List[RiskFactor], int]:
        """
        Görüntü tespit sonuçlarından vision Risk skoru hesaplar.

        Mantık:
            • Her ihlal türü (NO-Hardhat/Mask/Vest) bağımsız sayılır.
            • Toplam ihlal sayısına göre 0–100 skor üretilir.
            • 0 ihlal → 0, 1-2 → 25, 3-4 → 50, 5-7 → 75, 8+ → 100

        Returns:
            (skor, faktör_listesi, toplam_ihlal)
        """
        violation_counts: Dict[str, int] = {cls: 0 for cls in VIOLATION_CLASSES}
        total_violations = 0

        for result in results:
            for det in result.detections:
                if det.class_name in VIOLATION_CLASSES:
                    violation_counts[det.class_name] += 1
                    total_violations += 1

        # Skor hesapla
        vision_score = self._violations_to_score(total_violations)

        # Faktörler oluştur
        factors: List[RiskFactor] = []
        for cls_name, count in violation_counts.items():
            if count > 0:
                factors.append(
                    RiskFactor(
                        source="vision",
                        name=cls_name,
                        raw_value=float(count),
                        score=min(100.0, count * 25.0),
                        description=f"{count} adet {cls_name} ihlali tespit edildi",
                    )
                )

        return vision_score, factors, total_violations

    def _score_iot(
        self, env: Optional[EnvironmentData]
    ) -> tuple[float, List[RiskFactor]]:
        """
        IoT çevresel verilerinden risk skoru hesaplar.

        Her sensör değeri kendi eşik aralığına göre 0–100 arasında normalize edilir.
        En yüksek tekil skor, toplam IoT skorunu belirler (max yaklaşımı):
            → Tek bir kritik sensör tüm skoru yükseltir.

        Returns:
            (skor, faktör_listesi)
        """
        if env is None:
            return 0.0, []

        factors: List[RiskFactor] = []
        sensor_scores: List[float] = []

        # ── Her sensörü değerlendir ──
        sensor_map = {
            "gas_level": (env.gas_level, "Gaz seviyesi"),
            "temperature": (env.temperature, "Sıcaklık"),
            "humidity": (env.humidity, "Nem"),
            "noise_level": (env.noise_level, "Gürültü"),
            "vibration": (env.vibration, "Titreşim"),
        }

        for sensor_key, (value, display_name) in sensor_map.items():
            thresholds = IOT_THRESHOLDS.get(sensor_key)
            if not thresholds or value == 0.0:
                continue

            # Normalize: 0 (güvenli) → 100 (kritik üstü)
            warning_thresh = thresholds["warning"]
            critical_thresh = thresholds["critical"]
            unit = thresholds["unit"]

            if value >= critical_thresh:
                score = min(100.0, 75.0 + (value - critical_thresh) / critical_thresh * 25.0)
            elif value >= warning_thresh:
                score = 25.0 + (value - warning_thresh) / (critical_thresh - warning_thresh) * 50.0
            else:
                score = (value / warning_thresh) * 25.0

            score = round(min(100.0, max(0.0, score)), 1)
            sensor_scores.append(score)

            # Sadece warning üstü değerleri faktöre ekle
            if score >= 25.0:
                factors.append(
                    RiskFactor(
                        source="iot",
                        name=sensor_key,
                        raw_value=value,
                        score=score,
                        description=f"{display_name}: {value} {unit}",
                    )
                )

        # IoT skoru: en yüksek sensör skoru (tek bir kritik değer yeterli)
        iot_score = max(sensor_scores) if sensor_scores else 0.0

        return iot_score, factors

    @staticmethod
    def _violations_to_score(count: int) -> float:
        """İhlal sayısını 0–100 skoruna dönüştürür (adımlı eğri)."""
        if count == 0:
            return 0.0
        elif count <= 2:
            return 25.0 + (count - 1) * 12.5  # 1→25, 2→37.5
        elif count <= 4:
            return 50.0 + (count - 3) * 12.5  # 3→50, 4→62.5
        elif count <= 7:
            return 75.0 + (count - 5) * 8.3   # 5→75, 7→91.6
        else:
            return 100.0

    @staticmethod
    def _determine_level(score: float) -> RiskLevel:
        """Skor → Seviye dönüşümü."""
        if score >= 76:
            return RiskLevel.CRITICAL
        elif score >= 51:
            return RiskLevel.HIGH
        elif score >= 26:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    @staticmethod
    def _generate_recommendation(
        level: RiskLevel,
        vision_factors: List[RiskFactor],
        iot_factors: List[RiskFactor],
    ) -> str:
        """Risk seviyesine göre öneri üretir."""
        if level == RiskLevel.LOW:
            return "Ortam güvenli. Rutin denetimlere devam ediniz."
        elif level == RiskLevel.MEDIUM:
            issues = [f.name for f in vision_factors + iot_factors if f.score >= 25]
            return (
                f"Dikkat gerektiren durum(lar): {', '.join(issues)}. "
                "Personeli uyarınız."
            )
        elif level == RiskLevel.HIGH:
            return (
                "YÜKSEK RİSK! Bölgedeki tüm personelin KKD kontrolü yapılmalı "
                "ve çevresel koşullar gözden geçirilmelidir."
            )
        else:  # CRITICAL
            return (
                "KRİTİK TEHLİKE! Bölge tahliye edilmeli veya acil önlem alınmalıdır. "
                "İSG sorumlusuna derhal bildirimde bulununuz."
            )
