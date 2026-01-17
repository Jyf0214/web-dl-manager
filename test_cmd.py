import asyncio
from app.tasks import process_download_job
from pathlib import Path
import os

async def test():
    task_id = "test-task-123"
    url = "https://kemono.cr/patreon/user/28444363/post/148258017"
    params = {
        "kemono_path_template": "true",
        "enable_compression": "false"
    }
    
    # We only want to see the printed command from our modified tasks.py
    try:
        await process_download_job(
            task_id=task_id,
            url=url,
            downloader="gallery-dl",
            service="gofile",
            upload_path="",
            params=params,
            enable_compression=False,
            kemono_path_template="true"
        )
    except Exception as e:
        print(f"Caught expected error after mock: {e}")

if __name__ == "__main__":
    asyncio.run(test())
