"""
SSE consumer for Seestar event streaming.

Connects to seestar_alp's Server-Sent Events endpoints to capture
real-time telescope events and forward them to the MCP event system.
"""

import asyncio
import json
import re
from typing import Optional, Dict, Any
import aiohttp

from ascom_mcp.ascom_logging import StructuredLogger

logger = StructuredLogger("ascom.sse.consumer")


class SeestarSSEConsumer:
    """Consumes SSE events from seestar_alp and forwards to MCP."""
    
    def __init__(self, event_manager, base_url: str = "http://localhost:7556"):
        """Initialize SSE consumer.
        
        Args:
            event_manager: The EventStreamManager instance
            base_url: Base URL for seestar_alp SSE endpoints
        """
        self.event_manager = event_manager
        self.base_url = base_url
        self._tasks: Dict[str, asyncio.Task] = {}
        self._sessions: Dict[str, aiohttp.ClientSession] = {}
        
    async def start_consuming(self, device_id: str, device_num: int = 1) -> None:
        """Start consuming events for a device.
        
        Args:
            device_id: MCP device identifier
            device_num: Seestar device number (default 1)
        """
        if device_id in self._tasks:
            logger.debug(f"Already consuming events for {device_id}")
            return
            
        # Create session for this device
        self._sessions[device_id] = aiohttp.ClientSession()
        
        # Start consumer task
        task = asyncio.create_task(self._consume_events(device_id, device_num))
        self._tasks[device_id] = task
        
        logger.info(
            f"Started SSE consumer for {device_id}",
            extra={"device_id": device_id, "device_num": device_num}
        )
        
    async def stop_consuming(self, device_id: str) -> None:
        """Stop consuming events for a device.
        
        Args:
            device_id: MCP device identifier
        """
        if device_id not in self._tasks:
            return
            
        # Cancel task
        task = self._tasks.pop(device_id)
        task.cancel()
        
        # Close session
        if device_id in self._sessions:
            session = self._sessions.pop(device_id)
            await session.close()
            
        logger.info(f"Stopped SSE consumer for {device_id}")
        
    async def _consume_events(self, device_id: str, device_num: int) -> None:
        """Consume events from SSE endpoint.
        
        Args:
            device_id: MCP device identifier
            device_num: Seestar device number
        """
        url = f"{self.base_url}/{device_num}/events"
        session = self._sessions[device_id]
        
        while True:
            try:
                logger.debug(f"Connecting to SSE endpoint: {url}")
                
                async with session.get(url, timeout=None) as response:
                    if response.status != 200:
                        logger.error(
                            f"SSE connection failed: {response.status}",
                            extra={"url": url, "status": response.status}
                        )
                        await asyncio.sleep(5)  # Retry delay
                        continue
                        
                    logger.info(f"Connected to SSE stream for {device_id}")
                    
                    # Process event stream
                    async for line in response.content:
                        if not line:
                            continue
                            
                        line_str = line.decode('utf-8').strip()
                        
                        # Parse SSE format
                        if line_str.startswith('data: '):
                            event_data = self._parse_event(line_str[6:])
                            if event_data:
                                await self._forward_event(device_id, event_data)
                                
            except asyncio.CancelledError:
                logger.debug(f"SSE consumer cancelled for {device_id}")
                break
            except aiohttp.ClientError as e:
                logger.error(
                    f"SSE connection error: {e}",
                    extra={"device_id": device_id, "error": str(e)}
                )
                await asyncio.sleep(5)  # Retry delay
            except Exception as e:
                logger.error(
                    f"Unexpected error in SSE consumer: {e}",
                    extra={"device_id": device_id, "error": str(e)}
                )
                await asyncio.sleep(5)  # Retry delay
                
    def _parse_event(self, data: str) -> Optional[Dict[str, Any]]:
        """Parse event from SSE data format.
        
        Expected format: <pre>2025-08-01 10:06:55.8: {"Event": "PiStatus", ...}</pre>
        
        Args:
            data: Raw SSE data string
            
        Returns:
            Parsed event dict or None
        """
        try:
            # Extract JSON from HTML wrapper
            match = re.search(r'<pre>[^:]+: (.+)</pre>', data)
            if match:
                json_str = match.group(1)
                return json.loads(json_str)
            else:
                # Try direct JSON parse in case format changes
                return json.loads(data)
        except (json.JSONDecodeError, AttributeError) as e:
            logger.debug(f"Failed to parse event: {e}", extra={"data": data[:100]})
            return None
            
    async def _forward_event(self, device_id: str, event_data: Dict[str, Any]) -> None:
        """Forward parsed event to MCP event manager.
        
        Args:
            device_id: MCP device identifier
            event_data: Parsed event data
        """
        event_type = event_data.get("Event", "Unknown")
        
        # Transform to MCP event format
        mcp_event = {
            "device_id": device_id,
            "event_type": event_type,
            "timestamp": event_data.get("Timestamp"),
            "data": event_data
        }
        
        # Add to event manager
        await self.event_manager.add_event(device_id, mcp_event)
        
        logger.debug(
            f"Forwarded {event_type} event",
            extra={"device_id": device_id, "event_type": event_type}
        )