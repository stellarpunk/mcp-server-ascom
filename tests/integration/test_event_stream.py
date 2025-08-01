"""Integration tests for Seestar event stream handling."""

import asyncio
import json
import socket
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ascom_mcp.devices.seestar_event_handler import SeestarEventHandler


class MockSeestarConnection:
    """Mock Seestar TCP connection that sends events."""
    
    def __init__(self, host="localhost", port=4700):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        
    async def connect(self):
        """Simulate connection to Seestar."""
        self.reader = AsyncMock()
        self.writer = MagicMock()
        
    async def send_event(self, event_type: str, data: dict):
        """Simulate receiving an event from Seestar."""
        event = {
            "jsonrpc": "2.0",
            "method": event_type,
            "params": data,
            "Timestamp": "1234567890.123456"
        }
        return json.dumps(event) + "\r\n"
        
    async def close(self):
        """Close mock connection."""
        if self.writer:
            self.writer.close()


class TestEventStream:
    """Test Seestar event stream handling."""
    
    @pytest.mark.asyncio
    async def test_balance_sensor_events(self):
        """Test handling BalanceSensor events."""
        handler = SeestarEventHandler()
        
        # Track received events
        received_events = []
        
        async def event_callback(event):
            received_events.append(event)
            
        handler.subscribe("BalanceSensor", event_callback)
        
        # Simulate event
        event_data = {
            "x": 0.123,
            "y": -0.045,
            "z": 0.998
        }
        
        await handler.handle_event({
            "method": "BalanceSensor",
            "params": event_data
        })
        
        # Verify event was received
        assert len(received_events) == 1
        assert received_events[0]["params"] == event_data
        
    @pytest.mark.asyncio
    async def test_focuser_move_events(self):
        """Test handling FocuserMove events during focus operations."""
        handler = SeestarEventHandler()
        
        focus_positions = []
        
        async def focus_callback(event):
            focus_positions.append(event["params"]["position"])
            
        handler.subscribe("FocuserMove", focus_callback)
        
        # Simulate focus movement sequence
        for position in [1500, 1510, 1520, 1530]:
            await handler.handle_event({
                "method": "FocuserMove",
                "params": {"position": position}
            })
            
        assert focus_positions == [1500, 1510, 1520, 1530]
        
    @pytest.mark.asyncio
    async def test_concurrent_event_handling(self):
        """Test handling multiple event types concurrently."""
        handler = SeestarEventHandler()
        
        events_by_type = {
            "BalanceSensor": [],
            "PiStatus": [],
            "FocuserMove": []
        }
        
        async def make_callback(event_type):
            async def callback(event):
                events_by_type[event_type].append(event)
            return callback
            
        # Subscribe to multiple event types
        for event_type in events_by_type:
            callback = await make_callback(event_type)
            handler.subscribe(event_type, callback)
            
        # Send mixed events
        tasks = []
        for i in range(10):
            event_type = ["BalanceSensor", "PiStatus", "FocuserMove"][i % 3]
            event = {
                "method": event_type,
                "params": {"index": i}
            }
            tasks.append(handler.handle_event(event))
            
        await asyncio.gather(*tasks)
        
        # Verify all events were handled
        total_events = sum(len(events) for events in events_by_type.values())
        assert total_events == 10
        
    @pytest.mark.asyncio
    async def test_event_error_handling(self):
        """Test error handling in event callbacks."""
        handler = SeestarEventHandler()
        
        call_count = 0
        
        async def failing_callback(event):
            nonlocal call_count
            call_count += 1
            raise ValueError("Test error")
            
        handler.subscribe("TestEvent", failing_callback)
        
        # Should not crash when callback fails
        await handler.handle_event({
            "method": "TestEvent",
            "params": {}
        })
        
        assert call_count == 1  # Callback was called despite error
        
    @pytest.mark.asyncio
    async def test_state_synchronization(self):
        """Test maintaining state from event stream."""
        handler = SeestarEventHandler()
        
        # Track device state
        device_state = {
            "temperature": None,
            "focus_position": None,
            "orientation": None
        }
        
        async def update_temperature(event):
            device_state["temperature"] = event["params"]["cpu_temp"]
            
        async def update_focus(event):
            device_state["focus_position"] = event["params"]["position"]
            
        async def update_orientation(event):
            device_state["orientation"] = event["params"]
            
        handler.subscribe("PiStatus", update_temperature)
        handler.subscribe("FocuserMove", update_focus)
        handler.subscribe("BalanceSensor", update_orientation)
        
        # Simulate state updates
        await handler.handle_event({
            "method": "PiStatus",
            "params": {"cpu_temp": 45.2}
        })
        
        await handler.handle_event({
            "method": "FocuserMove",
            "params": {"position": 1520}
        })
        
        await handler.handle_event({
            "method": "BalanceSensor",
            "params": {"x": 0.1, "y": 0.2, "z": 0.97}
        })
        
        # Verify state is synchronized
        assert device_state["temperature"] == 45.2
        assert device_state["focus_position"] == 1520
        assert device_state["orientation"]["z"] == 0.97