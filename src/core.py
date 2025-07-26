"""
Core functionality for the YouTube Downloader project.
This module contains the main download task logic and status management.
"""
from collections import ChainMap
from typing import Any, Optional

from yt_dlp import YoutubeDL

from utils import get_logger


class DownloadStatus:
    """Base class for download status tracking."""

    def __init__(self, event_data: dict):
        self.event = event_data
        self.logger = get_logger()

    @classmethod
    def meets_condition(cls, event_data: dict) -> bool:
        """Check if this status class matches the given event data."""
        return False


class DownloadingStatus(DownloadStatus):
    """Status when download is in progress."""

    def __init__(self, event_data: dict):
        super().__init__(event_data)
        filename = event_data.get('filename', 'Unknown file')
        progress = event_data.get('_percent_str', '0%')
        self.logger.info(f"Downloading: {filename} - {progress} complete")

    @classmethod
    def meets_condition(cls, event_data: dict) -> bool:
        return event_data.get('status') == 'downloading'


class FinishedStatus(DownloadStatus):
    """Status when download is completed."""

    def __init__(self, event_data: dict):
        super().__init__(event_data)
        filename = event_data.get('filename', 'Unknown file')
        self.logger.info(f"Download completed: {filename}")

    @classmethod
    def meets_condition(cls, event_data: dict) -> bool:
        return event_data.get('status') == 'finished'


class VideoDownloader:
    """
    A class representing a video download task using yt-dlp.

    This class encapsulates the process of downloading a video from a specified URL.
    It manages the extraction of video information, progress tracking, and handling download status.

    Attributes:
        url: The URL of the video to be downloaded.
        video_info: The video information extracted from the URL.
        status: The current status of the download task.
        logger: Logger instance for this task.
        ydl_opts: Options for yt-dlp configuration.
    """

    def __init__(self, url: str):
        self.url = url
        self.video_info: dict[str, Any] | None = None
        self.status: Optional[DownloadStatus] = None
        self.logger = get_logger()

        self.ydl_opts: dict[str, Any] = {
            'format': 'bestvideo+bestaudio/best',
            'logger': self.logger,
            'progress_hooks': [self._progress_hook],
            'outtmpl': "./downloads/%(title)s.%(ext)s"
        }

        self.logger.info(f"Initialized download task for URL: {url}")

    def info(self) -> Optional[dict[str, Any]]:
        """
        Get the information of the video.

        Returns:
            Video information dictionary or None if extraction fails.
        """
        if self.video_info:
            return self.video_info

        self.logger.info("Fetching video information...")

        try:
            with YoutubeDL(self.ydl_opts) as ytd:
                self.video_info = ytd.extract_info(self.url, download=False)

            if self.video_info:
                title = self.video_info.get('title', 'Unknown')
                self.logger.info(f"Video title: {title}")

        except Exception as e:
            self.logger.error(f"Failed to extract video info: {e}")
            return None

        return self.video_info

    def _progress_hook(self, event_data: dict) -> None:
        """
        Progress hook to update download status.

        Args:
            event_data: Event data from yt-dlp
        """
        status_classes = DownloadStatus.__subclasses__()

        for status_cls in status_classes:
            if status_cls.meets_condition(event_data):
                self.status = status_cls(event_data)
                break

    def download(self, filename: str | None = None) -> bool:
        """
        Start the download process.

        Returns:
            True if download successful, False otherwise.
        """
        self.logger.info("Starting download process...")

        # Get video info first
        if not self.info():
            self.logger.error("Cannot proceed with download - video info extraction failed")
            return False

        user_opts = {
            'outtmpl': f"./downloads/{filename}.%(ext)s" if filename else None
        }

        opts = ChainMap(user_opts, self.ydl_opts)

        try:
            with YoutubeDL(opts) as ydl:
                ydl.process_info(self.video_info)

            self.logger.info("Download process completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            return False
