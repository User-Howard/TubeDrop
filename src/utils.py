"""
Utility functions and classes for the YouTube Downloader project.
This module contains utility classes and functions used throughout the project.
"""

import logging


class MyLogger:
    """Custom logger for yt-dlp."""

    def __init__(self, name: str = "yt-dlp"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # 避免重複添加handler
        if not self.logger.handlers:
            # Create console handler and set level
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)

            # Create formatter
            formatter = logging.Formatter(
                fmt="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

            # Add formatter to ch
            ch.setFormatter(formatter)

            # Add ch to logger
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
