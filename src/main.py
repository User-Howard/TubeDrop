from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel, HttpUrl

from core import VideoDownloader
from models import TaskInfo, TaskStatus, downloads_db

app = FastAPI(title="YouTube Downloader")



@app.get("/")
def main():
    print("Hello from youtube-downloader!")

class DownloadRequest(BaseModel):
    url: HttpUrl

@app.post("/download")
async def start_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid4())

    downloads_db[task_id] = TaskInfo(
        id=task_id,
        url=request.url
    )
    background_tasks.add_task(download_video, downloads_db[task_id])
    return

async def download_video(task: TaskInfo):
    try:
        downloader = VideoDownloader(url=str(task.url))
        downloads_db[task.id].status = TaskStatus.DOWNLOADING
        success = downloader.download(filename=task.id)
        if success:
            downloads_db[task.id].status = TaskStatus.COMPLETED
        else:
            downloads_db[task.id].status = TaskStatus.FAILED
    except Exception as e:
        downloads_db[task.id].status = TaskStatus.FAILED
        downloads_db[task.id].error = str(e)
