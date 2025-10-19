# schemas/youtube.py
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class TaskStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"


class YouTubeDownloadRequest(BaseModel):
    """YouTube 下載請求 - 現在只需要網址"""

    url: HttpUrl = Field(..., description="YouTube 影片網址")

    class Config:
        schema_extra = {
            "example": {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        }


class VideoInfo(BaseModel):
    """影片基本資訊 - 讓用戶知道下載的是什麼影片"""

    title: str = Field(..., description="影片標題")
    duration: int = Field(..., description="影片長度（秒）")
    uploader: str = Field(..., description="頻道名稱")


class DownloadTask(BaseModel):
    """下載任務狀態回應"""

    task_id: str = Field(..., description="任務唯一識別碼")
    status: TaskStatus = Field(..., description="目前下載狀態")
    progress: Optional[float] = Field(None, ge=0, le=100, description="下載進度百分比")
    video_info: Optional[VideoInfo] = Field(None, description="影片資訊")
    download_url: Optional[str] = Field(None, description="檔案下載連結")
    error_message: Optional[str] = Field(None, description="錯誤訊息")
    created_at: str = Field(..., description="任務開始時間")
