"""
Safety System

Monitors for unsafe conditions and triggers protective actions.
"""

from dataclasses import dataclass
from typing import Callable, List, Optional


@dataclass
class SafetyLimit:
    """A safety limit with thresholds."""
    name: str
    warning_threshold: float
    critical_threshold: float
    unit: str
    action_on_warning: Optional[Callable] = None
    action_on_critical: Optional[Callable] = None


class SafetyMonitor:
    """
    Monitors system parameters against safety limits.

    Triggers warnings and emergency actions when limits are exceeded.
    """

    # Default safety limits
    DEFAULT_LIMITS = [
        SafetyLimit(
            name="receiver_temperature",
            warning_threshold=700.0,
            critical_threshold=800.0,
            unit="°C"
        ),
        SafetyLimit(
            name="storage_temperature",
            warning_threshold=650.0,
            critical_threshold=700.0,
            unit="°C"
        ),
        SafetyLimit(
            name="stirling_hot_end",
            warning_threshold=750.0,
            critical_threshold=850.0,
            unit="°C"
        ),
        SafetyLimit(
            name="wind_speed",
            warning_threshold=15.0,
            critical_threshold=25.0,
            unit="m/s"
        ),
    ]

    def __init__(self, limits: Optional[List[SafetyLimit]] = None):
        self.limits = {limit.name: limit for limit in (limits or self.DEFAULT_LIMITS)}
        self._warnings: List[str] = []
        self._critical: List[str] = []

    def check(self, name: str, value: float) -> str:
        """
        Check a value against its safety limits.

        Args:
            name: Name of the parameter
            value: Current value

        Returns:
            "ok", "warning", or "critical"
        """
        if name not in self.limits:
            return "ok"

        limit = self.limits[name]

        if value >= limit.critical_threshold:
            if name not in self._critical:
                self._critical.append(name)
                if limit.action_on_critical:
                    limit.action_on_critical()
            return "critical"

        elif value >= limit.warning_threshold:
            if name not in self._warnings:
                self._warnings.append(name)
                if limit.action_on_warning:
                    limit.action_on_warning()
            return "warning"

        else:
            # Clear warnings/critical if value returns to normal
            if name in self._warnings:
                self._warnings.remove(name)
            if name in self._critical:
                self._critical.remove(name)
            return "ok"

    def emergency_shutdown(self) -> None:
        """Execute emergency shutdown procedure."""
        # TODO: Implement emergency shutdown
        # - Stop all motors
        # - Close valves
        # - Stow collector
        # - Disconnect generator load
        raise NotImplementedError("Emergency shutdown not yet implemented")

    @property
    def has_warnings(self) -> bool:
        """Check if any warnings are active."""
        return len(self._warnings) > 0

    @property
    def has_critical(self) -> bool:
        """Check if any critical conditions are active."""
        return len(self._critical) > 0
