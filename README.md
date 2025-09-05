# StreamVault
Simple YouTube video downloader built with Python and yt-dlp.
## Features

- Download YouTube videos with progress tracking
- Custom logging system
- Clean API interface

## Installation
```bash
git clone https://github.com/yourusername/streamvault.git
cd streamvault
pip install -r requirements.txt
```
## Usage
```python
from downloader import DownloadTask

task = DownloadTask("https://www.youtube.com/watch?v=example")
info = task.info()
task.download()
```
## License
MIT License