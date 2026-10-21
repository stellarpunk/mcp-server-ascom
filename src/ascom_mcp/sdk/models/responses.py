"""
Response models for Seestar commands.

Type-safe representations of all command responses.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SeestarResponse(BaseModel):
    """Base response from Seestar device."""

    jsonrpc: str = Field(default="2.0")
    method: str | None = None
    result: int | None = None
    code: int = Field(..., description="0 = success, non-zero = error")
    error: str | None = None
    id: int | None = None
    Timestamp: str | None = None

    @property
    def success(self) -> bool:
        """Check if operation succeeded."""
        return self.code == 0

    @property
    def error_message(self) -> str:
        """Get human-readable error message."""
        if self.code == 0:
            return "Success"
        error_map = {
            106: "Invalid parameter format",
            203: "Equipment is moving",
            207: "Failed to operate (check parameter format)",
            210: "Solar filter required",
            # Add more as discovered
        }
        return self.error or error_map.get(self.code, f"Unknown error {self.code}")


class CoordinateResponse(SeestarResponse):
    """Response containing telescope coordinates."""

    ra: float | None = Field(None, description="Right Ascension in hours")
    dec: float | None = Field(None, description="Declination in degrees")
    alt: float | None = Field(None, description="Altitude in degrees")
    az: float | None = Field(None, description="Azimuth in degrees")


class TelescopeStatus(BaseModel):
    """Complete telescope status."""

    connected: bool
    tracking: bool
    slewing: bool
    parked: bool
    ra: float = Field(..., description="Current RA in hours")
    dec: float = Field(..., description="Current Dec in degrees")
    altitude: float = Field(..., description="Current altitude in degrees")
    azimuth: float = Field(..., description="Current azimuth in degrees")
    sidereal_time: float | None = None

    @property
    def can_slew(self) -> bool:
        """Check if telescope can accept goto commands."""
        return self.connected and not self.slewing


class ViewStatus(BaseModel):
    """Current viewing status."""

    active: bool
    mode: Literal["star", "moon", "sun", "scenery", "planet"] | None = None
    target_name: str | None = None
    exposure_time_ms: int | None = None
    gain: int | None = None
    stacking: bool = False
    stack_count: int = 0

    @property
    def is_solar(self) -> bool:
        """Check if in solar viewing mode."""
        return self.mode == "sun"


class FocusPosition(BaseModel):
    """Focus position information."""

    position: int = Field(..., ge=0, le=3000)
    moving: bool = False
    temperature: float | None = None

    @property
    def focus_type(self) -> str:
        """Determine focus type from position."""
        if 1800 <= self.position <= 2000:
            return "astronomical"
        elif 500 <= self.position <= 1500:
            return "terrestrial"
        else:
            return "custom"


class StreamingStatus(BaseModel):
    """Video streaming status."""

    streaming: bool
    mjpeg_url: str | None = None
    frame_count: int = 0
    fps: float | None = None
    resolution: tuple[int, int] | None = None


class DeviceState(BaseModel):
    """Overall device state."""

    connected: bool
    initialized: bool
    battery_level: int | None = Field(None, ge=0, le=100)
    temperature_celsius: float | None = None
    free_space_gb: float | None = None
    firmware_version: str | None = None
    startup_complete: bool = False

    @property
    def battery_low(self) -> bool:
        """Check if battery is low."""
        return self.battery_level is not None and self.battery_level < 20

    @property
    def temperature_warning(self) -> bool:
        """Check if temperature is concerning."""
        if self.temperature_celsius is None:
            return False
        return self.temperature_celsius > 50 or self.temperature_celsius < -10


class FilterStatus(BaseModel):
    """Filter wheel status."""

    position: Literal[0, 1, 2]
    moving: bool = False
    filter_name: str

    @classmethod
    def from_position(cls, pos: int, moving: bool = False):
        """Create from position number."""
        names = {
            0: "Clear/Luminance",
            1: "UV/IR Cut",
            2: "Light Pollution"
        }
        return cls(
            position=pos,
            moving=moving,
            filter_name=names.get(pos, "Unknown")
        )


class StackingInfo(BaseModel):
    """Image stacking information."""

    active: bool
    mode: str | None = None
    target_name: str | None = None
    stack_count: int = 0
    total_exposure_s: float = 0
    rejection_count: int = 0

    @property
    def average_quality(self) -> float | None:
        """Calculate average frame quality."""
        total = self.stack_count + self.rejection_count
        if total == 0:
            return None
        return self.stack_count / total


class FrameCapture(BaseModel):
    """Captured frame information."""

    timestamp: datetime
    image_data: bytes = Field(..., description="JPEG image bytes")
    exposure_ms: int | None = None
    gain: int | None = None
    temperature: float | None = None

    @property
    def size_kb(self) -> float:
        """Get image size in KB."""
        return len(self.image_data) / 1024

    def save(self, filename: str) -> None:
        """Save image to file."""
        with open(filename, "wb") as f:
            f.write(self.image_data)


class ViewStatusWithPreview(ViewStatus):
    """View status with preview image."""

    preview_frame: FrameCapture | None = None
    mjpeg_url: str | None = None

    @property
    def has_preview(self) -> bool:
        """Check if preview is available."""
        return self.preview_frame is not None
