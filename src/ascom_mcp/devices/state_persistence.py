"""Device state persistence for ASCOM MCP server."""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .manager import DeviceInfo

# Import moved to avoid circular dependency

logger = logging.getLogger(__name__)


class DeviceStatePersistence:
    """Manages persistent storage of device information."""
    
    def __init__(self, state_file: str = None):
        """Initialize state persistence.
        
        Args:
            state_file: Path to state file. Defaults to ~/.ascom_mcp/devices.json
        """
        if state_file is None:
            state_dir = Path.home() / ".ascom_mcp"
            state_dir.mkdir(exist_ok=True)
            self.state_file = state_dir / "devices.json"
        else:
            self.state_file = Path(state_file)
            
        logger.info(f"Using state file: {self.state_file}")
        
    def load_devices(self) -> List["DeviceInfo"]:
        """Load device information from persistent storage.
        
        Returns:
            List of DeviceInfo objects
        """
        if not self.state_file.exists():
            logger.debug("No state file found")
            return []
            
        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)
                
            # Import here to avoid circular dependency
            from .manager import DeviceInfo
            
            devices = []
            for device_data in data.get("devices", []):
                try:
                    devices.append(DeviceInfo(device_data))
                except Exception as e:
                    logger.warning(f"Failed to load device: {e}")
                    
            logger.info(f"Loaded {len(devices)} devices from state")
            return devices
            
        except Exception as e:
            logger.error(f"Failed to load state file: {e}")
            return []
            
    def save_devices(self, devices: List["DeviceInfo"]):
        """Save device information to persistent storage.
        
        Args:
            devices: List of DeviceInfo objects to save
        """
        try:
            data = {
                "version": "1.0",
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "devices": [device.to_dict() for device in devices]
            }
            
            # Write to temp file first
            temp_file = self.state_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            # Atomic rename
            temp_file.replace(self.state_file)
            
            logger.info(f"Saved {len(devices)} devices to state")
            
        except Exception as e:
            logger.error(f"Failed to save state file: {e}")
            
    def merge_devices(self, existing: List["DeviceInfo"], new: List["DeviceInfo"]) -> List["DeviceInfo"]:
        """Merge new devices with existing ones.
        
        Args:
            existing: Current device list
            new: New devices to merge
            
        Returns:
            Merged device list
        """
        # Import here to avoid circular dependency
        from .manager import DeviceInfo
        
        # Create map of existing devices by ID
        device_map = {device.id: device for device in existing}
        
        # Merge new devices
        for device in new:
            if device.id in device_map:
                # Update existing device info
                existing_device = device_map[device.id]
                # Keep discovered_at from existing, update other fields
                device_data = device.to_dict()
                device_data["discovered_at"] = existing_device.to_dict().get("discovered_at")
                device_map[device.id] = DeviceInfo(device_data)
            else:
                # Add new device
                device_map[device.id] = device
                
        return list(device_map.values())
        
    def cleanup_stale_devices(self, devices: List["DeviceInfo"], max_age_days: int = 30) -> List["DeviceInfo"]:
        """Remove devices that haven't been seen recently.
        
        Args:
            devices: Device list to clean
            max_age_days: Maximum age in days before removal
            
        Returns:
            Cleaned device list
        """
        cleaned = []
        now = datetime.now(timezone.utc)
        
        for device in devices:
            try:
                # Parse discovered_at timestamp
                discovered_str = device.to_dict().get("discovered_at", "")
                if discovered_str:
                    discovered = datetime.fromisoformat(discovered_str.replace("Z", "+00:00"))
                    age_days = (now - discovered).days
                    
                    if age_days <= max_age_days:
                        cleaned.append(device)
                    else:
                        logger.info(f"Removing stale device {device.id} (age: {age_days} days)")
                else:
                    # No timestamp, keep it
                    cleaned.append(device)
                    
            except Exception as e:
                logger.warning(f"Error checking device age: {e}")
                cleaned.append(device)  # Keep on error
                
        return cleaned