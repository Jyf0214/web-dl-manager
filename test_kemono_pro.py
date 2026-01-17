import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.tasks import process_kemono_pro_job
from app.database import init_db

async def test_pro():
    init_db()
    task_id = "test-pro-task"
    service = "patreon"
    creator_id = "28444363"
    upload_service = "gofile" # Use gofile for easier testing
    upload_path = ""
    params = {
        "upload_service": "gofile",
        "gofile_token": "", # Public upload
    }
    
    print(f"[*] Starting local test for Kemono Pro...")
    print(f"[*] Target: {service}/{creator_id}")
    
    try:
        # We run the job. Note: it will try to fetch ALL posts.
        # For a quick test, I'll rely on the fact that we can monitor the logs.
        await process_kemono_pro_job(
            task_id=task_id,
            service=service,
            creator_id=creator_id,
            upload_service=upload_service,
            upload_path=upload_path,
            params=params
        )
        print("[*] Job finished execution.")
    except Exception as e:
        print(f"[!] Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(test_pro())
