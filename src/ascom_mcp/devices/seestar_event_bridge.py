"""
Bridge between Seestar eventbus and MCP event system.

This module handles the integration between Seestar's SSE-based
event streaming and the MCP event stream manager.
"""

import asyncio
import json
from typing import Any

from ascom_mcp.ascom_logging import StructuredLogger
from .seestar_sse_consumer import SeestarSSEConsumer

logger = StructuredLogger("ascom.seestar.events")


class SeestarEventBridge:
    """Bridges Seestar events to MCP event system."""
    
    # Class-level storage for SSE tasks to persist across HTTP requests
    _sse_tasks = {}
    _sse_consumers = {}
    
    def __init__(self, event_manager):
        """Initialize the event bridge.
        
        Args:
            event_manager: The EventStreamManager instance
        """
        self.event_manager = event_manager
        self._sse_consumer = SeestarSSEConsumer(event_manager)
        self._active_subscriptions = {}
        self._event_loop = None
        
    async def connect_to_seestar(self, device_id: str, device_info: Any) -> None:
        """Connect to a Seestar device's event system.
        
        This is called when a Seestar telescope is connected.
        
        Args:
            device_id: The device identifier
            device_info: Device information
        """
        logger.debug(f"connect_to_seestar called for {device_id}: {device_info.name} at {device_info.host}:{device_info.port}")
        try:
            # For Seestar devices at port 5555, start SSE consumer
            if device_info.port == 5555 and "seestar" in device_info.name.lower():
                logger.info(f"Setting up Seestar SSE event consumer for {device_id}")
                
                # Check if SSE consumer already exists for this device
                if device_id in self.__class__._sse_tasks:
                    logger.info(f"SSE consumer already exists for {device_id}, checking if it's running")
                    task = self.__class__._sse_tasks[device_id]
                    if not task.done():
                        logger.info(f"SSE consumer is still running for {device_id}")
                        return
                    else:
                        logger.info(f"SSE consumer task is done for {device_id}, will restart")
                
                # Extract device number from device_id or default to 1
                device_num = 1
                if device_id.startswith("telescope_"):
                    try:
                        device_num = int(device_id.split("_")[1])
                    except (IndexError, ValueError):
                        pass
                
                # Create SSE consumer if not exists
                if device_id not in self.__class__._sse_consumers:
                    logger.info(f"Creating new SSE consumer for {device_id}")
                    self.__class__._sse_consumers[device_id] = SeestarSSEConsumer(self.event_manager)
                
                # Get the consumer
                sse_consumer = self.__class__._sse_consumers[device_id]
                
                # Start SSE consumer as a background task
                logger.info(f"Starting SSE consumer task for {device_id}")
                # Call _consume_events directly to avoid double task wrapping
                task = asyncio.create_task(sse_consumer._consume_events(device_id, device_num))
                self.__class__._sse_tasks[device_id] = task
                logger.info(f"SSE task created: {task}, done={task.done()}")
                
                # Add callback to track when task completes
                def task_done_callback(t):
                    logger.info(f"SSE task for {device_id} completed. Done={t.done()}")
                    try:
                        result = t.result()
                        logger.info(f"Task result: {result}")
                    except Exception as e:
                        logger.error(f"Task exception: {e}", exc_info=True)
                
                task.add_done_callback(task_done_callback)
                
                # Store metadata for this device
                await self.event_manager.set_device_metadata(
                    device_id,
                    {
                        "name": device_info.name,
                        "type": "Seestar",
                        "unique_id": device_info.unique_id,
                        "supports_events": True,
                        "event_source": "SSE",
                    }
                )
                
                logger.info(f"Seestar SSE consumer started for {device_id} (task: {task})")
            else:
                logger.debug(f"Not a Seestar device or wrong port: port={device_info.port}, name={device_info.name}")
                
        except Exception as e:
            logger.error(f"Failed to set up Seestar SSE consumer: {e}", exc_info=True)
            
    async def handle_seestar_event(self, device_id: str, event_data: dict) -> None:
        """Handle an event from Seestar.
        
        This is called by the telescope tools when they receive events.
        
        Args:
            device_id: Device identifier
            event_data: Raw event data from Seestar
        """
        try:
            # Add the event to the stream
            await self.event_manager.add_event(device_id, event_data)
            
            # Log specific event types we care about
            event_type = event_data.get("Event", "Unknown")
            
            if event_type == "PiStatus":
                # System status update
                if "battery_capacity" in event_data:
                    logger.info(
                        f"Seestar battery: {event_data['battery_capacity']}%",
                        device_id=device_id
                    )
                    
            elif event_type == "GotoComplete":
                # Movement completed
                logger.info(
                    f"Seestar goto completed",
                    device_id=device_id,
                    ra=event_data.get("ra"),
                    dec=event_data.get("dec")
                )
                
            elif event_type == "ViewChanged":
                # View state changed
                logger.info(
                    f"Seestar view changed",
                    device_id=device_id,
                    state=event_data.get("state")
                )
                
        except Exception as e:
            logger.error(f"Failed to handle Seestar event: {e}", device_id=device_id)
            
    async def disconnect_from_seestar(self, device_id: str) -> None:
        """Disconnect from a Seestar device's event system.
        
        This is called when a Seestar telescope is disconnected.
        
        Args:
            device_id: The device identifier
        """
        try:
            # Stop SSE consumer task if it exists
            if device_id in self.__class__._sse_tasks:
                task = self.__class__._sse_tasks[device_id]
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                del self.__class__._sse_tasks[device_id]
                logger.info(f"Seestar SSE consumer task stopped for {device_id}")
            
            # Stop SSE consumer
            if device_id in self.__class__._sse_consumers:
                sse_consumer = self.__class__._sse_consumers[device_id]
                await sse_consumer.stop_consuming(device_id)
                logger.info(f"Seestar SSE consumer stopped for {device_id}")
        except Exception as e:
            logger.error(f"Failed to stop Seestar SSE consumer: {e}")
            
    def setup_event_loop(self):
        """Set up the event loop for async operations."""
        try:
            self._event_loop = asyncio.get_running_loop()
        except RuntimeError:
            # No event loop running, we'll handle events synchronously
            self._event_loop = None
            
    def handle_sync_event(self, device_id: str, event_data: dict):
        """Handle events from synchronous context (blinker callbacks).
        
        This bridges sync blinker events to async MCP event system.
        """
        if self._event_loop:
            # Schedule the async handler
            asyncio.run_coroutine_threadsafe(
                self.handle_seestar_event(device_id, event_data),
                self._event_loop
            )
        else:
            # No event loop, log warning
            logger.warning(
                "No event loop available for Seestar event",
                device_id=device_id,
                event_type=event_data.get("Event")
            )