import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, HttpUrl

from core import VideoDownloader
from models import TaskInfo, TaskStatus, downloads_db
from utils import get_logger, get_title

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
    title: str
    status: TaskStatus
    progress: float | None = None
    download_url: str | None = None
    error_message: str | None = None


download_executor = ThreadPoolExecutor(max_workers=5)

# TODO: 可以之後轉換成DownloadManager
downloader_db: dict[str, VideoDownloader] = {}


@app.post("/download")
async def start_download(
    request: DownloadRequest, background_tasks: BackgroundTasks
) -> TaskResponse:
    task_id = str(uuid4())[:6]
    title = get_title(request.url)
    downloads_db[task_id] = TaskInfo(
        id=task_id,
        url=request.url,
        title=title
    )
    background_tasks.add_task(download_video_task, downloads_db[task_id])
    return TaskResponse(task_id=task_id, title=title, status=TaskStatus.PENDING)

@app.get("/tasks")
async def list_tasks() -> dict[str, Any]:
    """列出所有任務"""
    all_tasks = {}
    for task_id, task in downloads_db.items():
        all_tasks[task_id] = {
            "title": task.title,
            "status": task.status.value,
            "progress": task.progress,
        }

    return {
        "tasks": all_tasks,
    }
@app.delete("/task/{task_id}")
async def cancel_task(
    task_id: str,
):
    if task_id not in downloader_db:
        raise HTTPException(status_code=404, detail="Task not found")
    cancel_download(downloader_db[task_id])


@app.get("/task/{task_id}")
async def check_task(
    task_id: str,
    background_tasks: BackgroundTasks
):
    get_logger().info(task_id)
    return downloads_db[task_id]

async def download_video_task(task: TaskInfo):
    try:
        downloader = VideoDownloader(task.id, str(task.url))
        downloader_db[task.id] = downloader
        downloads_db[task.id].status = TaskStatus.DOWNLOADING
        downloads_db[task.id].file_path = Path("downloads") / f"{task.id}.mp4"

        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(
            download_executor, downloader.download, task.id
        )
        if success:
            downloads_db[task.id].status = TaskStatus.COMPLETED
            title = task.title

            old_file = Path("downloads") / f"{task.id}.mp4"
            safe_title = "".join(c for c in title if c.isalnum() or c in " ._-").strip()
            new_file = Path("downloads") / f"{safe_title}.mp4"
            old_file.rename(new_file)

            downloads_db[task.id].file_path = new_file

        else:
            downloads_db[task.id].status = TaskStatus.FAILED
            downloads_db[task.id].error = "Download process returned failure"

    except Exception as e:
        downloads_db[task.id].status = TaskStatus.FAILED
        downloads_db[task.id].error = str(e)
        print(f"Download task {task.id} failed with error: {e}")

def cancel_download(downloader: VideoDownloader):
    downloader.cancel()
