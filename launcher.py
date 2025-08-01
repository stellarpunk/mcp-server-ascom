#!/usr/bin/env python3
"""Smart launcher for ASCOM MCP Server with auto-transport detection and hot-reload.

Automatically selects the best transport mode:
- stdio: When called by Claude Code (stdin is pipe)
- HTTP: When run manually (stdin is TTY)

Both modes support hot-reload for seamless development.
"""

import os
import sys
import subprocess
import signal
from pathlib import Path

def is_interactive():
    """Check if running interactively (TTY) or from Claude Code (pipe)."""
    return sys.stdin.isatty()

def get_transport_mode():
    """Determine transport mode based on environment and context."""
    # Allow explicit override
    mode = os.environ.get("MCP_MODE", "auto").lower()
    
    if mode == "stdio":
        return "stdio", None
    elif mode == "http":
        return "streamable-http", 3000
    elif mode == "auto":
        # Auto-detect based on TTY
        if is_interactive():
            # Manual run - use HTTP for better dev experience
            return "streamable-http", 3000
        else:
            # Called by Claude Code - use stdio
            return "stdio", None
    else:
        print(f"Unknown MCP_MODE: {mode}", file=sys.stderr)
        sys.exit(1)

def setup_environment():
    """Set up environment for MCP server."""
    env = os.environ.copy()
    
    # Ensure src is in Python path
    project_root = Path(__file__).parent
    src_path = project_root / "src"
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{src_path}:{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = str(src_path)
    
    # Pre-configure devices
    if "ASCOM_DIRECT_DEVICES" not in env:
        env["ASCOM_DIRECT_DEVICES"] = "telescope_1:localhost:5555:Seestar S50,telescope_99:localhost:4700:Simulator"
    
    return env

def run_with_hot_reload(transport, port):
    """Run server with hot-reload using watchdog."""
    env = setup_environment()
    
    # Build command
    base_cmd = [sys.executable, "-m", "ascom_mcp", "--transport", transport]
    if port:
        base_cmd.extend(["--port", str(port)])
    
    # Check if we're in interactive mode
    if is_interactive():
        print(f"🚀 Starting ASCOM MCP Server")
        print(f"📡 Transport: {transport}")
        if port:
            print(f"🌐 Port: {port}")
        print(f"🔥 Hot-reload: enabled")
        print(f"📂 Watching: *.py files")
        print("-" * 50)
    
    # Build watchmedo command
    watchmedo_cmd = [
        sys.executable, "-m", "watchdog.watchmedo",
        "auto-restart",
        "--patterns=*.py",
        "--recursive",
        "--ignore-patterns=*/tests/*;*/__pycache__/*;*/.*",
        "--",
    ] + base_cmd
    
    try:
        # Run with watchdog
        proc = subprocess.run(watchmedo_cmd, env=env)
        sys.exit(proc.returncode)
    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        # Fall back to direct run without hot-reload
        print("⚠️  Falling back to direct run (no hot-reload)", file=sys.stderr)
        proc = subprocess.run(base_cmd, env=env)
        sys.exit(proc.returncode)

def run_direct(transport, port):
    """Run server directly without hot-reload."""
    env = setup_environment()
    
    # Build command
    cmd = [sys.executable, "-m", "ascom_mcp", "--transport", transport]
    if port:
        cmd.extend(["--port", str(port)])
    
    # Run directly
    proc = subprocess.run(cmd, env=env)
    sys.exit(proc.returncode)

def main():
    """Main entry point."""
    transport, port = get_transport_mode()
    
    # Check if hot-reload is requested or beneficial
    hot_reload = os.environ.get("MCP_HOT_RELOAD", "auto").lower()
    
    if hot_reload == "off":
        run_direct(transport, port)
    elif hot_reload == "on" or (hot_reload == "auto" and is_interactive()):
        # Try hot-reload first
        try:
            # Quick check if watchdog is available
            import watchdog
            run_with_hot_reload(transport, port)
        except ImportError:
            if is_interactive():
                print("⚠️  watchdog not installed, running without hot-reload", file=sys.stderr)
                print("💡 Install with: pip install watchdog", file=sys.stderr)
            run_direct(transport, port)
    else:
        # Non-interactive stdio mode - run direct for stability
        run_direct(transport, port)

if __name__ == "__main__":
    main()