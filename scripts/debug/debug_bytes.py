#!/usr/bin/env python3
"""Debug script to see exactly what bytes are exchanged."""

import subprocess
import sys
import time
import json
import os

def hex_dump(data, label):
    """Print hex dump of data."""
    print(f"\n=== {label} ===")
    print(f"Length: {len(data)} bytes")
    if data:
        hex_str = data.hex()
        print(f"Hex: {hex_str}")
        print(f"Ascii: {repr(data.decode('utf-8', errors='replace'))}")
    else:
        print("No data")

def test_bytes_exchange():
    """Test exact byte exchange with server."""
    print("Starting byte-level debug test...")
    
    # Environment with minimal dependencies
    env = os.environ.copy()
    env.update({
        "LOG_LEVEL": "CRITICAL",
        "ASCOM_KNOWN_DEVICES": "",
        "ASCOM_SIMULATOR_DEVICES": "",
    })
    
    # Start server
    proc = subprocess.Popen(
        [sys.executable, "-m", "ascom_mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,  # Capture stderr to see what's there
        text=False,
        env=env
    )
    
    try:
        print("Server started, waiting 1 second...")
        time.sleep(1)
        
        # Check if server is still running
        if proc.poll() is not None:
            stderr_data = proc.stderr.read()
            stdout_data = proc.stdout.read()
            hex_dump(stderr_data, "SERVER STDERR (death)")
            hex_dump(stdout_data, "SERVER STDOUT (death)")
            print(f"Server died! Exit code: {proc.returncode}")
            return False
        
        print("Server is running, preparing message...")
        
        # Create initialize message
        init_msg = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "debug-test", "version": "1.0"}
            },
            "id": 1
        }
        
        content = json.dumps(init_msg)
        header = f"Content-Length: {len(content)}\r\n\r\n"
        message = (header + content).encode('utf-8')
        
        hex_dump(message, "SENDING TO SERVER")
        
        print("Writing to stdin...")
        proc.stdin.write(message)
        proc.stdin.flush()
        
        print("Message sent, waiting 2 seconds...")
        time.sleep(2)
        
        # Check stderr first
        stderr_data = proc.stderr.read(8192)  # Read some stderr
        if stderr_data:
            hex_dump(stderr_data, "SERVER STDERR")
        
        # Try to read any stdout data that's available
        print("Attempting to read from stdout...")
        
        # Try non-blocking read
        import select
        if select.select([proc.stdout], [], [], 0)[0]:
            stdout_data = proc.stdout.read(8192)
            hex_dump(stdout_data, "SERVER STDOUT")
            
            # Try to parse as JSON-RPC
            if b"Content-Length:" in stdout_data:
                print("\nFound Content-Length header!")
                # Try to extract and parse
                parts = stdout_data.split(b"\r\n\r\n", 1)
                if len(parts) == 2:
                    headers, body_start = parts
                    print(f"Headers: {headers.decode('utf-8', errors='replace')}")
                    print(f"Body start: {body_start.decode('utf-8', errors='replace')}")
            else:
                print("No Content-Length header found in stdout")
        else:
            print("No stdout data available")
        
        print("Checking if server is still alive...")
        if proc.poll() is not None:
            print(f"Server exited with code: {proc.returncode}")
        else:
            print("Server is still running")
        
        return True
        
    finally:
        print("Cleaning up...")
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()

if __name__ == "__main__":
    test_bytes_exchange()