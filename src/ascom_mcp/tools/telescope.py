"""
Telescope control tools for ASCOM MCP.

Provides telescope control capabilities including goto, tracking, and parking.
"""

import logging
from typing import Any, Dict, Optional
from astropy.coordinates import SkyCoord
from astropy import units as u
import astropy.coordinates as coord

from .base import BaseDeviceTools
from ..devices.manager import DeviceManager
from ..utils.errors import (
    DeviceNotFoundError, 
    InvalidParameterError,
    OperationNotSupportedError,
    DeviceBusyError
)

logger = logging.getLogger(__name__)


class TelescopeTools(BaseDeviceTools):
    """Tools for controlling ASCOM telescopes."""
        
    async def connect(self, device_id: str) -> Dict[str, Any]:
        """Connect to a telescope."""
        try:
            logger.info(f"Connecting to telescope {device_id}")
            
            # Connect via device manager
            connected = await self.device_manager.connect_device(device_id)
            telescope = connected.client
            
            # Get telescope info
            info = {
                'device_id': device_id,
                'name': connected.info.name,
                'connected': telescope.Connected,
                'description': telescope.Description,
                'driver_info': telescope.DriverInfo,
                'can_slew': telescope.CanSlew,
                'can_park': telescope.CanPark,
                'can_find_home': telescope.CanFindHome,
                'can_track': telescope.CanSetTracking,
                'tracking': telescope.Tracking if hasattr(telescope, 'Tracking') else None
            }
            
            return {
                'success': True,
                'message': f"Connected to {connected.info.name}",
                'telescope': info
            }
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to connect to telescope {device_id}"
            }
            
    async def disconnect(self, device_id: str) -> Dict[str, Any]:
        """Disconnect from a telescope."""
        try:
            logger.info(f"Disconnecting from telescope {device_id}")
            
            # Get device to check if parking is needed
            connected = self.device_manager.get_connected_device(device_id)
            telescope = connected.client
            
            # Park if possible and not already parked
            if telescope.CanPark and not telescope.AtPark:
                logger.info("Parking telescope before disconnect")
                telescope.Park()
                
            # Disconnect
            await self.device_manager.disconnect_device(device_id)
            
            return {
                'success': True,
                'message': f"Disconnected from telescope {device_id}"
            }
            
        except Exception as e:
            logger.error(f"Failed to disconnect: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to disconnect from telescope {device_id}"
            }
            
    async def goto(self, device_id: str, ra: float, dec: float) -> Dict[str, Any]:
        """
        Slew telescope to RA/Dec coordinates.
        
        Args:
            device_id: Connected telescope ID
            ra: Right Ascension in hours (0-24)
            dec: Declination in degrees (-90 to +90)
        """
        try:
            # Validate coordinates
            if not 0 <= ra <= 24:
                raise InvalidParameterError("RA must be between 0 and 24 hours")
            if not -90 <= dec <= 90:
                raise InvalidParameterError("Dec must be between -90 and +90 degrees")
                
            # Get telescope
            connected = self.device_manager.get_connected_device(device_id)
            telescope = connected.client
            
            # Check capabilities
            if not telescope.CanSlew:
                raise OperationNotSupportedError("Telescope cannot slew")
                
            # Check if slewing
            if telescope.Slewing:
                raise DeviceBusyError("Telescope is already slewing")
                
            logger.info(f"Slewing telescope to RA={ra}h, Dec={dec}°")
            
            # Perform async slew
            telescope.SlewToCoordinatesAsync(ra, dec)
            
            # Get initial status
            status = {
                'slewing': telescope.Slewing,
                'target_ra': ra,
                'target_dec': dec,
                'current_ra': telescope.RightAscension,
                'current_dec': telescope.Declination
            }
            
            return {
                'success': True,
                'message': f"Slewing to RA={ra:.3f}h, Dec={dec:+.2f}°",
                'status': status
            }
            
        except Exception as e:
            logger.error(f"Goto failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Failed to slew telescope"
            }
            
    async def goto_object(self, device_id: str, object_name: str) -> Dict[str, Any]:
        """
        Slew telescope to a named object.
        
        Uses astropy to resolve object names to coordinates.
        """
        try:
            logger.info(f"Resolving object name: {object_name}")
            
            # Try to resolve object name
            try:
                # First try as a solar system object
                if object_name.lower() in ['moon', 'sun', 'mercury', 'venus', 'mars', 
                                          'jupiter', 'saturn', 'uranus', 'neptune']:
                    # For now, return a helpful message
                    # In production, would calculate ephemeris
                    return {
                        'success': False,
                        'message': f"Solar system object '{object_name}' requires ephemeris calculation (coming soon)"
                    }
                    
                # Try to resolve as deep sky object
                skycoord = SkyCoord.from_name(object_name)
                ra_hours = skycoord.ra.hour
                dec_deg = skycoord.dec.degree
                
                logger.info(f"Resolved {object_name} to RA={ra_hours:.3f}h, Dec={dec_deg:+.2f}°")
                
                # Use regular goto
                result = await self.goto(device_id, ra_hours, dec_deg)
                
                if result['success']:
                    result['message'] = f"Slewing to {object_name} (RA={ra_hours:.3f}h, Dec={dec_deg:+.2f}°)"
                    result['object_info'] = {
                        'name': object_name,
                        'ra_hours': ra_hours,
                        'dec_degrees': dec_deg,
                        'ra_hms': skycoord.ra.to_string(unit=u.hour, sep=':', precision=1),
                        'dec_dms': skycoord.dec.to_string(unit=u.degree, sep=':', precision=0)
                    }
                    
                return result
                
            except Exception as e:
                logger.error(f"Failed to resolve object name: {e}")
                return {
                    'success': False,
                    'error': 'Object not found',
                    'message': f"Could not resolve '{object_name}'. Try catalog designations like 'M31' or 'NGC 224'"
                }
                
        except Exception as e:
            logger.error(f"goto_object failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Failed to slew to object"
            }
            
    async def get_position(self, device_id: str) -> Dict[str, Any]:
        """Get current telescope position."""
        try:
            # Get telescope
            connected = self.device_manager.get_connected_device(device_id)
            telescope = connected.client
            
            # Get position
            ra = telescope.RightAscension
            dec = telescope.Declination
            
            # Convert to string representations
            skycoord = SkyCoord(ra=ra*u.hour, dec=dec*u.degree)
            
            position = {
                'ra_hours': ra,
                'dec_degrees': dec,
                'ra_hms': skycoord.ra.to_string(unit=u.hour, sep=':', precision=1),
                'dec_dms': skycoord.dec.to_string(unit=u.degree, sep=':', precision=0),
                'altitude': telescope.Altitude if hasattr(telescope, 'Altitude') else None,
                'azimuth': telescope.Azimuth if hasattr(telescope, 'Azimuth') else None,
                'sidereal_time': telescope.SiderealTime if hasattr(telescope, 'SiderealTime') else None
            }
            
            # Get status
            status = {
                'tracking': telescope.Tracking if hasattr(telescope, 'Tracking') else None,
                'slewing': telescope.Slewing,
                'at_park': telescope.AtPark if hasattr(telescope, 'AtPark') else None,
                'at_home': telescope.AtHome if hasattr(telescope, 'AtHome') else None
            }
            
            return {
                'success': True,
                'position': position,
                'status': status
            }
            
        except Exception as e:
            logger.error(f"Failed to get position: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Failed to get telescope position"
            }
            
    async def park(self, device_id: str) -> Dict[str, Any]:
        """Park the telescope."""
        try:
            # Get telescope
            connected = self.device_manager.get_connected_device(device_id)
            telescope = connected.client
            
            # Check if can park
            if not telescope.CanPark:
                raise OperationNotSupportedError("Telescope cannot park")
                
            # Check if already parked
            if telescope.AtPark:
                return {
                    'success': True,
                    'message': "Telescope is already parked"
                }
                
            logger.info("Parking telescope")
            
            # Park telescope
            telescope.Park()
            
            return {
                'success': True,
                'message': "Telescope parking initiated",
                'status': {
                    'at_park': telescope.AtPark,
                    'slewing': telescope.Slewing
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to park: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Failed to park telescope"
            }