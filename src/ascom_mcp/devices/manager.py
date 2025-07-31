"""
Device manager for ASCOM devices.

Handles device discovery, connection management, and state caching.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from aiohttp import ClientSession
from alpaca import discovery
from alpaca.camera import Camera
from alpaca.filterwheel import FilterWheel
from alpaca.focuser import Focuser
from alpaca.telescope import Telescope

from ..config import config
from ..utils.errors import ConnectionError, DeviceNotFoundError

logger = logging.getLogger(__name__)


class DeviceInfo:
    """Information about an ASCOM device."""

    def __init__(self, device_data: dict[str, Any]):
        device_type = device_data.get("DeviceType", "unknown")
        device_number = device_data.get("DeviceNumber", 0)
        self.id = f"{device_type.lower()}_{device_number}"
        self.name = device_data.get("DeviceName", "Unknown Device")
        self.type = device_data.get("DeviceType", "unknown")
        self.number = device_data.get("DeviceNumber", 0)
        self.unique_id = device_data.get("UniqueID", "")
        self.host = device_data.get("Host", "localhost")
        self.port = device_data.get("Port", 11111)
        self.api_version = device_data.get("ApiVersion", 1)
        self.discovered_at = datetime.now(timezone.utc)
        self._raw_data = device_data

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "number": self.number,
            "unique_id": self.unique_id,
            "host": self.host,
            "port": self.port,
            "api_version": self.api_version,
            "discovered_at": self.discovered_at.isoformat(),
            "connection_url": f"http://{self.host}:{self.port}/api/v{self.api_version}",
        }


class ConnectedDevice:
    """Represents a connected ASCOM device."""

    def __init__(self, device_info: DeviceInfo, client: Any):
        self.info = device_info
        self.client = client
        self.connected_at = datetime.now(timezone.utc)
        self.last_used = datetime.now(timezone.utc)

    def update_last_used(self):
        """Update last used timestamp."""
        self.last_used = datetime.now(timezone.utc)


class DeviceManager:
    """Manages ASCOM device connections and discovery."""

    def __init__(self):
        self._available_devices: dict[str, DeviceInfo] = {}
        self._connected_devices: dict[str, ConnectedDevice] = {}
        self._session: ClientSession | None = None
        self._discovery_lock = asyncio.Lock()
        self._connection_lock = asyncio.Lock()

    async def initialize(self):
        """Initialize the device manager."""
        self._session = ClientSession()
        logger.info("Device manager initialized")

    async def shutdown(self):
        """Shutdown device manager and disconnect all devices."""
        # Disconnect all devices
        device_ids = list(self._connected_devices.keys())
        for device_id in device_ids:
            try:
                await self.disconnect_device(device_id)
            except Exception as e:
                logger.error(f"Error disconnecting device {device_id}: {e}")

        # Close session
        if self._session:
            await self._session.close()

        logger.info("Device manager shutdown complete")

    async def discover_devices(self, timeout: float = 5.0) -> list[DeviceInfo]:
        """
        Discover ASCOM devices on the network.

        Uses alpyca discovery to find Alpaca devices.
        """
        async with self._discovery_lock:
            logger.info(f"Starting device discovery (timeout: {timeout}s)")

            try:
                # First try standard alpyca discovery - run in thread to avoid blocking
                devices = await asyncio.to_thread(
                    discovery.search_ipv4, timeout=timeout
                )

                # Clear old devices
                self._available_devices.clear()

                # Process discovered devices
                found_devices = []
                for device_data in devices:
                    device_info = DeviceInfo(device_data)
                    self._available_devices[device_info.id] = device_info
                    found_devices.append(device_info)
                    logger.info(
                        f"Discovered: {device_info.name} ({device_info.type}) "
                        f"at {device_info.host}:{device_info.port}"
                    )

                # Check known devices that don't implement UDP discovery
                await self._check_known_devices(found_devices)

                logger.info(f"Discovery complete: found {len(found_devices)} devices")
                if not found_devices:
                    logger.warning(
                        "No ASCOM devices found on network. "
                        "Ensure devices are powered on and connected."
                    )
                return found_devices

            except Exception as e:
                logger.error(f"Discovery failed: {e}")
                raise

    async def get_available_devices(self) -> list[dict[str, Any]]:
        """Get list of available devices."""
        return [device.to_dict() for device in self._available_devices.values()]

    async def get_connected_devices(self) -> list[dict[str, Any]]:
        """Get list of connected devices."""
        devices = []
        for _device_id, connected in self._connected_devices.items():
            device_dict = connected.info.to_dict()
            device_dict.update(
                {
                    "connected_at": connected.connected_at.isoformat(),
                    "last_used": connected.last_used.isoformat(),
                }
            )
            devices.append(device_dict)
        return devices

    async def connect_device(self, device_id: str) -> ConnectedDevice:
        """
        Connect to a device by ID.

        Creates appropriate client based on device type.
        """
        async with self._connection_lock:
            # Check if already connected
            if device_id in self._connected_devices:
                logger.info(f"Device {device_id} already connected")
                return self._connected_devices[device_id]

            # Find device info
            if device_id not in self._available_devices:
                raise DeviceNotFoundError(
                    f"Device {device_id} not found. Run discovery first."
                )

            device_info = self._available_devices[device_id]
            logger.info(
                f"Connecting to {device_info.name} "
                f"at {device_info.host}:{device_info.port}"
            )

            try:
                # Create appropriate client based on device type
                client = None
                base_url = f"{device_info.host}:{device_info.port}"

                if device_info.type.lower() == "telescope":
                    client = Telescope(base_url, device_info.number)
                elif device_info.type.lower() == "camera":
                    client = Camera(base_url, device_info.number)
                elif device_info.type.lower() == "focuser":
                    client = Focuser(base_url, device_info.number)
                elif device_info.type.lower() == "filterwheel":
                    client = FilterWheel(base_url, device_info.number)
                else:
                    raise ConnectionError(
                        f"Unsupported device type: {device_info.type}"
                    )

                # Test connection
                client.Connected = True
                if not client.Connected:
                    raise ConnectionError("Failed to connect to device")

                # Store connected device
                connected = ConnectedDevice(device_info, client)
                self._connected_devices[device_id] = connected

                logger.info(f"Successfully connected to {device_info.name}")
                return connected

            except Exception as e:
                logger.error(f"Failed to connect to {device_id}: {e}")
                raise ConnectionError(f"Connection failed: {str(e)}") from e

    async def disconnect_device(self, device_id: str):
        """Disconnect from a device."""
        async with self._connection_lock:
            if device_id not in self._connected_devices:
                logger.warning(f"Device {device_id} not connected")
                return

            connected = self._connected_devices[device_id]
            logger.info(f"Disconnecting from {connected.info.name}")

            try:
                # Disconnect client
                connected.client.Connected = False

                # Remove from connected devices
                del self._connected_devices[device_id]

                logger.info(f"Disconnected from {connected.info.name}")

            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
                # Remove anyway
                if device_id in self._connected_devices:
                    del self._connected_devices[device_id]

    def get_connected_device(self, device_id: str) -> ConnectedDevice:
        """
        Get a connected device by ID.

        Raises DeviceNotFoundError if not connected.
        """
        if device_id not in self._connected_devices:
            raise DeviceNotFoundError(f"Device {device_id} is not connected")

        device = self._connected_devices[device_id]
        device.update_last_used()
        return device

    async def _check_known_devices(self, found_devices: list[DeviceInfo]) -> None:
        """
        Check known devices that don't implement UDP discovery.

        Queries the management API of each known device to discover
        configured devices.
        """
        for host, port, name in config.known_devices:
            logger.info(f"Checking known device: {name} at {host}:{port}")

            try:
                # Query management API
                url = f"http://{host}:{port}/management/v1/configureddevices"
                async with self._session.get(url, timeout=2.0) as response:
                    if response.status == 200:
                        data = await response.json()
                        devices = data.get("Value", [])

                        for device_data in devices:
                            # Add host and port to device data
                            device_data["Host"] = host
                            device_data["Port"] = port

                            # Create DeviceInfo
                            device_info = DeviceInfo(device_data)

                            # Check if not already discovered
                            if device_info.id not in self._available_devices:
                                self._available_devices[device_info.id] = device_info
                                found_devices.append(device_info)
                                logger.info(
                                    f"Added known device: {device_info.name} "
                                    f"({device_info.type}) from {name}"
                                )
                    else:
                        logger.warning(
                            f"Known device {name} returned status {response.status}"
                        )

            except asyncio.TimeoutError:
                logger.warning(f"Known device {name} at {host}:{port} timed out")
            except Exception as e:
                logger.warning(f"Error checking known device {name}: {e}")

    async def get_device_info(self, device_id: str) -> dict[str, Any]:
        """Get detailed information about a device."""
        # Check if connected
        if device_id in self._connected_devices:
            connected = self._connected_devices[device_id]
            info = connected.info.to_dict()
            info["connected"] = True

            # Get additional info from device
            try:
                client = connected.client
                info["driver_info"] = client.DriverInfo
                info["driver_version"] = client.DriverVersion
                info["interface_version"] = client.InterfaceVersion
                info["description"] = client.Description

                # Type-specific info
                if connected.info.type.lower() == "telescope":
                    info["can_slew"] = client.CanSlew
                    info["can_park"] = client.CanPark
                    info["can_find_home"] = client.CanFindHome
                elif connected.info.type.lower() == "camera":
                    info["sensor_type"] = client.SensorType
                    info["pixel_size"] = client.PixelSizeX
                    info["max_bin"] = client.MaxBinX

            except Exception as e:
                logger.warning(f"Could not get extended info: {e}")

            return info

        # Check if available
        elif device_id in self._available_devices:
            info = self._available_devices[device_id].to_dict()
            info["connected"] = False
            return info

        else:
            raise DeviceNotFoundError(f"Device {device_id} not found")
