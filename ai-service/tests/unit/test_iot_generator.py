"""
IoT Dummy Generator Unit Test
"""

from iot.dummy_generator import DummySensorGenerator
from app.models.schemas.iot import SensorType


class TestDummySensorGenerator:
    """DummySensorGenerator birim testleri."""

    def setup_method(self):
        self.gen = DummySensorGenerator(location="Test Alanı")

    def test_generate_single_temperature(self):
        reading = self.gen.generate_single(SensorType.TEMPERATURE)
        assert reading.sensor_type == SensorType.TEMPERATURE
        assert 15.0 <= reading.value <= 50.0
        assert reading.unit == "°C"
        assert reading.location == "Test Alanı"

    def test_generate_all_sensors(self):
        readings = self.gen.generate_all()
        assert len(readings) == len(SensorType)
        types = {r.sensor_type for r in readings}
        assert types == set(SensorType)

    def test_generate_environment(self):
        env = self.gen.generate_environment()
        assert 0 <= env.gas_level <= 100
        assert 15 <= env.temperature <= 50
        assert 25 <= env.humidity <= 95
        assert 40 <= env.noise_level <= 120
        assert 0 <= env.vibration <= 12

    def test_generate_critical(self):
        env = self.gen.generate_critical()
        assert env.gas_level >= 80
        assert env.temperature >= 42

    def test_generate_normal(self):
        env = self.gen.generate_normal()
        assert env.temperature <= 28
        assert env.gas_level <= 30

    def test_seeded_generators_are_deterministic(self):
        left = DummySensorGenerator(location="A", seed=42)
        right = DummySensorGenerator(location="A", seed=42)

        left_env = left.generate_environment()
        right_env = right.generate_environment()

        assert left_env.gas_level == right_env.gas_level
        assert left_env.temperature == right_env.temperature
        assert left_env.humidity == right_env.humidity
