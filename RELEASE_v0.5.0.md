# Release v0.5.0 - Visual Feedback & Type Safety

## 🎯 Highlights

See what your telescope sees with new visual feedback tools and prevent parameter errors with type-safe validation.

## ✨ New Features

### Visual Feedback System
- `telescope_preview()` - Capture current view as JPEG
- `telescope_where_am_i()` - Get position with visual context
- `telescope_start_streaming()` - MJPEG live video feed
- Support for scenery mode (terrestrial viewing)

### Type-Safe SDK
- Pydantic models prevent Error 207
- Parameter validation for all Seestar commands
- Helper methods for common operations
- Comprehensive error messages

### SSE Event Streaming
- Real-time event capture from devices
- Event history with filtering
- Support for PiStatus, GotoComplete, ViewChanged
- Automatic SSE consumer on device connection

## 🔧 Improvements

- FastMCP 2.0 compliance
- Better error handling with ToolError
- Consolidated documentation
- Hot-reload development support
- Dynamic version management

## 🐛 Bug Fixes

- Fixed SSE event parsing for non-dict data
- Fixed telescope_where_am_i callable error
- Fixed import errors preventing server startup
- Fixed MCP configuration for Claude Code

## 📚 Documentation

- Simplified README with quick start
- Removed redundant documentation files
- Updated for Claude Code (not Desktop)
- Added troubleshooting guide

## ⚠️ Known Limitations

- Visual feedback may return empty images with some devices
- Park/unpark not supported on all hardware
- Some unit tests need mock updates (functionality works)

## 🚀 Installation

```bash
pip install --upgrade mcp-server-ascom==0.5.0
```

## 🙏 Thanks

Thanks to the Seestar community for testing and feedback!