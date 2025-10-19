"""
Core functionality for the YouTube Downloader project.
This module contains the main download task logic and status management.
"""

import threading
import signal
from pathlib import Path
import os
import subprocess

from .utils import extract_percent, get_logger
from .models import downloads_db, TEMP_DIR

class VideoDownloader:
    def __init__(self, task_id: str, url: str):
        self.task_id = task_id
        self.url = url
        self.logger = get_logger()
        self.process: subprocess.Popen[str] | None = None
        self._cancellation_requested = threading.Event()

        self.logger.info(f"Initialized download task for URL: {url}")

    def _update_download_status(self, percent: float | None):
        if self.task_id in downloads_db:
            if percent: downloads_db[self.task_id].progress = percent

    def _monitor_download(self, process: subprocess.Popen[str]):
        for line in process.stdout:
            if self._cancellation_requested.is_set():
                self.logger.info(f"Cancellation detected for task {self.task_id}")
                break

            line = line.strip()
            percent = extract_percent(line)
            self._update_download_status(percent)
            self.logger.info(line)

    def download(self, filename: str) -> bool:
        self.logger.info("Starting download process...")

        # Ensure temp directory exists
        TEMP_DIR.mkdir(parents=True, exist_ok=True)

        cmd = [
            "yt-dlp",
            f"{self.url}",
            "--merge-output-format", "mp4",
            "--output", f"{TEMP_DIR}/{filename}.%(ext)s",
            "--no-playlist",
            "--progress",
        ]

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            preexec_fn=os.setsid,
        )
        self._monitor_download(self.process)

        return_code = self.process.wait()

        if self._cancellation_requested.is_set():
            self.logger.info(f"Download cancelled for task {self.task_id}")
            return False
        elif return_code == 0:
            self.logger.info(f"Download completed successfully for task {self.task_id}")
            self._update_download_status(100.0)
            return True
        else:
            # 讀取錯誤信息
            error_output = ""
            if self.process.stderr:
                error_output = self.process.stderr.read()

            self.logger.error(f"Download failed for task {self.task_id} (return code {return_code}): {error_output}")
            return False

    def _terminate_process(self) -> None:
        """
        Safely terminate the yt-dlp process.
        """
        if not self.process:
            return

        try:
            self.logger.info(f"Terminating process for task {self.task_id}")
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass

            try:
                self.process.wait(timeout=5.0)
                self.logger.info(f"Process terminated gracefully for task {self.task_id}")
            except subprocess.TimeoutExpired:
                self.logger.warning(f"Force killing process for task {self.task_id}")
                try:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass

        except Exception as e:
            self.logger.error(f"Error terminating process for task {self.task_id}: {e}")

    def cancel(self) -> None:
        """
        Request cancellation of the download.
        This sets a flag that will be checked during monitoring.
        """
        self.logger.info(f"Cancellation requested for task {self.task_id}")
        self._cancellation_requested.set()

        if self.process:
            self._terminate_process()

        # Clean up partial files from temp directory
        for part_file in TEMP_DIR.glob(f"{self.task_id}*.part"):
            try:
                os.remove(part_file)
                self.logger.info(f"Removed partial file: {part_file}")
            except Exception as e:
                self.logger.warning(f"Failed to remove partial file {part_file}: {e}")
