"""
System State Machine

Manages overall system state and transitions between operating modes.
"""

from enum import Enum, auto
from typing import Optional


class SystemState(Enum):
    """Possible system states."""
    STARTUP = auto()       # System initializing
    IDLE = auto()          # Waiting, not collecting or generating
    TRACKING = auto()      # Collector tracking sun, storage charging
    GENERATING = auto()    # Discharging storage, generating electricity
    STOW = auto()          # Collector stowed (high wind, night, maintenance)
    FAULT = auto()         # Error condition, safe shutdown
    SHUTDOWN = auto()      # Orderly shutdown in progress


class SystemEvent(Enum):
    """Events that trigger state transitions."""
    STARTUP_COMPLETE = auto()
    SUN_AVAILABLE = auto()
    SUN_UNAVAILABLE = auto()
    POWER_DEMAND = auto()
    POWER_DEMAND_ENDED = auto()
    STORAGE_FULL = auto()
    STORAGE_DEPLETED = auto()
    HIGH_WIND = auto()
    WIND_NORMAL = auto()
    FAULT_DETECTED = auto()
    FAULT_CLEARED = auto()
    SHUTDOWN_REQUESTED = auto()


class SystemStateMachine:
    """
    State machine for system-level control.

    Coordinates collector, storage, and conversion subsystems.
    """

    def __init__(self):
        self._state = SystemState.STARTUP
        self._fault_message: Optional[str] = None

    @property
    def state(self) -> SystemState:
        """Current system state."""
        return self._state

    def handle_event(self, event: SystemEvent) -> None:
        """
        Process an event and transition state if appropriate.

        Args:
            event: The event that occurred
        """
        # TODO: Implement state transition logic
        # This should be a proper state machine with defined transitions

        if event == SystemEvent.FAULT_DETECTED:
            self._state = SystemState.FAULT
        elif event == SystemEvent.SHUTDOWN_REQUESTED:
            self._state = SystemState.SHUTDOWN
        else:
            # TODO: Implement full transition table
            pass

    def can_track(self) -> bool:
        """Check if tracking is allowed in current state."""
        return self._state in (SystemState.IDLE, SystemState.TRACKING)

    def can_generate(self) -> bool:
        """Check if generation is allowed in current state."""
        return self._state in (SystemState.IDLE, SystemState.TRACKING, SystemState.GENERATING)

    def fault(self, message: str) -> None:
        """Enter fault state with a message."""
        self._fault_message = message
        self._state = SystemState.FAULT

    @property
    def fault_message(self) -> Optional[str]:
        """Get fault message if in fault state."""
        return self._fault_message if self._state == SystemState.FAULT else None
