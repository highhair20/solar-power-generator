"""
Collector Temperature Sensors

Monitors receiver and focal point temperatures.
"""

from dataclasses import dataclass
from typing import List, Optional

from ...common.sensors.base import Sensor, SensorReading


@dataclass
class ReceiverTemperature:
    """Temperature readings from the solar receiver."""
    inlet: float          # °C - fluid inlet temperature
    outlet: float         # °C - fluid outlet temperature
    surface: float        # °C - receiver surface temperature
    ambient: float        # °C - ambient air temperature

    @property
    def delta_t(self) -> float:
        """Temperature rise across receiver."""
        return self.outlet - self.inlet


class ReceiverTemperatureSensor(Sensor):
    """
    Multi-point temperature sensor for the solar receiver.

    Typically uses thermocouples (Type K for high temp) or RTDs.
    """

    def __init__(
        self,
        inlet_channel: int,
        outlet_channel: int,
        surface_channel: int,
        ambient_channel: int,
        adc_interface=None
    ):
        self.inlet_channel = inlet_channel
        self.outlet_channel = outlet_channel
        self.surface_channel = surface_channel
        self.ambient_channel = ambient_channel
        self.adc = adc_interface

    def read(self) -> ReceiverTemperature:
        """Read all temperature sensors."""
        # TODO: Implement actual sensor reading via ADC
        raise NotImplementedError("Temperature reading not yet implemented")

    def read_surface_temperature(self) -> float:
        """Read just the surface temperature (for safety monitoring)."""
        # TODO: Implement
        raise NotImplementedError()
