"""
Imaging and frame capture service.

Provides image capture, stacking, and visual feedback capabilities.
"""

import base64
from datetime import datetime

from ..models.commands import StackingParams
from ..models.responses import FrameCapture, StackingInfo


class ImagingService:
    """Image capture and processing."""

    def __init__(self, client):
        self.client = client

    async def capture_frame(self) -> bytes:
        """
        Capture current frame from telescope.
        
        Returns:
            JPEG image bytes
        """
        # Get current image
        response = await self.client.execute_action("get_current_img")

        if response.success and response.model_dump().get("image_data"):
            # Image data might be base64 encoded
            img_data = response.model_dump()["image_data"]
            if isinstance(img_data, str):
                return base64.b64decode(img_data)
            return img_data

        # Fallback: Try to grab from MJPEG stream
        return await self._capture_from_stream()

    async def _capture_from_stream(self) -> bytes:
        """Capture frame from MJPEG stream."""
        stream_url = f"http://{self.client.host}:5432/img/live_stacking"

        async with self.client.session.get(stream_url) as response:
            # Read until we get a complete JPEG frame
            buffer = b""
            jpeg_start = b"\xff\xd8"
            jpeg_end = b"\xff\xd9"

            async for chunk in response.content.iter_chunked(8192):
                buffer += chunk

                # Look for complete JPEG
                start_idx = buffer.find(jpeg_start)
                if start_idx >= 0:
                    end_idx = buffer.find(jpeg_end, start_idx)
                    if end_idx >= 0:
                        # Extract complete JPEG
                        jpeg_data = buffer[start_idx:end_idx + 2]
                        return jpeg_data

                # Prevent buffer overflow
                if len(buffer) > 1024 * 1024:  # 1MB max
                    buffer = buffer[-8192:]  # Keep last chunk

        raise RuntimeError("Failed to capture frame from stream")

    async def capture_frame_with_metadata(self) -> FrameCapture:
        """
        Capture frame with full metadata.
        
        Returns:
            FrameCapture object with image and metadata
        """
        # Get image data
        image_data = await self.capture_frame()

        # Get current settings
        view_status = await self.client.viewing.get_status()
        device_state = await self.client.status.get_device_state()

        return FrameCapture(
            timestamp=datetime.now(),
            image_data=image_data,
            exposure_ms=view_status.exposure_time_ms,
            gain=view_status.gain,
            temperature=device_state.temperature_celsius
        )

    async def save_image(self, filename: str | None = None) -> str:
        """
        Save current image to telescope storage.
        
        Args:
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Saved filename
        """
        params = {}
        if filename:
            params["filename"] = filename

        response = await self.client.execute_action("save_image", params)

        if response.success:
            return response.model_dump().get("filename", "saved_image.jpg")
        raise RuntimeError(f"Failed to save image: {response.error_message}")

    async def start_stacking(
        self,
        target_name: str,
        mode: str = "star"
    ) -> StackingInfo:
        """
        Start image stacking session.
        
        Args:
            target_name: Name for this session
            mode: Stacking mode
            
        Returns:
            Stacking status
        """
        params = StackingParams(mode=mode, target_name=target_name)
        response = await self.client.execute_action(
            "iscope_start_stack",
            params.model_dump()
        )

        if response.success:
            return await self.get_stacking_info()

        return StackingInfo(
            active=False,
            mode=mode,
            target_name=target_name
        )

    async def get_stacking_info(self) -> StackingInfo:
        """Get current stacking status."""
        response = await self.client.execute_action("get_stack_info")

        if response.success:
            data = response.model_dump()
            return StackingInfo(
                active=data.get("stacking", False),
                mode=data.get("mode"),
                target_name=data.get("target_name"),
                stack_count=data.get("stack_count", 0),
                total_exposure_s=data.get("total_exposure", 0),
                rejection_count=data.get("rejected_count", 0)
            )

        return StackingInfo(active=False)

    async def capture_preview_grid(
        self,
        directions: list[str] = ["north", "east", "south", "west"]
    ) -> dict[str, FrameCapture]:
        """
        Capture preview images in multiple directions.
        
        Useful for getting a panoramic sense of surroundings.
        
        Args:
            directions: List of directions to capture
            
        Returns:
            Dictionary mapping direction to captured frame
        """
        previews = {}

        # Save starting position
        start_pos = await self.client.telescope.get_position()

        for direction in directions:
            # Quick look in direction
            frame = await self.client.telescope.quick_look(
                direction,
                duration=2.0,
                return_to_start=False
            )
            previews[direction] = frame

        # Return to start
        await self.client.telescope.goto(start_pos.ra, start_pos.dec)

        return previews
