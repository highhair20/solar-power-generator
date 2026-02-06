"""
Tracker Controller

Controls the motors that rotate the solar collector to track the sun.
Supports single-axis (Scheffler, trough) and dual-axis (dish) configurations.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Protocol

from .sun_position import SunPosition, calculate_tracker_angles


class TrackerType(Enum):
    """Supported tracker configurations."""
    SCHEFFLER = "scheffler"  # 1-axis, fixed focus
    DISH = "dish"            # 2-axis
    TROUGH = "trough"        # 1-axis


class MotorInterface(Protocol):
    """Interface for motor control."""

    def move_to(self, angle: float) -> None:
        """Move to absolute angle in degrees."""
        ...

    def get_position(self) -> float:
        """Get current position in degrees."""
        ...

    def stop(self) -> None:
        """Emergency stop."""
        ...


@dataclass
class TrackerConfig:
    """Tracker configuration."""
    tracker_type: TrackerType
    primary_motor: MotorInterface
    secondary_motor: Optional[MotorInterface] = None  # For 2-axis only
    position_tolerance: float = 0.5  # degrees
    update_interval: float = 60.0    # seconds between position updates


class TrackerController:
    """
    Controls solar collector tracking.

    Calculates required angles from sun position and commands motors.
    """

    def __init__(self, config: TrackerConfig):
        self.config = config
        self._tracking_enabled = False

    def update(self, sun_position: SunPosition) -> None:
        """
        Update tracker position based on current sun position.

        Args:
            sun_position: Current sun position
        """
        if not self._tracking_enabled:
            return

        primary_angle, secondary_angle = calculate_tracker_angles(
            sun_position,
            self.config.tracker_type.value
        )

        # Move primary axis
        current_primary = self.config.primary_motor.get_position()
        if abs(current_primary - primary_angle) > self.config.position_tolerance:
            self.config.primary_motor.move_to(primary_angle)

        # Move secondary axis (2-axis trackers only)
        if self.config.secondary_motor is not None:
            current_secondary = self.config.secondary_motor.get_position()
            if abs(current_secondary - secondary_angle) > self.config.position_tolerance:
                self.config.secondary_motor.move_to(secondary_angle)

    def enable_tracking(self) -> None:
        """Enable automatic sun tracking."""
        self._tracking_enabled = True

    def disable_tracking(self) -> None:
        """Disable tracking (hold current position)."""
        self._tracking_enabled = False

    def stow(self) -> None:
        """Move to safe stow position (e.g., for high wind)."""
        self.disable_tracking()
        # TODO: Move to configured stow position
        raise NotImplementedError("Stow position not yet implemented")

    def emergency_stop(self) -> None:
        """Emergency stop all motors."""
        self._tracking_enabled = False
        self.config.primary_motor.stop()
        if self.config.secondary_motor is not None:
            self.config.secondary_motor.stop()
