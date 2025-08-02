# v0.5.0: Parameter Validation & Helper Methods

## Summary

This release adds parameter validation and helper methods based on comprehensive OpenAPI analysis of the Seestar S50 API. The main goal is to prevent common parameter errors that cause frustrating failures, particularly the infamous Error 207 tracking bug.

## What's New

### 🛡️ Parameter Validation
- Automatic validation for 41 simulator-verified commands
- Prevents Error 207 by validating tracking parameter format
- User-friendly error messages with correct format hints
- Backward compatible - existing code continues to work

### 🚀 Helper Methods
New easy-to-use methods for common operations:
- `telescope_set_tracking()` - No more parameter confusion!
- `telescope_move_direction()` - Simple directional movement
- `telescope_auto_focus()` - Handles API typo gracefully
- `telescope_safe_startup()` - Required initialization made easy
- `telescope_get_full_status()` - Comprehensive status in one call
- Plus 5 more helper methods

### 📋 Based on OpenAPI Analysis
- Comprehensive analysis of 226+ native Seestar commands
- Validation rules derived from 41 tested methods
- Parameter formats verified with simulator
- Real hardware testing pending

## Example: Tracking Fix

**Before (Error 207):**
```python
# This looks right but fails!
telescope_custom_action(
    device_id="telescope_1",
    action="method_sync",
    parameters='{"method": "scope_set_track_state", "params": {"on": true}}'
)
# Error 207: fail to operate
```

**After (Works!):**
```python
# Option 1: Use helper method
telescope_set_tracking(device_id="telescope_1", enabled=True)

# Option 2: Validation catches the error
telescope_custom_action(...)
# ValidationError: Method 'scope_set_track_state': Use direct boolean (true/false), not object like {'on': true}
```

## Testing

- ✅ Validation tests pass
- ✅ Backward compatibility maintained
- ⏳ Real hardware testing needed

## Files Changed

- `src/ascom_mcp/validation/` - New validation layer
- `src/ascom_mcp/tools/telescope_enhanced.py` - Helper methods
- `src/ascom_mcp/server_fastmcp.py` - Enhanced with validation
- `tests/unit/test_seestar_validation.py` - Comprehensive tests
- Documentation updates

## Breaking Changes

None - fully backward compatible!

## Next Steps

1. Test with real Seestar hardware
2. Add more helper methods based on user feedback
3. Extend validation to camera and other devices