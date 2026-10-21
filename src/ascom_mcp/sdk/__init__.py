"""
Seestar S50 Type-Safe SDK

A focused SDK providing safe, type-checked access to Seestar telescope commands.
Based on comprehensive OpenAPI analysis and real hardware validation.
"""

from .client import SeestarClient
from .models.commands import (
    GotoParams,
    MoveParams,
    StackingParams,
    StartupParams,
    ViewParams,
)
from .models.responses import (
    DeviceState,
    FocusPosition,
    StreamingStatus,
    TelescopeStatus,
    ViewStatus,
)

__version__ = "1.0.0"
__all__ = [
    "SeestarClient",
    "TelescopeStatus",
    "ViewStatus",
    "FocusPosition",
    "StreamingStatus",
    "DeviceState",
    "GotoParams",
    "MoveParams",
    "ViewParams",
    "StackingParams",
    "StartupParams",
]
