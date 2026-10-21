"""
Seestar command validation based on OpenAPI specification findings.

This module prevents common parameter errors discovered during API analysis,
particularly the tracking parameter format bug (Error 207).
"""

from typing import Any, Dict, Optional, Union
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when command validation fails."""
    def __init__(self, message: str, correct_format: Optional[str] = None):
        super().__init__(message)
        self.correct_format = correct_format


class SeestarValidator:
    """Validates Seestar commands against known parameter formats."""
    
    # Commands verified in simulator testing (41 methods)
    SIMULATOR_VERIFIED = {
        # System Control
        "get_device_state", "pi_shutdown", "pi_reboot", "get_setting", "set_setting",
        "pi_station_state", "pi_is_verified",
        
        # Telescope Movement
        "scope_goto", "scope_speed_move", "scope_get_equ_coord", "scope_sync",
        "scope_park", "set_user_location",
        
        # Imaging & Stacking
        "iscope_start_view", "iscope_stop_view", "iscope_start_stack", 
        "get_stack_info", "get_view_state", "get_camera_state", "get_camera_exp_and_bin",
        
        # Focus Control
        "get_focuser_position", "move_focuser", "start_auto_focuse", "stop_auto_focuse",
        
        # Filter Wheel
        "get_wheel_state", "get_wheel_setting", "set_wheel_position",
        
        # Polar Alignment
        "start_polar_align", "stop_polar_align",
    }
    
    # Known parameter formats from OpenAPI analysis
    PARAM_VALIDATORS = {
        # CRITICAL: Tracking must be direct boolean!
        "scope_set_track_state": {
            "type": "boolean",
            "error_hint": "Use direct boolean (true/false), not object like {'on': true}"
        },
        
        # Coordinate validation
        "scope_goto": {
            "type": "object",
            "properties": {
                "ra_hour": {"type": "number", "min": 0, "max": 24},
                "dec_deg": {"type": "number", "min": -90, "max": 90}
            }
        },
        
        # Movement parameters
        "scope_speed_move": {
            "type": "object",
            "properties": {
                "speed": {"type": "number", "min": 0, "max": 1000},
                "angle": {"type": "number", "min": 0, "max": 360},
                "dur_sec": {"type": "number", "min": 0, "max": 60}
            }
        },
        
        # Location settings
        "set_user_location": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "min": -90, "max": 90},
                "lon": {"type": "number", "min": -180, "max": 180}
            }
        },
        
        # Focus position
        "move_focuser": {
            "type": "object",
            "properties": {
                "step": {"type": "number", "min": 0, "max": 3000}
            }
        },
        
        # No parameters
        "get_device_state": {"type": "none"},
        "pi_shutdown": {"type": "none"},
        "pi_reboot": {"type": "none"},
        "scope_park": {"type": "none"},
        "start_auto_focuse": {"type": "none"},  # Note: API typo
        "stop_auto_focuse": {"type": "none"},
    }
    
    @classmethod
    def validate_command(cls, method: str, params: Any) -> Dict[str, Any]:
        """
        Validate command parameters against known formats.
        
        Args:
            method: The Seestar method name
            params: The parameters to validate
            
        Returns:
            Validated parameters ready for sending
            
        Raises:
            ValidationError: If parameters don't match expected format
        """
        # Check if method is known
        validator = cls.PARAM_VALIDATORS.get(method)
        if not validator:
            # Unknown method - pass through but log
            if method not in cls.SIMULATOR_VERIFIED:
                logger.warning(f"Unknown method '{method}' - no validation available")
            return {"method": method, "params": params}
        
        # Validate based on type
        param_type = validator["type"]
        
        if param_type == "none":
            # No parameters expected
            if params is not None:
                raise ValidationError(
                    f"Method '{method}' expects no parameters, got {type(params).__name__}"
                )
            return {"method": method}
        
        elif param_type == "boolean":
            # Direct boolean parameter (tracking bug prevention!)
            if isinstance(params, dict):
                hint = validator.get("error_hint", "Expected boolean, got dict")
                raise ValidationError(
                    f"Method '{method}': {hint}",
                    correct_format="true or false"
                )
            return {"method": method, "params": bool(params)}
        
        elif param_type == "object":
            # Object with properties
            if not isinstance(params, dict):
                raise ValidationError(
                    f"Method '{method}' expects object parameters, got {type(params).__name__}"
                )
            
            # Validate properties if defined
            if "properties" in validator:
                validated_params = {}
                for prop, rules in validator["properties"].items():
                    if prop in params:
                        value = params[prop]
                        
                        # Type check
                        if rules["type"] == "number" and not isinstance(value, (int, float)):
                            raise ValidationError(
                                f"Method '{method}': property '{prop}' must be a number"
                            )
                        
                        # Range check
                        if "min" in rules and value < rules["min"]:
                            raise ValidationError(
                                f"Method '{method}': {prop} must be >= {rules['min']}, got {value}"
                            )
                        if "max" in rules and value > rules["max"]:
                            raise ValidationError(
                                f"Method '{method}': {prop} must be <= {rules['max']}, got {value}"
                            )
                        
                        validated_params[prop] = value
                    elif prop in ["ra_hour", "dec_deg", "lat", "lon", "step"]:
                        # Required coordinate/position parameters
                        raise ValidationError(
                            f"Method '{method}': missing required parameter '{prop}'"
                        )
                
                return {"method": method, "params": validated_params}
            
            return {"method": method, "params": params}
        
        # Default pass-through
        return {"method": method, "params": params}
    
    @classmethod
    def get_method_info(cls, method: str) -> Dict[str, Any]:
        """Get information about a method's parameters and validation."""
        return {
            "method": method,
            "verified": method in cls.SIMULATOR_VERIFIED,
            "validator": cls.PARAM_VALIDATORS.get(method, {}),
            "hint": cls.PARAM_VALIDATORS.get(method, {}).get("error_hint")
        }