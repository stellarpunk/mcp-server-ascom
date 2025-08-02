"""
Command parameter models with validation.

These Pydantic models ensure type safety and parameter validation
for all Seestar commands, preventing common errors like Error 207.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class GotoParams(BaseModel):
    """Parameters for telescope goto operations."""

    ra_hour: float = Field(
        ...,
        ge=0,
        le=24,
        description="Right Ascension in hours (0-24)"
    )
    dec_deg: float = Field(
        ...,
        ge=-90,
        le=90,
        description="Declination in degrees (-90 to +90)"
    )

    @field_validator("ra_hour")
    def validate_ra(cls, v):
        if not 0 <= v <= 24:
            raise ValueError(f"RA must be 0-24 hours, got {v}")
        return v


class MoveParams(BaseModel):
    """Parameters for directional movement."""

    speed: int = Field(
        default=300,
        ge=0,
        le=1000,
        description="Movement speed (0-1000)"
    )
    angle: Literal[0, 90, 180, 270] = Field(
        ...,
        description="Direction: 0=North, 90=East, 180=South, 270=West"
    )
    dur_sec: float = Field(
        default=3.0,
        ge=0.1,
        le=30,
        description="Duration in seconds (0.1-30)"
    )

    @property
    def direction(self) -> str:
        """Get human-readable direction."""
        return {0: "north", 90: "east", 180: "south", 270: "west"}[self.angle]


class ViewParams(BaseModel):
    """Parameters for viewing modes."""

    mode: Literal["star", "moon", "sun", "scenery", "planet"] = Field(
        default="star",
        description="Viewing mode"
    )
    target_name: str | None = Field(
        None,
        description="Optional target name for goto+view"
    )

    @field_validator("mode")
    def validate_solar_safety(cls, v):
        if v == "sun":
            # In real implementation, would check solar filter status
            pass
        return v


class FocusParams(BaseModel):
    """Parameters for focus control."""

    step: int = Field(
        ...,
        ge=0,
        le=3000,
        description="Focus position (0-3000). Stars: 1800-2000, Terrestrial: 500-1500"
    )

    @property
    def focus_type(self) -> str:
        """Guess focus type from position."""
        if 1800 <= self.step <= 2000:
            return "astronomical"
        elif 500 <= self.step <= 1500:
            return "terrestrial"
        else:
            return "custom"


class FilterParams(BaseModel):
    """Parameters for filter wheel."""

    pos: Literal[0, 1, 2] = Field(
        ...,
        description="Filter position: 0=Clear, 1=UV/IR Cut, 2=Light Pollution"
    )

    @property
    def filter_name(self) -> str:
        """Get filter name from position."""
        return {
            0: "Clear/Luminance",
            1: "UV/IR Cut",
            2: "Light Pollution"
        }[self.pos]


class StackingParams(BaseModel):
    """Parameters for image stacking."""

    mode: Literal["star", "moon", "sun", "scenery", "planet"] = Field(
        default="star",
        description="Stacking mode"
    )
    target_name: str = Field(
        ...,
        min_length=1,
        description="Name for this stacking session"
    )


class StartupParams(BaseModel):
    """Parameters for telescope initialization (CRITICAL)."""

    lat: float = Field(
        ...,
        ge=-90,
        le=90,
        description="Observer latitude"
    )
    lon: float = Field(
        ...,
        ge=-180,
        le=180,
        description="Observer longitude"
    )
    time_zone: str = Field(
        default="UTC",
        description="Time zone string"
    )
    move_arm: bool = Field(
        default=True,
        description="Whether to move telescope arm during startup"
    )

    @field_validator("lat", "lon")
    def validate_coordinates(cls, v, info):
        field_name = info.field_name
        if field_name == "lat" and not -90 <= v <= 90:
            raise ValueError(f"Latitude must be -90 to 90, got {v}")
        if field_name == "lon" and not -180 <= v <= 180:
            raise ValueError(f"Longitude must be -180 to 180, got {v}")
        return v


class PresetParams(BaseModel):
    """Parameters for preset positions."""

    preset_id: str = Field(
        ...,
        min_length=1,
        description="Preset identifier (e.g., 'manhattan_skyline', 'zenith')"
    )


# Special validation for tracking to prevent Error 207
class TrackingParams(BaseModel):
    """
    Parameters for tracking control.
    
    CRITICAL: This must be a direct boolean, NOT an object like {"on": true}
    which causes Error 207!
    """

    enabled: bool = Field(
        ...,
        description="Direct boolean value for tracking state"
    )

    def to_seestar_params(self) -> bool:
        """Convert to Seestar parameter format (direct boolean)."""
        return self.enabled  # NOT {"on": self.enabled}!
