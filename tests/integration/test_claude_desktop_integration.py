"""
Integration test for Claude Desktop MCP communication.

This test simulates the exact protocol flow that Claude Desktop uses
to communicate with MCP servers via stdio.
"""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest


class TestClaudeDesktopIntegration:
    """Test actual Claude Desktop integration via stdio."""
    
    @pytest.mark.asyncio
    async def test_stdio_communication_flow(self):
        """Test the complete stdio communication flow with Claude Desktop protocol."""
        # Launch the server as a subprocess (simulating uvx/Claude Desktop)
        proc = subprocess.Popen(
            [sys.executable, "-m", "ascom_mcp"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False  # Use binary mode for proper JSON-RPC handling
        )
        
        try:
            # Helper to send JSON-RPC message
            def send_message(method, params=None, id=1):
                msg = {
                    "jsonrpc": "2.0",
                    "method": method,
                    "id": id
                }
                if params:
                    msg["params"] = params
                
                content = json.dumps(msg)
                header = f"Content-Length: {len(content)}\r\n\r\n"
                full_msg = (header + content).encode('utf-8')
                proc.stdin.write(full_msg)
                proc.stdin.flush()
            
            # Helper to read JSON-RPC response
            def read_response(timeout=5):
                start_time = time.time()
                headers = b""
                
                # Read headers
                while b"\r\n\r\n" not in headers:
                    if time.time() - start_time > timeout:
                        raise TimeoutError("Timeout reading headers")
                    chunk = proc.stdout.read(1)
                    if not chunk:
                        raise EOFError("Server closed connection")
                    headers += chunk
                
                # Parse content length
                header_str = headers.decode('utf-8')
                content_length = None
                for line in header_str.split('\r\n'):
                    if line.startswith('Content-Length:'):
                        content_length = int(line.split(':')[1].strip())
                        break
                
                if content_length is None:
                    raise ValueError("No Content-Length header found")
                
                # Read content
                content = proc.stdout.read(content_length)
                return json.loads(content.decode('utf-8'))
            
            # Test 1: Initialize (this is what Claude Desktop sends first)
            send_message("initialize", {
                "protocolVersion": "2025-06-18",
                "capabilities": {
                    "roots": {"listChanged": True},
                    "experimental": {}
                },
                "clientInfo": {
                    "name": "claude-desktop-test",
                    "version": "1.0.0"
                }
            })
            
            response = read_response()
            assert "result" in response
            assert response["result"]["protocolVersion"] in ["2025-06-18", "2024-11-05"]
            assert "capabilities" in response["result"]
            assert "serverInfo" in response["result"]
            
            # Test 2: List tools (common Claude Desktop operation)
            send_message("tools/list", {}, id=2)
            
            response = read_response()
            
            # Check for the specific error we saw in production
            if "error" in response:
                assert False, f"Got error response: {response['error']}"
            
            assert "result" in response, f"No result in response: {response}"
            tools = response["result"]["tools"]
            assert isinstance(tools, list)
            assert len(tools) > 0
            
            # Verify essential tools exist
            tool_names = [t["name"] for t in tools]
            assert "discover_ascom_devices" in tool_names
            assert "telescope_connect" in tool_names
            
            # Test 3: Call a tool (device discovery)
            send_message("tools/call", {
                "name": "discover_ascom_devices",
                "arguments": {"timeout": 1.0}
            }, id=3)
            
            response = read_response()
            assert "result" in response
            assert "content" in response["result"]
            
        finally:
            # Clean shutdown
            proc.terminate()
            proc.wait(timeout=5)
    
    def test_cli_entry_point(self):
        """Test that the CLI entry point works without asyncio warnings."""
        # Run the server with a timeout to ensure it starts correctly
        proc = subprocess.Popen(
            ["mcp-server-ascom", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = proc.communicate(timeout=5)
        
        # Check for common issues
        assert proc.returncode == 0
        assert "coroutine" not in stderr.lower()
        assert "was never awaited" not in stderr.lower()
        assert "mcp-server-ascom" in stdout.lower()