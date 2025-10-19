"""
Utility functions and classes for the YouTube Downloader project.
This module contains utility classes and functions used throughout the project.
"""

import subprocess
import re
import logging

from pydantic import HttpUrl
from typing import Optional, Dict, Any

from .models import VideoInfo


class MyLogger:
    """Custom logger for yt-dlp."""

    def __init__(self, name: str = "yt-dlp"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)

            formatter = logging.Formatter(
                fmt="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

            ch.setFormatter(formatter)

            self.logger.addHandler(ch)

            self.logger.propagate = False

    def info(self, msg: str):
        self.logger.info(msg)

    def debug(self, msg: str):
        self.logger.debug(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def error(self, msg: str):
        self.logger.error(msg)


logger = MyLogger()


def get_logger():
    return logger


def get_video_info(url: HttpUrl) -> Optional[VideoInfo]:
    try:
        result = subprocess.run(
            ["yt-dlp", "--get-title", str(url)],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            title = result.stdout.strip()
            if not title:
                logger.warning(f"Got empty title for {url}")
                title = "Unknown Title"
            return VideoInfo(title=title)
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            logger.warning(f"Failed to get video info for {url}: {error_msg}")
            return None

    except subprocess.TimeoutExpired:
        logger.error(f"Timeout getting video info for {url}")
        return None
    except Exception as e:
        logger.error(f"Error getting video info for {url}: {e}")
        return None


def extract_percent(line: str) -> float | None:
    match = re.search(r"(\d{1,3}(?:\.\d+)?)%", line)
    if not match:
        return None
    try:
        return float(match.group(1))
    except (ValueError, AttributeError):
        return None
