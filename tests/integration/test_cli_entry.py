"""
Test CLI entry point to catch asyncio and import issues early.
"""

import subprocess
import sys
import time

import pytest


class TestCLIEntry:
    """Test the command-line interface entry points."""
    
    def test_module_entry_point(self):
        """Test running as python -m ascom_mcp."""
        proc = subprocess.Popen(
            [sys.executable, "-m", "ascom_mcp", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = proc.communicate(timeout=5)
        
        assert proc.returncode == 0
        assert "0.2" in stdout  # Version check
        assert not stderr  # No errors
    
    def test_script_entry_point(self):
        """Test running via the installed script entry point."""
        # This simulates what happens when installed via pip/uvx
        proc = subprocess.Popen(
            [sys.executable, "-c", 
             "from ascom_mcp.server import run; print('Entry point OK')"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = proc.communicate(timeout=5)
        
        assert proc.returncode == 0
        assert "Entry point OK" in stdout
        assert "coroutine" not in stderr
        assert "was never awaited" not in stderr
    
    def test_server_starts_without_hanging(self):
        """Test that server starts and responds to shutdown signal."""
        proc = subprocess.Popen(
            [sys.executable, "-m", "ascom_mcp"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give it a moment to start
        time.sleep(1)
        
        # Should still be running
        assert proc.poll() is None
        
        # Terminate gracefully
        proc.terminate()
        try:
            stdout, stderr = proc.communicate(timeout=5)
            assert proc.returncode in [-15, 0]  # SIGTERM or clean exit
        except subprocess.TimeoutExpired:
            proc.kill()
            pytest.fail("Server did not shut down gracefully")
    
    def test_help_output(self):
        """Test --help flag works correctly."""
        proc = subprocess.Popen(
            [sys.executable, "-m", "ascom_mcp", "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = proc.communicate(timeout=5)
        
        assert proc.returncode == 0
        assert "ASCOM MCP Server" in stdout
        assert "--version" in stdout
        assert "--log-level" in stdout