"""Device ID resolution for flexible connection patterns."""

import re
import logging
from typing import Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .manager import DeviceInfo

logger = logging.getLogger(__name__)


class DeviceResolver:
    """Resolves device IDs to connection information."""
    
    # Pattern for direct connection strings: name@host:port or host:port
    DIRECT_PATTERN = re.compile(r'^(?:([^@]+)@)?([^:]+):(\d+)$')
    
    @classmethod
    def parse_connection_string(cls, device_id: str) -> Optional[Tuple[str, str, int]]:
        """Parse a connection string like 'seestar@192.168.1.100:5555'.
        
        Args:
            device_id: Connection string to parse
            
        Returns:
            Tuple of (name, host, port) or None if not a valid format
        """
        match = cls.DIRECT_PATTERN.match(device_id)
        if match:
            name = match.group(1) or "Direct Connection"
            host = match.group(2)
            port = int(match.group(3))
            return (name, host, port)
        return None
        
    @classmethod
    def create_device_info_from_connection(
        cls, 
        device_id: str,
        name: str,
        host: str, 
        port: int,
        device_type: str = "Telescope",
        device_number: int = 1
    ) -> "DeviceInfo":
        """Create DeviceInfo from connection parameters.
        
        Args:
            device_id: Device identifier
            name: Device name
            host: Host address
            port: Port number
            device_type: ASCOM device type
            device_number: Device number
            
        Returns:
            DeviceInfo object
        """
        # Import here to avoid circular dependency
        from .manager import DeviceInfo
        
        # Try to extract type from device_id if it contains underscore
        if "_" in device_id:
            type_part, num_part = device_id.rsplit("_", 1)
            device_type = type_part.title()
            try:
                device_number = int(num_part)
            except ValueError:
                pass
                
        device_data = {
            "DeviceType": device_type,
            "DeviceNumber": device_number,
            "DeviceName": name,
            "Host": host,
            "Port": port,
            "UniqueID": f"{device_id}_{host}_{port}",
            "ApiVersion": 1
        }
        
        return DeviceInfo(device_data)
        
    @classmethod
    def parse_device_id_type(cls, device_id: str) -> Tuple[str, int]:
        """Extract device type and number from device_id.
        
        Args:
            device_id: Device identifier like 'telescope_1'
            
        Returns:
            Tuple of (device_type, device_number)
        """
        device_type = "Telescope"  # Default
        device_number = 1
        
        if "_" in device_id:
            parts = device_id.rsplit("_", 1)
            if len(parts) == 2:
                type_part, num_part = parts
                device_type = type_part.title()
                try:
                    device_number = int(num_part)
                except ValueError:
                    pass
                    
        return device_type, device_number