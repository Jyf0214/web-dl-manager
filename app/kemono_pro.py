import os
import asyncio
import shutil
import logging
import tempfile
from pathlib import Path
from typing import Optional

from .database import db_config
from .config import DOWNLOADS_DIR, STATUS_DIR
from .utils import update_task_status

# 获取logger
logger = logging.getLogger(__name__)

def create_netscape_cookies(cookies_str: str) -> str:
    """Converts a standard cookie string to a Netscape format cookie file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("# Netscape HTTP Cookie File\n")
        f.write("# http://curl.haxx.se/rfc/cookie_spec.html\n")
        f.write("# This is a generated file!  Do not edit.\n\n")
        
        for cookie in cookies_str.split(';'):
            if '=' in cookie:
                name, value = cookie.strip().split('=', 1)
                # domain, domain_specified, path, secure, expires, name, value
                # We use .kemono.cr as a default domain
                f.write(f".kemono.cr\tTRUE\t/\tFALSE\t0\t{name}\t{value}\n")
                f.write(f".coomer.su\tTRUE\t/\tFALSE\t0\t{name}\t{value}\n")
        return f.name

async def process_kemono_pro_job(task_id: str, service: str, creator_id: str, upload_service: str, upload_path: str, params: dict, cookies: Optional[str] = None, kemono_username: Optional[str] = None, kemono_password: Optional[str] = None):
    """Main background task for Kemono DL Pro using kemono-dl CLI."""
    from .tasks import task_semaphore, upload_uncompressed
    
    async with task_semaphore:
        task_download_dir = DOWNLOADS_DIR / task_id
        task_download_dir.mkdir(parents=True, exist_ok=True)
        status_file = STATUS_DIR / f"{task_id}.log"
        upload_log_file = STATUS_DIR / f"{task_id}_upload.log"
        
        update_task_status(task_id, {"status": "running", "url": f"{service}/{creator_id} (Pro-v2)"})
        
        cookie_file = None
        try:
            # 1. Prepare Command
            # Base URL: https://kemono.cr/service/user/creator_id
            url = f"https://kemono.cr/{service}/user/{creator_id}"
            
            cmd = ["python3", "-m", "kemono_dl", "--path", str(task_download_dir), url]
            
            # Use specific output template to match original style: [Date] [Title]--Filename
            # kemono-dl templates: {published} for date, {title} for title, {filename} for original name
            # Note: We use a flattened structure as we did before
            cmd.extend(["--output", "[{published}] [{title}]--{filename}"])

            if cookies:
                cookie_file = create_netscape_cookies(cookies)
                cmd.extend(["--cookies", cookie_file])
            elif kemono_username and kemono_password:
                cmd.extend(["--kemono-login", kemono_username, kemono_password])

            with open(status_file, "a") as f: f.write(f"Starting kemono-dl for {url}...\n")

            # 2. Execute process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )

            # Monitor output to update progress (simple implementation)
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                decoded_line = line.decode('utf-8', errors='ignore')
                with open(status_file, "a") as f:
                    f.write(decoded_line)
                
                # Try to parse progress if possible (kemono-dl output varies)
                if "Downloading" in decoded_line:
                    update_task_status(task_id, {"progress_count": "Downloading..."})

            await process.wait()

            if process.returncode != 0:
                raise Exception(f"kemono-dl exited with code {process.returncode}")

            with open(status_file, "a") as f:
                f.write("\nDownload complete. Starting upload...\n")

            # 3. Upload
            update_task_status(task_id, {"status": "uploading"})
            await upload_uncompressed(task_id, upload_service, upload_path, params, upload_log_file)
            update_task_status(task_id, {"status": "completed"})
            
        except Exception as e:
            error_msg = f"Kemono Pro v2 failed: {str(e)}"
            logger.error(error_msg)
            update_task_status(task_id, {"status": "failed", "error": error_msg})
            with open(status_file, "a") as f:
                f.write(f"\n[ERROR] {error_msg}\n")
        finally:
            if cookie_file and os.path.exists(cookie_file):
                os.unlink(cookie_file)
            if os.path.exists(task_download_dir):
                shutil.rmtree(task_download_dir)
