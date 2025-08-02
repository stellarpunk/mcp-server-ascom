"""
Main Seestar SDK client.

Provides type-safe access to all telescope operations with visual feedback support.
"""

import json
from contextlib import asynccontextmanager
from typing import Any

import aiohttp

from ..ascom_logging import StructuredLogger
from .models.responses import SeestarResponse
from .services.focus import FocusService
from .services.imaging import ImagingService
from .services.status import StatusService
from .services.telescope import TelescopeService
from .services.viewing import ViewingService
from .streaming import StreamingService

logger = StructuredLogger("seestar.sdk.client")


class SeestarClient:
    """
    Type-safe client for Seestar S50 telescope.
    
    Example:
        async with SeestarClient("seestar.local") as client:
            # Initialize telescope (REQUIRED!)
            await client.initialize(latitude=40.7, longitude=-74.0)
            
            # Get visual feedback
            status = await client.telescope.where_am_i()
            print(f"Looking at: RA={status.ra}, Dec={status.dec}")
            
            # Start scenery mode
            await client.viewing.start(mode="scenery")
            frame = await client.imaging.capture_frame()
    """

    def __init__(
        self,
        host: str,
        port: int = 5555,
        device_num: int = 1,
        client_id: int = 1,
        timeout: float = 30.0
    ):
        """
        Initialize Seestar client.
        
        Args:
            host: Telescope hostname or IP
            port: ASCOM API port (default: 5555)
            device_num: Device number (default: 1)
            client_id: ASCOM client ID
            timeout: Request timeout in seconds
        """
        self.host = host
        self.port = port
        self.device_num = device_num
        self.client_id = client_id
        self.timeout = timeout

        # API endpoints
        self.base_url = f"http://{host}:{port}"
        self.api_url = f"{self.base_url}/api/v1/telescope/{device_num}"

        # Will be initialized in __aenter__
        self.session: aiohttp.ClientSession | None = None

        # Services
        self.telescope = TelescopeService(self)
        self.viewing = ViewingService(self)
        self.imaging = ImagingService(self)
        self.focus = FocusService(self)
        self.status = StatusService(self)
        self.streaming = StreamingService(self)

        # State
        self._initialized = False
        self._connected = False

    @asynccontextmanager
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
        if self.session:
            await self.session.close()

    async def connect(self) -> bool:
        """Connect to telescope."""
        try:
            # Set connected state via ASCOM
            response = await self._put_action(
                "Connected",
                {"Connected": True}
            )

            if response.get("Value"):
                self._connected = True
                logger.info(f"Connected to Seestar at {self.host}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from telescope."""
        if self._connected:
            try:
                await self._put_action("Connected", {"Connected": False})
                self._connected = False
                logger.info("Disconnected from Seestar")
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")

    async def initialize(
        self,
        latitude: float,
        longitude: float,
        move_arm: bool = True,
        timezone: str = "UTC"
    ) -> bool:
        """
        Initialize telescope (REQUIRED before most operations).
        
        Args:
            latitude: Observer latitude (-90 to 90)
            longitude: Observer longitude (-180 to 180)
            move_arm: Whether to move telescope arm
            timezone: Time zone string
            
        Returns:
            True if initialization succeeded
        """
        if self._initialized:
            logger.info("Already initialized")
            return True

        try:
            # Run startup sequence
            response = await self.execute_action(
                "action_start_up_sequence",
                {
                    "lat": latitude,
                    "lon": longitude,
                    "move_arm": move_arm,
                    "time_zone": timezone
                }
            )

            if response.success:
                self._initialized = True
                logger.info("Telescope initialized successfully")
                return True
            else:
                logger.error(f"Initialization failed: {response.error_message}")
                return False

        except Exception as e:
            logger.error(f"Initialization error: {e}")
            return False

    async def execute_action(
        self,
        action: str,
        parameters: dict[str, Any] | None = None
    ) -> SeestarResponse:
        """
        Execute a telescope action.
        
        Args:
            action: Action name (e.g., "method_sync")
            parameters: Action parameters
            
        Returns:
            Parsed response
        """
        if not self._connected:
            raise RuntimeError("Not connected to telescope")

        # Handle method_sync wrapper
        if action == "method_sync" and parameters:
            # Already in correct format
            params_str = json.dumps(parameters)
        elif action.startswith("action_"):
            # Direct action with parameters
            params_str = json.dumps(parameters) if parameters else "{}"
        else:
            # Wrap in method_sync
            wrapped = {
                "method": action,
                "params": parameters
            }
            params_str = json.dumps(wrapped)
            action = "method_sync"

        response = await self._put_action(
            "Action",
            {
                "Action": action,
                "Parameters": params_str
            }
        )

        # Parse response
        value = response.get("Value", {})
        return SeestarResponse(**value)

    async def _put_action(
        self,
        endpoint: str,
        data: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute PUT request to telescope."""
        if not self.session:
            raise RuntimeError("Client not initialized. Use 'async with' context.")

        url = f"{self.api_url}/{endpoint.lower()}"

        # Add ClientID
        data["ClientID"] = self.client_id
        data["ClientTransactionID"] = self._get_transaction_id()

        # Convert to form data
        form_data = aiohttp.FormData()
        for key, value in data.items():
            form_data.add_field(key, str(value))

        async with self.session.put(url, data=form_data) as response:
            response.raise_for_status()
            return await response.json()

    async def _get(self, endpoint: str) -> dict[str, Any]:
        """Execute GET request to telescope."""
        if not self.session:
            raise RuntimeError("Client not initialized")

        url = f"{self.api_url}/{endpoint.lower()}"
        params = {
            "ClientID": self.client_id,
            "ClientTransactionID": self._get_transaction_id()
        }

        async with self.session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()

    def _get_transaction_id(self) -> int:
        """Generate unique transaction ID."""
        # Simple incrementing ID (in production, use better method)
        if not hasattr(self, "_transaction_counter"):
            self._transaction_counter = 1000
        self._transaction_counter += 1
        return self._transaction_counter

    @property
    def is_ready(self) -> bool:
        """Check if telescope is ready for operations."""
        return self._connected and self._initialized
