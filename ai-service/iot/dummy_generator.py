"""
Dummy Sensor Generator — Production-grade sahte sensör verisi üretici.

Bu modül:
    • Random walk (drift) simülasyonu ile gerçekçi sensör verileri üretir.
    • Ani zıplama (spike) yerine kademeli kayma (drift) davranışı sergiler.
    • Periyodik anomali enjeksiyonu ile alarm testi yapılabilir.
    • Her sensör bağımsız state tutar; çağrılar arasında süreklilik sağlanır.
    • async_generate() ile asenkron IoT veri akışı sağlar.

Gerçek donanım olmadığında geliştirme ve test amaçlı kullanılır.

Katmanlı mimari kuralı:
    Bu modül iot/ katmanındadır — app/ katmanından bağımsız.
    Sadece app.models.schemas.iot'a bağımlıdır.
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional
from uuid import uuid4

from app.models.schemas.iot import (
    EnvironmentData,
    SensorReading,
    SensorType,
)


@dataclass
class SensorState:
    """
    Tek bir sensörün iç durumu.
    Random walk ile önceki değere göre küçük kaymalar uygulanır.
    """

    sensor_type: SensorType
    current_value: float
    min_value: float
    max_value: float
    unit: str
    drift_speed: float  # Her adımda maksimum kayma miktarı
    sensor_id: str = field(default_factory=lambda: uuid4().hex[:8])

    def step(self, rng: random.Random) -> float:
        """
        Bir adım ilerlet — random walk + clamp.

        Değer, önceki değerin etrafında drift_speed kadar kayar.
        Sınır değerlere (min/max) yaklaştığında orta noktaya geri
        çekilme eğilimi (mean reversion) gösterir.
        """
        # Orta nokta ve mevcut sapma
        midpoint = (self.min_value + self.max_value) / 2.0
        deviation = (self.current_value - midpoint) / (self.max_value - self.min_value)

        # Mean reversion kuvveti: merkezden uzaklaştıkça geri çekme artar
        reversion_force = -deviation * 0.3

        # Random walk: Gaussian gürültü + drift
        noise = rng.gauss(0, self.drift_speed)
        delta = noise + reversion_force * self.drift_speed

        self.current_value = max(
            self.min_value,
            min(self.max_value, self.current_value + delta),
        )
        return round(self.current_value, 2)

    def inject_spike(self, magnitude: float = 1.5) -> float:
        """
        Ani anomali spike'ı enjekte eder.
        Değeri üst sınıra doğru magnitude oranında iter.
        """
        spike_target = self.min_value + (self.max_value - self.min_value) * 0.85
        self.current_value = min(
            self.max_value,
            spike_target * magnitude,
        )
        return round(self.current_value, 2)


class DummySensorGenerator:
    """
    Drift (kayma) tabanlı gerçekçi sensör verisi üretici.

    Her çağrıda değerler kademeli olarak değişir (random walk).
    Opsiyonel spike özelliği ile alarm testi yapılabilir.

    Kullanım:
        gen = DummySensorGenerator(location="İskele Bölgesi")
        reading = gen.generate_single(SensorType.TEMPERATURE)
        env_data = gen.generate_environment()

        # Asenkron stream (sonsuz):
        async for data in gen.async_generate(interval=2.0):
            process(data)
    """

    # ── Sensör konfigürasyonları ──
    # (min, max, birim, başlangıç, drift_hızı)
    _SENSOR_CONFIGS = {
        SensorType.GAS: (0.0, 100.0, "ppm", 15.0, 2.0),
        SensorType.TEMPERATURE: (10.0, 55.0, "°C", 24.0, 0.5),
        SensorType.HUMIDITY: (20.0, 95.0, "%", 55.0, 1.5),
        SensorType.NOISE: (35.0, 130.0, "dB", 60.0, 3.0),
        SensorType.VIBRATION: (0.0, 15.0, "mm/s", 2.0, 0.3),
    }

    def __init__(
        self,
        location: str = "Genel Alan",
        spike_probability: float = 0.02,
        seed: Optional[int] = None,
    ) -> None:
        """
        Args:
            location: Sensörlerin bulunduğu bölge adı.
            spike_probability: Her adımda anomali spike olasılığı (0.0 - 1.0).
        """
        self._location = location
        self._spike_probability = spike_probability
        self._rng = random.Random(seed)

        # Her sensör türü için bağımsız state oluştur
        self._states: Dict[SensorType, SensorState] = {}
        for sensor_type, (min_v, max_v, unit, start, drift) in self._SENSOR_CONFIGS.items():
            self._states[sensor_type] = SensorState(
                sensor_type=sensor_type,
                current_value=start,
                min_value=min_v,
                max_value=max_v,
                unit=unit,
                drift_speed=drift,
            )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Tekil Okuma
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def generate_single(self, sensor_type: SensorType) -> SensorReading:
        """
        Belirli bir sensör türü için tek bir okuma üretir.
        Drift simülasyonu ile önceki değere göre kademeli kayma yapar.
        """
        state = self._states[sensor_type]

        # Rastgele spike kontrolü
        if self._rng.random() < self._spike_probability:
            value = state.inject_spike()
        else:
            value = state.step(self._rng)

        return SensorReading(
            sensor_id=f"sensor_{sensor_type.value}_{state.sensor_id}",
            sensor_type=sensor_type,
            value=value,
            unit=state.unit,
            timestamp=datetime.utcnow(),
            location=self._location,
        )

    def generate_all(self) -> List[SensorReading]:
        """Tüm sensör türleri için birer okuma üretir."""
        return [self.generate_single(st) for st in SensorType]

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Toplu Çevresel Veri
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def generate_environment(self) -> EnvironmentData:
        """
        Toplu çevresel veri üretir.
        Her sensör state'i bir adım ilerletilir → drift davranışı.
        """
        gas = self._states[SensorType.GAS].step(self._rng)
        temp = self._states[SensorType.TEMPERATURE].step(self._rng)
        hum = self._states[SensorType.HUMIDITY].step(self._rng)
        noise = self._states[SensorType.NOISE].step(self._rng)
        vib = self._states[SensorType.VIBRATION].step(self._rng)

        # Spike kontrolü (herhangi bir sensörde)
        if self._rng.random() < self._spike_probability:
            target = self._rng.choice(list(self._states.values()))
            target.inject_spike()
            # Spike'tan sonra state değerini güncelle
            if target.sensor_type == SensorType.GAS:
                gas = target.current_value
            elif target.sensor_type == SensorType.TEMPERATURE:
                temp = target.current_value
            elif target.sensor_type == SensorType.HUMIDITY:
                hum = target.current_value
            elif target.sensor_type == SensorType.NOISE:
                noise = target.current_value
            elif target.sensor_type == SensorType.VIBRATION:
                vib = target.current_value

        return EnvironmentData(
            gas_level=gas,
            temperature=temp,
            humidity=hum,
            noise_level=noise,
            vibration=vib,
            timestamp=datetime.utcnow(),
            location=self._location,
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Senaryo Bazlı Üretim (Test Amaçlı)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def generate_normal(self) -> EnvironmentData:
        """
        Normal aralıkta çevresel veri üretir.
        State'i geçici olarak güvenli bölgeye çeker.
        """
        return EnvironmentData(
            gas_level=round(self._rng.uniform(5, 30), 2),
            temperature=round(self._rng.uniform(18, 28), 2),
            humidity=round(self._rng.uniform(40, 60), 2),
            noise_level=round(self._rng.uniform(45, 70), 2),
            vibration=round(self._rng.uniform(0.5, 3.0), 2),
            timestamp=datetime.utcnow(),
            location=self._location,
        )

    def generate_critical(self) -> EnvironmentData:
        """
        Kritik seviyede çevresel veri üretir (alarm testi için).
        Tüm sensörleri tehlikeli bölgeye iter.
        """
        for state in self._states.values():
            state.inject_spike(magnitude=1.2)

        return EnvironmentData(
            gas_level=self._states[SensorType.GAS].current_value,
            temperature=self._states[SensorType.TEMPERATURE].current_value,
            humidity=self._states[SensorType.HUMIDITY].current_value,
            noise_level=self._states[SensorType.NOISE].current_value,
            vibration=self._states[SensorType.VIBRATION].current_value,
            timestamp=datetime.utcnow(),
            location=self._location,
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Asenkron Stream
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def async_generate(
        self, interval: float = 5.0
    ) -> AsyncGenerator[EnvironmentData, None]:
        """
        Sonsuz asenkron sensör veri akışı (async generator).

        Args:
            interval: İki okuma arasındaki süre (saniye).

        Yields:
            EnvironmentData — her interval'de bir çevresel veri seti.

        Kullanım:
            async for data in generator.async_generate(interval=2.0):
                await process(data)
        """
        while True:
            yield self.generate_environment()
            await asyncio.sleep(interval)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Durum
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def get_current_values(self) -> Dict[str, float]:
        """Tüm sensörlerin mevcut değerlerini döner (debug amaçlı)."""
        return {
            st.value: round(state.current_value, 2)
            for st, state in self._states.items()
        }

    def reset(self) -> None:
        """Tüm sensörleri başlangıç değerlerine sıfırlar."""
        for sensor_type, (min_v, max_v, unit, start, drift) in self._SENSOR_CONFIGS.items():
            self._states[sensor_type].current_value = start
