import asyncio
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel, HttpUrl

from core import VideoDownloader
from models import TaskInfo, TaskStatus, downloads_db
from utils import get_logger

app = FastAPI(title="YouTube Downloader")


@app.get("/")
def root():
    print("Hello from youtube-downloader!")


class DownloadRequest(BaseModel):
    url: HttpUrl

class TaskControlRequest(BaseModel):
    task_id: str

class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    progress: float | None = None
    download_url: str | None = None
    error_message: str | None = None


download_executor = ThreadPoolExecutor(max_workers=5)


@app.post("/download")
async def start_download(
    request: DownloadRequest, background_tasks: BackgroundTasks
) -> TaskResponse:
    task_id = str(uuid4())[:6]
    downloads_db[task_id] = TaskInfo(
        id=task_id,
        url=request.url,
    )
    background_tasks.add_task(download_video_task, downloads_db[task_id])
    return TaskResponse(task_id=task_id, status=TaskStatus.PENDING)

@app.delete("/task/{task_id}")
async def stop_task(
    task_id: str,
    background_tasks: BackgroundTasks
):
    ...

@app.get("/task/{task_id}")
async def check_task(
    task_id: str,
    background_tasks: BackgroundTasks
):
    get_logger().info(task_id)
    return downloads_db[task_id]


def fill_video_metadata(file: Path, info: dict[str, Any]) -> None:
    """使用 ffmpeg 為影片加上 metadata"""
    metadata_args = [
        "-metadata", f"title={info.get('title', '')}",
        "-metadata", f"artist={info.get('uploader', '')}",
        "-metadata", f"date={info.get('upload_date', '')}",
    ]

    output_file = file.with_name(file.stem + "_meta.webm")

    cmd = [
        "ffmpeg", "-y", "-i", str(file), *metadata_args,
        "-c", "copy", str(output_file)
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    output_file.replace(file)

async def download_video_task(task: TaskInfo):
    try:
        downloader = VideoDownloader(url=str(task.url))
        downloads_db[task.id].status = TaskStatus.DOWNLOADING
        downloads_db[task.id].file_path = Path("downloads") / f"{task.id}.mp4"

        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(
            download_executor, downloader.download, task.id
        )

        if success:
            downloads_db[task.id].status = TaskStatus.COMPLETED
            video_info = downloader.info()
            title = video_info.get("title") or datetime.now().isoformat()

            old_file = Path("downloads") / f"{task.id}.mp4"
            safe_title = "".join(c for c in title if c.isalnum() or c in " ._-").strip()
            new_file = Path("downloads") / f"{safe_title}.mp4"
            old_file.rename(new_file)

            fill_video_metadata(new_file, video_info)

            downloads_db[task.id].file_path = new_file

        else:
            downloads_db[task.id].status = TaskStatus.FAILED
            downloads_db[task.id].error = "Download process returned failure"

    except Exception as e:
        downloads_db[task.id].status = TaskStatus.FAILED
        downloads_db[task.id].error = str(e)
        print(f"Download task {task.id} failed with error: {e}")
