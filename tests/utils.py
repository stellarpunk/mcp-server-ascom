"""Test utilities for ASCOM MCP server tests."""

import asyncio
import json
import os
import subprocess
import sys
import time
import select
import platform
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import httpx
import pytest
import structlog
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


logger = structlog.get_logger()


class ServiceManager:
    """Manage external services for testing."""
    
    def __init__(self):
        self.processes = {}
        self.project_root = Path(__file__).parent.parent
        self.seestar_path = self.project_root.parent / "seestar_alp"
    
    async def start_simulator(self, port: int = 4700) -> subprocess.Popen:
        """Start the seestar simulator."""
        logger.info("starting_simulator", port=port)
        
        process = subprocess.Popen(
            [sys.executable, "simulator/src/main.py", "--port", str(port)],
            cwd=str(self.seestar_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        self.processes['simulator'] = process
        
        # Wait for simulator to be ready
        await self._wait_for_port(port, timeout=10)
        return process
    
    async def start_seestar_alp(self) -> subprocess.Popen:
        """Start the seestar_alp server."""
        logger.info("starting_seestar_alp")
        
        process = subprocess.Popen(
            [sys.executable, "root_app.py"],
            cwd=str(self.seestar_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, "PYTHONPATH": str(self.seestar_path)}
        )
        
        self.processes['seestar'] = process
        
        # Wait for API to be ready
        await self._wait_for_http(
            "http://localhost:5555/api/v1/telescope/1/connected?ClientID=1&ClientTransactionID=1",
            timeout=30
        )
        return process
    
    async def _wait_for_port(self, port: int, timeout: int = 10):
        """Wait for a port to be available."""
        import socket
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.connect(('localhost', port))
                sock.close()
                return
            except:
                await asyncio.sleep(0.5)
        
        raise TimeoutError(f"Port {port} not available after {timeout}s")
    
    async def _wait_for_http(self, url: str, timeout: int = 30):
        """Wait for HTTP endpoint to be available."""
        start_time = time.time()
        
        async with httpx.AsyncClient() as client:
            while time.time() - start_time < timeout:
                try:
                    response = await client.get(url, timeout=2.0)
                    if response.status_code == 200:
                        return
                except:
                    pass
                await asyncio.sleep(1)
        
        raise TimeoutError(f"HTTP endpoint {url} not available after {timeout}s")
    
    async def is_service_running(self, url: str) -> bool:
        """Check if a service is already running."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=2.0)
                return response.status_code == 200
        except:
            return False
    
    def cleanup(self):
        """Stop all managed processes."""
        for name, process in self.processes.items():
            if process and process.poll() is None:
                logger.info("stopping_service", name=name)
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


class MCPTestClient:
    """Test client for MCP protocol testing."""
    
    def __init__(self, server_params: Optional[StdioServerParameters] = None):
        self.server_params = server_params or self._default_server_params()
        self._session = None
        self._read = None
        self._write = None
    
    def _default_server_params(self) -> StdioServerParameters:
        """Create default server parameters."""
        project_root = Path(__file__).parent.parent
        
        return StdioServerParameters(
            command=sys.executable,
            args=["-m", "ascom_mcp.server_fastmcp"],
            cwd=str(project_root),
            env={
                **dict(os.environ),
                "ASCOM_SIMULATOR_DEVICES": "localhost:4700:seestar_simulator",
                "ASCOM_KNOWN_DEVICES": "localhost:5555:seestar_alp",
                "LOG_LEVEL": "DEBUG"
            }
        )
    
    @asynccontextmanager
    async def connect(self):
        """Connect to MCP server."""
        async with stdio_client(self.server_params) as (read, write):
            self._read = read
            self._write = write
            
            async with ClientSession(read, write) as session:
                self._session = session
                await session.initialize()
                yield self
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call an MCP tool and return parsed response."""
        if not self._session:
            raise RuntimeError("Not connected to MCP server")
        
        result = await self._session.call_tool(tool_name, arguments=arguments)
        
        # Parse response
        if not result:
            return None
        
        content = result[0]
        
        # Handle different content types
        if hasattr(content, 'text'):
            # TextContent - parse JSON
            try:
                return json.loads(content.text)
            except json.JSONDecodeError:
                return {"text": content.text}
        elif hasattr(content, 'data'):
            # ImageContent or other binary
            return {"data": content.data, "mime_type": getattr(content, 'mime_type', None)}
        else:
            # Direct dict or other type
            return content
    
    async def discover_devices(self, timeout: float = 5.0) -> Dict[str, Any]:
        """Convenience method for device discovery."""
        return await self.call_tool("discover_ascom_devices", {"timeout": timeout})
    
    async def connect_telescope(self, device_id: str) -> Dict[str, Any]:
        """Convenience method for telescope connection."""
        return await self.call_tool("telescope_connect", {"device_id": device_id})
    
    async def get_telescope_position(self, device_id: str) -> Dict[str, Any]:
        """Convenience method for getting telescope position."""
        return await self.call_tool("telescope_get_position", {"device_id": device_id})


def assert_tool_success(response: Dict[str, Any], message: Optional[str] = None):
    """Assert that a tool response indicates success."""
    assert response is not None, "Response is None"
    assert response.get("success") is True, f"Tool failed: {response.get('error', response.get('message', 'Unknown error'))}"
    if message:
        assert message in str(response), f"Expected '{message}' in response"


def assert_tool_error(response: Dict[str, Any], error_code: Optional[str] = None):
    """Assert that a tool response indicates an error."""
    assert response is not None, "Response is None"
    assert response.get("success") is False, "Expected failure but got success"
    
    if error_code:
        # Check for error code in response
        actual_code = response.get("code") or response.get("error_code")
        assert actual_code == error_code, f"Expected error code '{error_code}', got '{actual_code}'"


def create_test_device_info(device_type: str = "Telescope", 
                           device_number: int = 0,
                           name: Optional[str] = None,
                           host: str = "localhost",
                           port: int = 11111) -> Dict[str, Any]:
    """Create test device info dictionary."""
    return {
        "DeviceType": device_type,
        "DeviceNumber": device_number,
        "DeviceName": name or f"Test {device_type}",
        "UniqueID": f"test-{device_type.lower()}-{device_number:03d}",
        "Host": host,
        "Port": port,
        "ApiVersion": 1
    }


@asynccontextmanager
async def managed_services():
    """Context manager for test services."""
    manager = ServiceManager()
    
    try:
        # Check if services are already running
        if not await manager.is_service_running("http://localhost:5555/api/v1/telescope/1/connected?ClientID=1&ClientTransactionID=1"):
            # Start services
            await manager.start_simulator()
            await manager.start_seestar_alp()
            logger.info("services_started")
        else:
            logger.info("services_already_running")
        
        yield manager
        
    finally:
        manager.cleanup()


# Test markers for pytest
def requires_simulator(test_func):
    """Mark test as requiring the simulator."""
    return pytest.mark.requires_simulator(test_func)


def requires_seestar(test_func):
    """Mark test as requiring seestar_alp."""
    return pytest.mark.requires_seestar(test_func)


def slow_test(test_func):
    """Mark test as slow."""
    return pytest.mark.slow(test_func)


class StdioTestHelper:
    """Helper for robust stdio testing with subprocess.Popen."""
    
    @staticmethod
    def send_json_rpc_message(proc: subprocess.Popen, message: dict):
        """Send JSON-RPC message to subprocess via stdin."""
        content = json.dumps(message)
        header = f"Content-Length: {len(content)}\r\n\r\n"
        full_message = (header + content).encode('utf-8')
        proc.stdin.write(full_message)
        proc.stdin.flush()
    
    @staticmethod
    def read_json_rpc_response(proc: subprocess.Popen, timeout: float = 10.0) -> dict:
        """Read JSON-RPC response from subprocess with robust timeout handling."""
        import select
        import sys
        
        start_time = time.time()
        headers = b""
        
        # Read headers with proper timeout and EOF handling
        while b"\r\n\r\n" not in headers:
            if time.time() - start_time > timeout:
                # Collect stderr for debugging
                stderr_data = b""
                if proc.stderr:
                    try:
                        stderr_data = proc.stderr.read()
                    except:
                        pass
                raise TimeoutError(f"Header read timeout after {timeout}s. Process exit code: {proc.poll()}. Stderr: {stderr_data.decode('utf-8', errors='ignore')}")
            
            # Use select on Unix systems for non-blocking check
            if sys.platform != "win32":
                ready, _, _ = select.select([proc.stdout], [], [], 0.1)
                if not ready:
                    # Check if process is still alive
                    if proc.poll() is not None:
                        stderr_data = proc.stderr.read() if proc.stderr else b""
                        raise EOFError(f"Process terminated with exit code {proc.returncode}. Stderr: {stderr_data.decode('utf-8', errors='ignore')}")
                    continue
            
            # Read a chunk of data
            try:
                chunk = proc.stdout.read(1)
            except Exception as e:
                raise IOError(f"Failed to read from subprocess: {e}")
                
            if not chunk:
                # EOF - check if process terminated
                if proc.poll() is not None:
                    stderr_data = proc.stderr.read() if proc.stderr else b""
                    raise EOFError(f"Process terminated unexpectedly with exit code {proc.returncode}. Stderr: {stderr_data.decode('utf-8', errors='ignore')}")
                # On Windows, empty read doesn't mean EOF, just no data available
                if sys.platform == "win32":
                    time.sleep(0.01)
                continue
                
            headers += chunk
        
        # Parse Content-Length
        header_text = headers.decode('utf-8')
        content_length = None
        for line in header_text.split('\r\n'):
            if line.startswith('Content-Length:'):
                try:
                    content_length = int(line.split(':', 1)[1].strip())
                    break
                except (ValueError, IndexError) as e:
                    raise ValueError(f"Invalid Content-Length header: {line}. Error: {e}")
        
        if content_length is None:
            raise ValueError(f"No Content-Length header found in headers: {header_text}")
        
        if content_length <= 0:
            raise ValueError(f"Invalid content length: {content_length}")
        
        # Read body with timeout
        body = b""
        while len(body) < content_length:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Body read timeout after {timeout}s. Read {len(body)}/{content_length} bytes")
            
            # Calculate how much more to read
            remaining = content_length - len(body)
            chunk_size = min(remaining, 4096)  # Read in larger chunks for efficiency
            
            # Use select on Unix systems
            if sys.platform != "win32":
                ready, _, _ = select.select([proc.stdout], [], [], 0.1)
                if not ready:
                    if proc.poll() is not None:
                        raise EOFError(f"Process terminated while reading body")
                    continue
            
            try:
                chunk = proc.stdout.read(chunk_size)
            except Exception as e:
                raise IOError(f"Failed to read body from subprocess: {e}")
                
            if not chunk:
                if proc.poll() is not None:
                    raise EOFError(f"Process terminated while reading body")
                if sys.platform == "win32":
                    time.sleep(0.01)
                continue
                
            body += chunk
        
        # Parse JSON response
        try:
            return json.loads(body.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {body.decode('utf-8', errors='ignore')}. Error: {e}")
    
    @staticmethod
    def create_test_process(timeout_startup: float = 2.0) -> subprocess.Popen:
        """Create a test subprocess with proper error handling."""
        proc = subprocess.Popen(
            [sys.executable, "-m", "ascom_mcp"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            bufsize=0  # Unbuffered for real-time communication
        )
        
        # Give server time to start
        time.sleep(timeout_startup)
        
        # Check if it started successfully
        if proc.poll() is not None:
            stderr_data = proc.stderr.read() if proc.stderr else b""
            stdout_data = proc.stdout.read() if proc.stdout else b""
            raise RuntimeError(
                f"Server failed to start. Exit code: {proc.returncode}. "
                f"Stderr: {stderr_data.decode('utf-8', errors='ignore')}. "
                f"Stdout: {stdout_data.decode('utf-8', errors='ignore')}"
            )
        
        return proc