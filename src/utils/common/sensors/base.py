"""
Base Sensor Classes

Abstract interfaces for sensor implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Generic, TypeVar


T = TypeVar('T')


@dataclass
class SensorReading(Generic[T]):
    """A timestamped sensor reading."""
    value: T
    timestamp: datetime
    unit: str
    sensor_id: str


class Sensor(ABC, Generic[T]):
    """Abstract base class for all sensors."""

    @abstractmethod
    def read(self) -> T:
        """Read current sensor value."""
        ...

    def read_with_timestamp(self) -> SensorReading[T]:
        """Read sensor with timestamp."""
        return SensorReading(
            value=self.read(),
            timestamp=datetime.utcnow(),
            unit=self.unit,
            sensor_id=self.sensor_id
        )

    @property
    @abstractmethod
    def unit(self) -> str:
        """Unit of measurement (e.g., '°C', 'bar', 'W')."""
        ...

    @property
    @abstractmethod
    def sensor_id(self) -> str:
        """Unique identifier for this sensor."""
        ...


class TemperatureSensor(Sensor[float]):
    """Base class for temperature sensors."""

    @property
    def unit(self) -> str:
        return "°C"


class PressureSensor(Sensor[float]):
    """Base class for pressure sensors."""

    @property
    def unit(self) -> str:
        return "bar"


class PowerSensor(Sensor[float]):
    """Base class for electrical power sensors."""

    @property
    def unit(self) -> str:
        return "W"
