"""
Device manager for ASCOM devices.

Handles device discovery, connection management, and state caching.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from alpyca import discovery, Telescope, Camera, Focuser, FilterWheel
from aiohttp import ClientSession

from ..utils.errors import DeviceNotFoundError, ConnectionError

logger = logging.getLogger(__name__)


class DeviceInfo:
    """Information about an ASCOM device."""
    
    def __init__(self, device_data: Dict[str, Any]):
        self.id = f"{device_data.get('DeviceType', 'unknown')}_{device_data.get('DeviceNumber', 0)}"
        self.name = device_data.get('DeviceName', 'Unknown Device')
        self.type = device_data.get('DeviceType', 'unknown')
        self.number = device_data.get('DeviceNumber', 0)
        self.unique_id = device_data.get('UniqueID', '')
        self.host = device_data.get('Host', 'localhost')
        self.port = device_data.get('Port', 11111)
        self.api_version = device_data.get('ApiVersion', 1)
        self.discovered_at = datetime.utcnow()
        self._raw_data = device_data
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'number': self.number,
            'unique_id': self.unique_id,
            'host': self.host,
            'port': self.port,
            'api_version': self.api_version,
            'discovered_at': self.discovered_at.isoformat(),
            'connection_url': f"http://{self.host}:{self.port}/api/v{self.api_version}"
        }


class ConnectedDevice:
    """Represents a connected ASCOM device."""
    
    def __init__(self, device_info: DeviceInfo, client: Any):
        self.info = device_info
        self.client = client
        self.connected_at = datetime.utcnow()
        self.last_used = datetime.utcnow()
        
    def update_last_used(self):
        """Update last used timestamp."""
        self.last_used = datetime.utcnow()


class DeviceManager:
    """Manages ASCOM device connections and discovery."""
    
    def __init__(self):
        self._available_devices: Dict[str, DeviceInfo] = {}
        self._connected_devices: Dict[str, ConnectedDevice] = {}
        self._session: Optional[ClientSession] = None
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
        
    async def discover_devices(self, timeout: float = 5.0) -> List[DeviceInfo]:
        """
        Discover ASCOM devices on the network.
        
        Uses alpyca discovery to find Alpaca devices.
        """
        async with self._discovery_lock:
            logger.info(f"Starting device discovery (timeout: {timeout}s)")
            
            try:
                # Use alpyca discovery
                devices = discovery.search_ipv4(timeout=timeout)
                
                # Clear old devices
                self._available_devices.clear()
                
                # Process discovered devices
                found_devices = []
                for device_data in devices:
                    device_info = DeviceInfo(device_data)
                    self._available_devices[device_info.id] = device_info
                    found_devices.append(device_info)
                    logger.info(f"Discovered: {device_info.name} ({device_info.type}) at {device_info.host}:{device_info.port}")
                    
                logger.info(f"Discovery complete: found {len(found_devices)} devices")
                if not found_devices:
                    logger.warning("No ASCOM devices found on network. Ensure devices are powered on and connected.")
                return found_devices
                
            except Exception as e:
                logger.error(f"Discovery failed: {e}")
                raise
                
    async def get_available_devices(self) -> List[Dict[str, Any]]:
        """Get list of available devices."""
        return [device.to_dict() for device in self._available_devices.values()]
        
    async def get_connected_devices(self) -> List[Dict[str, Any]]:
        """Get list of connected devices."""
        devices = []
        for device_id, connected in self._connected_devices.items():
            device_dict = connected.info.to_dict()
            device_dict.update({
                'connected_at': connected.connected_at.isoformat(),
                'last_used': connected.last_used.isoformat()
            })
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
                raise DeviceNotFoundError(f"Device {device_id} not found. Run discovery first.")
                
            device_info = self._available_devices[device_id]
            logger.info(f"Connecting to {device_info.name} at {device_info.host}:{device_info.port}")
            
            try:
                # Create appropriate client based on device type
                client = None
                base_url = f"{device_info.host}:{device_info.port}"
                
                if device_info.type.lower() == 'telescope':
                    client = Telescope(base_url, device_info.number)
                elif device_info.type.lower() == 'camera':
                    client = Camera(base_url, device_info.number)
                elif device_info.type.lower() == 'focuser':
                    client = Focuser(base_url, device_info.number)
                elif device_info.type.lower() == 'filterwheel':
                    client = FilterWheel(base_url, device_info.number)
                else:
                    raise ConnectionError(f"Unsupported device type: {device_info.type}")
                    
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
                raise ConnectionError(f"Connection failed: {str(e)}")
                
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
        
    async def get_device_info(self, device_id: str) -> Dict[str, Any]:
        """Get detailed information about a device."""
        # Check if connected
        if device_id in self._connected_devices:
            connected = self._connected_devices[device_id]
            info = connected.info.to_dict()
            info['connected'] = True
            
            # Get additional info from device
            try:
                client = connected.client
                info['driver_info'] = client.DriverInfo
                info['driver_version'] = client.DriverVersion
                info['interface_version'] = client.InterfaceVersion
                info['description'] = client.Description
                
                # Type-specific info
                if connected.info.type.lower() == 'telescope':
                    info['can_slew'] = client.CanSlew
                    info['can_park'] = client.CanPark
                    info['can_find_home'] = client.CanFindHome
                elif connected.info.type.lower() == 'camera':
                    info['sensor_type'] = client.SensorType
                    info['pixel_size'] = client.PixelSizeX
                    info['max_bin'] = client.MaxBinX
                    
            except Exception as e:
                logger.warning(f"Could not get extended info: {e}")
                
            return info
            
        # Check if available
        elif device_id in self._available_devices:
            info = self._available_devices[device_id].to_dict()
            info['connected'] = False
            return info
            
        else:
            raise DeviceNotFoundError(f"Device {device_id} not found")