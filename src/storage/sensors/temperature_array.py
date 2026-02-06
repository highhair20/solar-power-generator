"""
Storage Temperature Array

Multi-point temperature monitoring for thermal stratification analysis.
"""

from dataclasses import dataclass
from typing import List
import statistics


@dataclass
class StorageTemperatures:
    """Temperature profile of the thermal storage."""
    readings: List[float]  # °C, ordered from top to bottom of storage
    timestamps: List[float]  # Unix timestamps

    @property
    def top(self) -> float:
        """Temperature at top of storage (hottest)."""
        return self.readings[0]

    @property
    def bottom(self) -> float:
        """Temperature at bottom of storage (coolest)."""
        return self.readings[-1]

    @property
    def average(self) -> float:
        """Average temperature across all sensors."""
        return statistics.mean(self.readings)

    @property
    def stratification(self) -> float:
        """Temperature difference top to bottom."""
        return self.top - self.bottom

    def energy_content(self, mass_kg: float, specific_heat: float = 840.0) -> float:
        """
        Estimate stored thermal energy.

        Args:
            mass_kg: Total mass of storage medium (kg)
            specific_heat: Specific heat capacity (J/kg·K), default is sand

        Returns:
            Energy in kWh above 20°C reference
        """
        reference_temp = 20.0  # °C
        delta_t = self.average - reference_temp
        energy_joules = mass_kg * specific_heat * delta_t
        return energy_joules / 3.6e6  # Convert J to kWh


class StorageTemperatureArray:
    """
    Vertical array of temperature sensors in the storage silo.

    Typically 5-10 thermocouples or RTDs distributed from top to bottom.
    """

    def __init__(self, sensor_channels: List[int], adc_interface=None):
        """
        Args:
            sensor_channels: ADC channel numbers, ordered top to bottom
            adc_interface: ADC hardware interface
        """
        self.channels = sensor_channels
        self.adc = adc_interface

    def read(self) -> StorageTemperatures:
        """Read all temperature sensors."""
        # TODO: Implement actual sensor reading
        raise NotImplementedError("Temperature array reading not yet implemented")

    @property
    def sensor_count(self) -> int:
        """Number of sensors in the array."""
        return len(self.channels)
