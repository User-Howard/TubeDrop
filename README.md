# YouTube Downloader

一個簡單的 YouTube 視頻下載工具，使用 Python 和 yt-dlp 開發。

## 功能特點

- 支持從 YouTube 下載視頻
- 提供下載進度追蹤
- 自定義日誌記錄
- 簡潔的 API 接口

## 安裝

1. 克隆專案：
```bash
git clone https://github.com/yourusername/youtube-downloader.git
cd youtube-downloader
```

2. 安裝依賴：
```bash
pip install -r requirements.txt
```

## 使用方法

```python
from downloader import DownloadTask

# 創建下載任務
task = DownloadTask("https://www.youtube.com/watch?v=example")

# 獲取視頻信息
info = task.info()

# 開始下載
task.download()
```

## 開發

1. 安裝開發依賴：
```bash
pip install -r requirements-dev.txt
```

2. 運行測試：
```bash
pytest tests/
```

## 授權

MIT License 