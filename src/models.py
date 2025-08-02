from enum import Enum
from pathlib import Path

from pydantic import BaseModel, HttpUrl


class TaskStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskInfo(BaseModel):
    id: str
    url: HttpUrl
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    file_path: Path | None = None
    error: str | None = None


# 簡單的記憶體資料庫 - 適合學習和原型開發
# 在真實專案中，你可能會想要使用 SQLite 或其他資料庫
downloads_db: dict[str, TaskInfo] = {}
