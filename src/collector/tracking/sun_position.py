"""
Sun Position Calculator

Calculates solar azimuth and elevation angles for a given location and time.
Used for sun tracking and collector alignment.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Tuple
import math


@dataclass
class Location:
    """Geographic location."""
    latitude: float   # degrees, positive = North
    longitude: float  # degrees, positive = East
    elevation: float = 0.0  # meters above sea level


@dataclass
class SunPosition:
    """Solar position in the sky."""
    azimuth: float    # degrees, 0 = North, 90 = East
    elevation: float  # degrees above horizon
    zenith: float     # degrees from vertical (90 - elevation)


def calculate_sun_position(location: Location, dt: datetime) -> SunPosition:
    """
    Calculate sun position for a given location and time.

    Uses the NOAA solar position algorithm.

    Args:
        location: Geographic location
        dt: UTC datetime

    Returns:
        SunPosition with azimuth and elevation angles
    """
    # TODO: Implement NOAA solar position algorithm
    # Reference: https://gml.noaa.gov/grad/solcalc/solareqns.PDF

    raise NotImplementedError("Sun position calculation not yet implemented")


def calculate_tracker_angles(
    sun_position: SunPosition,
    tracker_type: str = "scheffler"
) -> Tuple[float, float]:
    """
    Convert sun position to tracker motor angles.

    Args:
        sun_position: Current sun position
        tracker_type: "scheffler" (1-axis), "dish" (2-axis), "trough" (1-axis)

    Returns:
        Tuple of (primary_angle, secondary_angle) in degrees
        For 1-axis trackers, secondary_angle is always 0
    """
    # TODO: Implement tracker angle conversion for each tracker type
    raise NotImplementedError("Tracker angle calculation not yet implemented")
