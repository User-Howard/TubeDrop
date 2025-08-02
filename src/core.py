"""
Core functionality for the YouTube Downloader project.
This module contains the main download task logic and status management.
"""

from collections import ChainMap
from typing import Any, Optional, cast

from yt_dlp import YoutubeDL

from utils import get_logger


class DownloadStatus:
    """Base class for download status tracking."""

    def __init__(self, event_data: dict[str, Any]):
        self.event = event_data
        self.logger = get_logger()

    @classmethod
    def meets_condition(cls, event_data: dict[str, Any]) -> bool:
        """Check if this status class matches the given event data."""
        return False


class DownloadingStatus(DownloadStatus):
    """Status when download is in progress."""

    def __init__(self, event_data: dict[str, Any]):
        super().__init__(event_data)
        filename = event_data.get("filename", "Unknown file")
        progress = event_data.get("_percent_str", "0%")
        self.logger.info(f"Downloading: {filename} - {progress} complete")

    @classmethod
    def meets_condition(cls, event_data: dict[str, Any]) -> bool:
        return event_data.get("status") == "downloading"


class FinishedStatus(DownloadStatus):
    """Status when download is completed."""

    def __init__(self, event_data: dict[str, Any]):
        super().__init__(event_data)
        filename = event_data.get("filename", "Unknown file")
        self.logger.info(f"Download completed: {filename}")

    @classmethod
    def meets_condition(cls, event_data: dict[str, Any]) -> bool:
        return event_data.get("status") == "finished"


class VideoDownloader:
    def __init__(self, url: str):
        self.url = url
        self.video_info: dict[str, Any] | None = None
        self.status: Optional[DownloadStatus] = None
        self.logger = get_logger()
        self.ydl_opts: dict[str, Any] = {
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "postprocessors": [
                {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4",
                }
            ],
            "logger": self.logger,
            "progress_hooks": [self._progress_hook],
            "outtmpl": "./downloads/%(title)s.%(ext)s",
        }
        self.logger.info(f"Initialized download task for URL: {url}")

    def _progress_hook(self, event_data: dict[str, Any]) -> None:
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
        else:
            ValueError("No suitable DownloadStatus subclass found for event_data")

    def download(self, filename: str | None = None) -> bool:
        """
        同步下載方法 - 專門設計來在背景執行緒中運行

        這個方法會阻塞呼叫它的執行緒，但由於它會在 run_in_executor() 的
        背景執行緒中運行，所以不會影響主事件迴圈。
        """
        self.logger.info("Starting download process...")
        assert self.info()!={}, "Cannot proceed with download - video info extraction failed"

        # 準備下載選項
        user_opts = {"outtmpl": f"./downloads/{filename}.%(ext)s" if filename else None}
        opts = ChainMap(user_opts, self.ydl_opts)

        try:
            with YoutubeDL(dict(opts)) as ydl:
                ydl.process_info(self.video_info)
            self.logger.info("Download process completed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            return False

    def info(self) -> dict[str, Any]:
        """
        同步版本的影片資訊獲取
        """
        if self.video_info:
            return self.video_info

        self.logger.info("Fetching video information...")
        try:
            with YoutubeDL(self.ydl_opts) as ytd:
                self.video_info = cast(dict[str, Any], ytd.extract_info(self.url, download=False))
            if self.video_info:
                title = self.video_info.get("title", "Unknown")
                self.logger.info(f"Video title: {title}")
        except Exception as e:
            self.logger.error(f"Failed to extract video info: {e}")
            return {}
        return self.video_info
