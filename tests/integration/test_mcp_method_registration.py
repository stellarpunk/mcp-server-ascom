"""Test MCP method registration. Catches protocol errors fast."""

import json
import subprocess
import sys
import time

import pytest


def test_mcp_methods_registered():
    """Server must respond to required MCP methods."""
    proc = subprocess.Popen(
        [sys.executable, "-m", "ascom_mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
        env={**subprocess.os.environ, "LOG_LEVEL": "ERROR"}  # Reduce noise
    )
    
    try:
        # Send init
        init = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {}
            },
            "id": 1
        }
        send_json_rpc(proc, init)
        response = read_json_rpc(proc)
        assert "result" in response
        
        # Test critical methods
        methods = ["tools/list", "resources/list"]
        
        for i, method in enumerate(methods, 2):
            msg = {
                "jsonrpc": "2.0",
                "method": method,
                "params": {},
                "id": i
            }
            send_json_rpc(proc, msg)
            response = read_json_rpc(proc, timeout=2)
            
            # Fail fast on "Method not found"
            assert "error" not in response, \
                f"{method} failed: {response.get('error', {}).get('message', 'Unknown error')}"
            assert "result" in response, \
                f"{method} missing result: {response}"
    
    finally:
        proc.terminate()
        proc.wait(timeout=2)


def send_json_rpc(proc, msg):
    """Send JSON-RPC message via stdio."""
    content = json.dumps(msg)
    header = f"Content-Length: {len(content)}\r\n\r\n"
    proc.stdin.write((header + content).encode('utf-8'))
    proc.stdin.flush()


def read_json_rpc(proc, timeout=5):
    """Read JSON-RPC response. Timeout prevents hangs."""
    start = time.time()
    headers = b""
    
    # Read headers
    while b"\r\n\r\n" not in headers:
        if time.time() - start > timeout:
            raise TimeoutError("Response timeout")
        chunk = proc.stdout.read(1)
        if not chunk:
            raise EOFError("Server closed")
        headers += chunk
    
    # Parse length
    length = None
    for line in headers.decode('utf-8').split('\r\n'):
        if line.startswith('Content-Length:'):
            length = int(line.split(':')[1].strip())
            break
    
    if not length:
        raise ValueError("No Content-Length")
    
    # Read body
    body = proc.stdout.read(length)
    return json.loads(body.decode('utf-8'))