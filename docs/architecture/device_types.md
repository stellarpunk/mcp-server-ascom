# ASCOM Device Types

## Overview

[HIGH] ASCOM standards support multiple astronomy device types, each defined by a specific interface to allow software control and interoperability across telescope equipment.
Source: https://ascom-standards.org/newdocs/interfaces.html (Accessed: 2025-07-30)

[HIGH] These interfaces are functionally identical across classic COM-based ASCOM and modern Alpaca network protocols.
Source: https://ascom-standards.org/alpyca/alpacaclasses.html (Accessed: 2025-07-30)

## Complete List of ASCOM Device Types

### 1. Telescope

**Purpose**: Controls telescope mounts for pointing, slewing, tracking, and guiding operations.

**Key Capabilities**:
- Slew to celestial coordinates (RA/Dec, Alt/Az)
- Track celestial objects accounting for Earth's rotation
- Park/unpark mount
- Support for different mount types (equatorial, alt-azimuth)
- Pulse guiding for astrophotography

[HIGH] The Telescope interface is one of the most complex, supporting various coordinate systems and mount configurations.
Source: https://ascom-standards.org/newdocs/telescope.html (Accessed: 2025-07-30)

### 2. Camera

**Purpose**: Manages imaging cameras for astrophotography and scientific imaging.

**Key Capabilities**:
- Control exposure duration and parameters
- Download images from camera
- Set binning, subframe, and gain settings
- Control camera cooling (if available)
- Monitor camera temperature and status

[HIGH] Camera interface supports both still image capture and video streaming capabilities.
Source: https://ascom-standards.org/api/AlpacaDeviceAPI_v1.yaml (Accessed: 2025-07-30)

### 3. Focuser

**Purpose**: Controls motorized focusers for precise optical system focusing.

**Key Capabilities**:
- Move to absolute or relative positions
- Temperature compensation
- Report position in steps
- Support for both absolute and relative focusers
- Backlash compensation

[INFERENCE][HIGH] Focuser control is critical for astrophotography as temperature changes during the night require focus adjustments.
Source: Based on ASCOM device type descriptions (2025-07-30)

### 4. FilterWheel

**Purpose**: Controls motorized filter wheels for filter selection and positioning.

**Key Capabilities**:
- Select filters by position or name
- Report current filter position
- Support for various wheel sizes (5, 6, 7, 8+ positions)
- Filter name management

### 5. Dome

**Purpose**: Controls observatory domes, roll-off roofs, and similar enclosures.

**Key Capabilities**:
- Open/close shutter or roof
- Rotate dome to azimuth position
- Slave dome to telescope (automatic following)
- Report dome status and position
- Safety interlocks

[HIGH] Dome interface includes safety features to prevent equipment damage during automated operations.
Source: https://ascom-standards.org/api/AlpacaDeviceAPI_v1.yaml (Accessed: 2025-07-30)

### 6. CoverCalibrator

**Purpose**: Controls telescope covers and flat field calibration light sources.

**Key Capabilities**:
- Open/close telescope cover
- Control calibration light brightness
- Provide uniform illumination for flat frames
- Report cover and calibrator status

[HIGH] CoverCalibrator devices support combined cover and flat-field calibration functionality.
Source: https://ascom-standards.org/alpyca/alpacaclasses.html (Accessed: 2025-07-30)

### 7. Rotator

**Purpose**: Controls field rotators to maintain image orientation or derotate field.

**Key Capabilities**:
- Rotate to specific position angle
- Report current angle
- Support for mechanical angle vs sky position angle
- Reverse rotation direction if needed

### 8. ObservingConditions

**Purpose**: Reports environmental and weather data from sensors.

**Key Capabilities**:
- Temperature, humidity, pressure readings
- Wind speed and direction
- Cloud coverage estimation
- Sky quality measurements
- Rain detection
- Time-series data with averaging periods

[HIGH] ObservingConditions interface supplies real-time and historical data from environmental sensors for observatory safety and automation.
Source: https://ascom-standards.org/alpyca/alpacaclasses.html (Accessed: 2025-07-30)

### 9. SafetyMonitor

**Purpose**: Provides binary safe/unsafe status for automated observatory protection.

**Key Capabilities**:
- Report overall safety status
- Aggregate multiple safety conditions
- Trigger automated shutdown procedures
- Support for custom safety logic

[HIGH] SafetyMonitor interfaces with devices or software that aggregate environmental and system safety information.
Source: https://ascom-standards.org/alpyca/alpacaclasses.html (Accessed: 2025-07-30)

### 10. Switch (Not in original list but found in repositories)

**Purpose**: Controls generic switches, relays, and digital I/O devices.

**Key Capabilities**:
- Control multiple switches/relays
- Read switch states
- Support for analog values
- Name management for switches

[INFERENCE][HIGH] Based on GitHub analysis, Switch devices are commonly implemented for observatory automation:
- Power control for equipment
- Dew heater control
- Light control
Evidence: Multiple ESP8266/ESP32 ASCOM Switch implementations found
Source: GitHub repositories analysis (2025-07-30)

## Common Patterns Across Device Types

[HIGH] All ASCOM device types share common endpoints and patterns:
Source: https://ascom-standards.org/api/AlpacaDeviceAPI_v1.yaml (Accessed: 2025-07-30)

### Standard Properties (All Devices)
- `Connected`: Get/set connection state
- `Description`: Device description string
- `DriverInfo`: Driver information
- `DriverVersion`: Driver version string
- `InterfaceVersion`: ASCOM interface version supported
- `Name`: Short device name
- `SupportedActions`: List of device-specific actions

### Standard Methods (All Devices)
- `Action`: Execute device-specific commands
- `CommandBlind`: Send command without response
- `CommandBool`: Send command returning boolean
- `CommandString`: Send command returning string

### Error Handling
[HIGH] All devices use consistent error codes and JSON error responses:
- 400: Bad Request - Invalid parameters
- 500: Internal Server Error - Device error
- Transaction IDs for request tracking
Source: https://ascom-standards.org/api/AlpacaDeviceAPI_v1.yaml (Accessed: 2025-07-30)

## Implementation Considerations

### Device Numbering
[HIGH] Devices are identified by type and number (e.g., /telescope/0, /camera/1)
Source: https://ascom-standards.org/api/AlpacaDeviceAPI_v1.yaml (Accessed: 2025-07-30)

### Multi-Device Support
[INFERENCE][HIGH] The numbering scheme allows multiple devices of the same type to be controlled simultaneously, essential for complex observatory setups.
Evidence: URL pattern /{device_type}/{device_number}/ in all API endpoints
Source: API documentation analysis (2025-07-30)

### Extensibility
[HIGH] The Action/CommandX methods allow device-specific functionality beyond the standard interface, enabling innovation while maintaining compatibility.
Source: https://ascom-standards.org/api/AlpacaDeviceAPI_v1.yaml (Accessed: 2025-07-30)