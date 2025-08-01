"""Minimal service management for ASCOM MCP and seestar_alp"""
from invoke import task
import subprocess
import time
import requests
import os


@task
def start_seestar(c):
    """Start seestar_alp server"""
    print("Starting seestar_alp...")
    c.run("cd ../seestar_alp && source venv/bin/activate && python root_app.py", 
          pty=True, asynchronous=True)


@task
def start_mcp(c):
    """Start ASCOM MCP server"""
    print("Starting ASCOM MCP...")
    c.run("source .venv/bin/activate && python -m ascom_mcp", 
          pty=True, asynchronous=True)


@task
def start(c):
    """Start all services"""
    start_seestar(c)
    time.sleep(3)  # Let seestar_alp start first
    start_mcp(c)
    print("\nServices starting... Check with: invoke status")


@task
def status(c):
    """Check service status"""
    print("\n=== Service Status ===")
    
    # Check seestar_alp
    try:
        r = requests.get("http://localhost:5555/management/v1/description", timeout=2)
        if r.status_code == 200:
            print("✅ seestar_alp: Running on port 5555")
        else:
            print("⚠️  seestar_alp: Responding but may have issues")
    except:
        print("❌ seestar_alp: Not running")
    
    # Check MCP server
    result = c.run("ps aux | grep 'python -m ascom_mcp' | grep -v grep", 
                   hide=True, warn=True)
    if result.ok:
        print("✅ ASCOM MCP: Running")
    else:
        print("❌ ASCOM MCP: Not running")
    
    # Check telescope connection
    try:
        r = requests.get("http://localhost:5555/api/v1/telescope/0/connected?ClientID=1&ClientTransactionID=1", 
                        timeout=2)
        data = r.json()
        if r.status_code == 200 and data.get("Value"):
            print("✅ Telescope: Connected")
        else:
            print("⚠️  Telescope: Not connected")
    except:
        print("⚠️  Telescope: Status unknown")


@task  
def stop(c):
    """Stop all services"""
    print("Stopping services...")
    c.run("pkill -f 'python root_app.py'", warn=True)
    c.run("pkill -f 'python -m ascom_mcp'", warn=True)
    print("Services stopped")


@task
def logs(c, tail=50):
    """Tail combined logs for events
    
    Args:
        tail: Number of lines to show (default: 50)
    """
    print(f"Tailing last {tail} lines of logs (Ctrl+C to stop)...")
    c.run(f"cd ../seestar_alp && tail -f -{tail} alpyca.log seestar_alp.log | grep -E 'event|Event|STATUS|status|connected'", 
          pty=True)


@task
def test_connection(c):
    """Quick test of telescope connection"""
    print("\nTesting telescope connection...")
    try:
        # Get telescope info
        r = requests.put("http://localhost:5555/api/v1/telescope/0/action",
                        data={
                            "Action": "get_device_info",
                            "Parameters": "{}",
                            "ClientID": 1,
                            "ClientTransactionID": 1
                        })
        if r.status_code == 200:
            data = r.json()
            print(f"✅ Device info: {data.get('Value', 'Unknown')}")
        else:
            print(f"❌ Failed to get device info: {r.status_code}")
    except Exception as e:
        print(f"❌ Connection test failed: {e}")


@task
def dev(c, hot=False, transport="stdio", log_file=None):
    """Run MCP server in development mode
    
    Args:
        hot: Enable hot-reload with watchmedo
        transport: Transport type (stdio, sse, streamable-http)
        log_file: Optional log file to capture output (e.g. 'mcp.log')
    """
    print("🚀 Starting ASCOM MCP in development mode...")
    env = os.environ.copy()
    env.update({
        "PYTHONPATH": "src",
        "ASCOM_DIRECT_DEVICES": "telescope_1:localhost:5555:Seestar S50,telescope_99:localhost:4700:Simulator"
    })
    
    base_cmd = f"python -m ascom_mcp --transport {transport}"
    if transport != "stdio":
        base_cmd += " --port 3000"
    
    # Add logging output (captures both stdout and stderr)
    if log_file:
        base_cmd = f"{base_cmd} 2>&1 | tee {log_file}"
        print(f"📝 Logging output to {log_file} (including stderr)")
        print(f"   Tail in another terminal: tail -f {log_file}")
        print(f"   Filter events: tail -f {log_file} | grep -E 'EventBus|event|blinker'")
    
    if hot:
        # Install watchdog if needed
        c.run("pip install watchdog", hide=True, warn=True)
        print("🔥 Hot-reload enabled (watching for *.py changes)")
        c.run(f"watchmedo auto-restart --patterns='*.py' --recursive --ignore-patterns='*/tests/*;*/__pycache__/*' -- {base_cmd}", 
              env=env, pty=True, shell="/bin/bash")
    else:
        c.run(base_cmd, env=env, pty=True)


@task
def test_quick(c):
    """Quick smoke tests"""
    print("🧪 Running quick smoke tests...")
    c.run("pytest -m smoke -v", pty=True)


@task
def clean(c):
    """Clean logs and temporary files"""
    print("🧹 Cleaning up...")
    c.run("rm -f *.log mcp_server*.log", warn=True)
    print("✅ Cleaned up log files")


@task
def monitor(c, follow=True):
    """Monitor MCP server output
    
    Args:
        follow: Follow log file (like tail -f)
    """
    log_file = "mcp_dev.log"
    if not os.path.exists(log_file):
        print(f"❌ Log file {log_file} not found.")
        print("   Start server with: invoke dev --hot --log-file=mcp_dev.log")
        return
    
    if follow:
        print(f"📜 Following {log_file} (Ctrl+C to stop)...")
        c.run(f"tail -f {log_file}", pty=True)
    else:
        print(f"📜 Last 50 lines of {log_file}:")
        c.run(f"tail -n 50 {log_file}", pty=True)