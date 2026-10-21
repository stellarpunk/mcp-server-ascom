"""
Streaming service for live video feeds.

Provides access to MJPEG streams and frame capture.
"""

import asyncio
from collections.abc import AsyncIterator

from .models.responses import StreamingStatus


class StreamingService:
    """Video streaming control."""

    def __init__(self, client):
        self.client = client
        self._streaming = False

    def get_mjpeg_url(self) -> str:
        """
        Get MJPEG stream URL.
        
        Returns:
            URL for live MJPEG stream
        """
        return f"http://{self.client.host}:5432/img/live_stacking"

    def get_frame_status_url(self) -> str:
        """
        Get SSE frame status URL.
        
        Returns:
            URL for frame counter updates
        """
        return f"http://{self.client.host}:7556/{self.client.device_num}/vid/status"

    async def start_streaming(self) -> StreamingStatus:
        """Start video streaming."""
        response = await self.client.execute_action("begin_streaming")

        if response.success:
            self._streaming = True
            return StreamingStatus(
                streaming=True,
                mjpeg_url=self.get_mjpeg_url(),
                frame_count=0
            )

        return StreamingStatus(streaming=False)

    async def stop_streaming(self) -> bool:
        """Stop video streaming."""
        response = await self.client.execute_action("stop_streaming")
        if response.success:
            self._streaming = False
        return response.success

    async def get_status(self) -> StreamingStatus:
        """Get streaming status."""
        # Would check actual streaming state
        return StreamingStatus(
            streaming=self._streaming,
            mjpeg_url=self.get_mjpeg_url() if self._streaming else None,
            frame_count=0  # Would get from SSE
        )

    async def stream_frames(self) -> AsyncIterator[bytes]:
        """
        Stream frames from MJPEG feed.
        
        Yields:
            JPEG frame bytes
        """
        url = self.get_mjpeg_url()

        async with self.client.session.get(url) as response:
            buffer = b""
            jpeg_start = b"\xff\xd8"
            jpeg_end = b"\xff\xd9"

            async for chunk in response.content.iter_chunked(8192):
                buffer += chunk

                # Look for complete JPEGs
                while True:
                    start_idx = buffer.find(jpeg_start)
                    if start_idx < 0:
                        break

                    end_idx = buffer.find(jpeg_end, start_idx)
                    if end_idx < 0:
                        break

                    # Extract and yield complete JPEG
                    jpeg_data = buffer[start_idx:end_idx + 2]
                    yield jpeg_data

                    # Remove processed data
                    buffer = buffer[end_idx + 2:]

                # Prevent buffer overflow
                if len(buffer) > 1024 * 1024:
                    buffer = buffer[-8192:]

    async def capture_video_segment(
        self,
        duration_seconds: float,
        output_file: str
    ) -> int:
        """
        Capture video segment to file.
        
        Args:
            duration_seconds: How long to record
            output_file: Output filename (.avi)
            
        Returns:
            Number of frames captured
        """
        # Start recording
        response = await self.client.execute_action(
            "start_record_avi",
            {"filename": output_file}
        )

        if not response.success:
            raise RuntimeError(f"Failed to start recording: {response.error_message}")

        # Wait for duration
        await asyncio.sleep(duration_seconds)

        # Stop recording
        stop_response = await self.client.execute_action("stop_record_avi")

        if stop_response.success:
            return stop_response.model_dump().get("frame_count", 0)

        return 0
