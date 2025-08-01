"""Event handler for Seestar telescope event streams."""

import asyncio
import logging
from collections import defaultdict
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)


class SeestarEventHandler:
    """Handles asynchronous events from Seestar telescopes.
    
    Seestar sends unsolicited events like:
    - BalanceSensor: Accelerometer data
    - PiStatus: Temperature and system status
    - FocuserMove: Focus position changes
    - mount_guide_star_lost: Guiding events
    """
    
    def __init__(self):
        self.event_queue = asyncio.Queue()
        self.subscribers = defaultdict(list)
        self._processing = False
        self._task = None
        
    def subscribe(self, event_type: str, callback: Callable[[dict], Coroutine[Any, Any, None]]):
        """Subscribe to events of a specific type.
        
        Args:
            event_type: The event method name (e.g., "BalanceSensor")
            callback: Async function to call with event data
        """
        self.subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to {event_type} events")
        
    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from events."""
        if callback in self.subscribers[event_type]:
            self.subscribers[event_type].remove(callback)
            
    async def handle_event(self, event: dict):
        """Handle an incoming event from Seestar.
        
        Args:
            event: Event dictionary with 'method' and 'params'
        """
        await self.event_queue.put(event)
        
    async def start_processing(self):
        """Start processing events from the queue."""
        if self._processing:
            return
            
        self._processing = True
        self._task = asyncio.create_task(self._process_events())
        logger.info("Started event processing")
        
    async def stop_processing(self):
        """Stop processing events."""
        self._processing = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped event processing")
        
    async def _process_events(self):
        """Process events from the queue."""
        while self._processing:
            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(
                    self.event_queue.get(), 
                    timeout=1.0
                )
                
                event_type = event.get("method", "unknown")
                logger.debug(f"Processing {event_type} event")
                
                # Notify all subscribers for this event type
                callbacks = self.subscribers.get(event_type, [])
                for callback in callbacks:
                    try:
                        await callback(event)
                    except Exception as e:
                        logger.error(
                            f"Error in {event_type} callback: {e}",
                            exc_info=True
                        )
                        
            except asyncio.TimeoutError:
                # No events, continue
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)
                
    def get_subscriber_count(self, event_type: str = None) -> int:
        """Get number of subscribers for an event type."""
        if event_type:
            return len(self.subscribers.get(event_type, []))
        return sum(len(subs) for subs in self.subscribers.values())