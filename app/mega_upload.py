import os
import asyncio
from pathlib import Path
from typing import Optional
from mega import Mega

async def upload_to_mega(file_path: Path, email: str, password: str, two_factor_code: Optional[str] = None, status_file: Optional[Path] = None):
    """
    Uploads a file to MEGA cloud storage.
    
    Args:
        file_path: Path to the file to upload
        email: MEGA account email
        password: MEGA account password
        two_factor_code: Optional 2FA code if enabled
        status_file: Optional path to status log file
    
    Returns:
        str: Public download link if successful
    """
    def log_message(msg: str):
        if status_file:
            with open(status_file, "a", encoding="utf-8") as f:
                f.write(f"{msg}\n")
    
    try:
        log_message(f"Starting MEGA upload for: {file_path.name}")
        
        # Initialize MEGA client
        mega = Mega()
        
        # Login to MEGA
        log_message("Logging into MEGA account...")
        if two_factor_code:
            m = mega.login(email, password, two_factor_code)
        else:
            m = mega.login(email, password)
        
        # Upload file
        log_message(f"Uploading file: {file_path.name} ({file_path.stat().st_size / 1024 / 1024:.2f} MB)")
        
        # Use asyncio to run blocking operation in thread pool
        loop = asyncio.get_event_loop()
        file = await loop.run_in_executor(None, m.upload, str(file_path))
        
        # Get public link
        log_message("Generating public download link...")
        link = await loop.run_in_executor(None, m.get_upload_link, file)
        
        log_message(f"MEGA upload completed successfully!")
        log_message(f"Download link: {link}")
        
        return link
        
    except Exception as e:
        error_msg = f"MEGA upload failed: {str(e)}"
        log_message(f"ERROR: {error_msg}")
        raise RuntimeError(error_msg)