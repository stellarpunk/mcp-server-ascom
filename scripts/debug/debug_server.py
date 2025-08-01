#!/usr/bin/env python3
"""Debug script to test MCP server startup."""

import subprocess
import sys
import time
import json
import os

def test_server_startup():
    """Test basic server startup and response."""
    print("Testing MCP server startup...")
    
    # Environment with minimal dependencies
    env = os.environ.copy()
    env.update({
        "LOG_LEVEL": "DEBUG",
        "ASCOM_KNOWN_DEVICES": "",
        "ASCOM_SIMULATOR_DEVICES": "",
    })
    
    # Start server
    proc = subprocess.Popen(
        [sys.executable, "-m", "ascom_mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
        env=env
    )
    
    try:
        print("Server started, waiting for initialization...")
        time.sleep(2)
        
        # Check if server is still running
        if proc.poll() is not None:
            stderr_data = proc.stderr.read()
            stdout_data = proc.stdout.read()
            print(f"Server died! Exit code: {proc.returncode}")
            print(f"Stderr: {stderr_data.decode('utf-8', errors='ignore')}")
            print(f"Stdout: {stdout_data.decode('utf-8', errors='ignore')}")
            return False
        
        print("Server is running, sending initialize...")
        
        # Send initialize message
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
        
        print(f"Sending message ({len(message)} bytes): {message[:100]}...")
        proc.stdin.write(message)
        proc.stdin.flush()
        
        print("Message sent, reading response...")
        
        # Try to read headers
        headers = b""
        timeout = 10
        start_time = time.time()
        
        while b"\r\n\r\n" not in headers and time.time() - start_time < timeout:
            if proc.poll() is not None:
                print(f"Server died while reading headers! Exit code: {proc.returncode}")
                break
            
            chunk = proc.stdout.read(1)
            if chunk:
                headers += chunk
                print(f"Read chunk: {chunk} (total headers: {len(headers)} bytes)")
            else:
                time.sleep(0.1)
        
        if b"\r\n\r\n" in headers:
            print(f"Got headers: {headers.decode('utf-8', errors='ignore')}")
            
            # Parse content length
            content_length = None
            for line in headers.decode('utf-8').split('\r\n'):
                if line.startswith('Content-Length:'):
                    content_length = int(line.split(':')[1].strip())
                    break
            
            if content_length:
                print(f"Content length: {content_length}")
                body = proc.stdout.read(content_length)
                print(f"Response body: {body.decode('utf-8', errors='ignore')}")
                return True
            else:
                print("No content length found")
        else:
            print(f"Timeout waiting for headers. Got so far: {headers}")
            
        return False
        
    finally:
        # Read any remaining stderr
        try:
            stderr_data = proc.stderr.read()
            if stderr_data:
                print(f"Final stderr: {stderr_data.decode('utf-8', errors='ignore')}")
        except:
            pass
        
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()

if __name__ == "__main__":
    success = test_server_startup()
    print(f"Test {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)