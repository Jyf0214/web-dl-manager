import os
import sys
import signal
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
import httpx

# --- Configuration ---
OWNER = "Jyf0214"
REPO = "web-dl-manager"
BRANCH = "main"
BASE_DIR = Path(__file__).resolve().parent.parent
VERSION_INFO_FILE = BASE_DIR / ".version_info"
CHANGELOG_FILE = BASE_DIR / "CHANGELOG.md"
REQUIREMENTS_FILE = BASE_DIR / "app" / "requirements.txt"

# --- Helper Functions ---
def log(message: str):
    """Prints a message to stdout."""
    print(f"[Updater] {message}", flush=True)

def get_api_headers():
    """Returns headers for GitHub API requests, using a token if available."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    return headers

def get_latest_commit_sha() -> str:
    """Fetches the SHA of the latest commit from the specified branch."""
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/commits/{BRANCH}"
    with httpx.Client() as client:
        response = client.get(url, headers=get_api_headers())
        response.raise_for_status()
        return response.json()["sha"]

def get_local_commit_sha() -> str | None:
    """Reads the currently installed commit SHA from the version info file."""
    if not VERSION_INFO_FILE.exists():
        return None
    return VERSION_INFO_FILE.read_text().strip()

def store_commit_sha(sha: str):
    """Stores the given commit SHA in the version info file."""
    VERSION_INFO_FILE.write_text(sha)

def get_file_tree(commit_sha: str) -> list:
    """Gets the recursive file tree for a given commit SHA."""
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/git/trees/{commit_sha}?recursive=1"
    with httpx.Client() as client:
        response = client.get(url, headers=get_api_headers())
        response.raise_for_status()
        return response.json()["tree"]

def update_changelog(old_sha: str, new_sha: str):
    """Fetches commits between two SHAs and updates the changelog."""
    if not old_sha:
        log("No previous version found, skipping changelog generation.")
        return

    url = f"https://api.github.com/repos/{OWNER}/{REPO}/compare/{old_sha}...{new_sha}"
    with httpx.Client() as client:
        response = client.get(url, headers=get_api_headers())
        if response.status_code != 200:
            log(f"Could not fetch commit comparison, skipping changelog. Status: {response.status_code}")
            return
        
        data = response.json()
        commits = data.get("commits", [])
        if not commits:
            log("No new commits found for changelog.")
            return

        log_entries = [f"- {c['commit']['message'].splitlines()[0]} ({c['sha'][:7]})" for c in commits]
    logs = "\n".join(log_entries)
    
    today = datetime.now().strftime("%Y-%m-%d")
    # We don't have a version number here, so we use the commit SHA
    new_entry = f"## [{new_sha[:7]}] - {today}\n\n### Changed\n{logs}\n\n"
    
    if not CHANGELOG_FILE.exists():
        CHANGELOG_FILE.write_text(f"# Changelog\n\n{new_entry}")
    else:
        original_content = CHANGELOG_FILE.read_text()
        insert_position = original_content.find('\n\n') + 2
        updated_content = original_content[:insert_position] + new_entry + original_content[insert_position:]
        CHANGELOG_FILE.write_text(updated_content)
    
    log("CHANGELOG.md updated.")

def check_for_updates() -> dict:
    """Checks if updates are available without performing the update."""
    try:
        log("Checking for updates...")
        new_sha = get_latest_commit_sha()
        old_sha = get_local_commit_sha()
        
        update_available = new_sha != old_sha if old_sha else True
        commits_behind = 0
        
        if update_available and old_sha:
            # Get commit count between old and new SHA
            url = f"https://api.github.com/repos/{OWNER}/{REPO}/compare/{old_sha}...{new_sha}"
            with httpx.Client() as client:
                response = client.get(url, headers=get_api_headers())
                if response.status_code == 200:
                    data = response.json()
                    commits_behind = len(data.get("commits", []))
        
        return {
            "status": "success",
            "update_available": update_available,
            "current_version": old_sha[:7] if old_sha else "N/A",
            "latest_version": new_sha[:7],
            "commits_behind": commits_behind,
            "current_full_sha": old_sha,
            "latest_full_sha": new_sha
        }
    except Exception as e:
        log(f"Error checking for updates: {e}")
        return {
            "status": "error",
            "message": str(e),
            "update_available": False,
            "current_version": "N/A",
            "latest_version": "N/A",
            "commits_behind": 0
        }

def update_dependencies() -> dict:
    """Updates Python dependencies from requirements.txt."""
    try:
        log("Updating dependencies from requirements.txt...")
        
        if not REQUIREMENTS_FILE.exists():
            return {
                "status": "error",
                "message": f"Requirements file not found: {REQUIREMENTS_FILE}"
            }
        
        # Update pip first
        log("Upgrading pip...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=False, capture_output=True, text=True)
        
        # Install/upgrade dependencies
        log("Installing/upgrading dependencies...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)],
            check=False, capture_output=True, text=True
        )
        
        if result.returncode == 0:
            log("Dependencies updated successfully.")
            return {
                "status": "success",
                "message": "Dependencies updated successfully.",
                "output": result.stdout
            }
        else:
            log(f"Failed to update dependencies: {result.stderr}")
            return {
                "status": "error",
                "message": f"Failed to update dependencies: {result.stderr}",
                "output": result.stdout,
                "error": result.stderr
            }
    except Exception as e:
        log(f"Error updating dependencies: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

def get_update_info() -> dict:
    """Returns comprehensive update information."""
    try:
        old_sha = get_local_commit_sha()
        check_result = check_for_updates()
        
        # Get last update time if available
        last_update_time = None
        if VERSION_INFO_FILE.exists():
            mtime = VERSION_INFO_FILE.stat().st_mtime
            last_update_time = datetime.fromtimestamp(mtime).isoformat()
        
        # Get dependency count
        dependency_count = 0
        if REQUIREMENTS_FILE.exists():
            content = REQUIREMENTS_FILE.read_text()
            # Count non-empty, non-comment lines
            lines = [line.strip() for line in content.split('\n') if line.strip() and not line.strip().startswith('#')]
            dependency_count = len(lines)
        
        return {
            "status": "success",
            "current_version": old_sha[:7] if old_sha else "N/A",
            "current_full_sha": old_sha,
            "update_available": check_result.get("update_available", False),
            "latest_version": check_result.get("latest_version", "N/A"),
            "latest_full_sha": check_result.get("latest_full_sha"),
            "commits_behind": check_result.get("commits_behind", 0),
            "last_update_time": last_update_time,
            "dependencies_count": dependency_count,
            "requirements_file": str(REQUIREMENTS_FILE.relative_to(BASE_DIR)),
            "changelog_exists": CHANGELOG_FILE.exists()
        }
    except Exception as e:
        log(f"Error getting update info: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

def update_page_library() -> dict:
    """Updates page library (templates and static resources) from GitHub."""
    try:
        log("Updating page library (templates and static resources)...")
        
        # Get latest commit SHA
        new_sha = get_latest_commit_sha()
        
        # Get file tree for the latest commit
        file_tree = get_file_tree(new_sha)
        
        # Define page library directories to update
        page_lib_dirs = ["app/templates", "app/static"]
        updated_files = []
        skipped_files = []
        
        with httpx.Client(timeout=60) as client:
            for item in file_tree:
                if item["type"] == "blob":  # It's a file
                    path_str = item["path"]
                    
                    # Check if file belongs to page library directories
                    should_update = any(path_str.startswith(dir_prefix) for dir_prefix in page_lib_dirs)
                    if not should_update:
                        continue
                    
                    local_path = BASE_DIR / path_str
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    download_url = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{new_sha}/{path_str}"
                    log(f"Downloading page library file: {path_str}")
                    
                    response = client.get(download_url)
                    response.raise_for_status()
                    local_path.write_bytes(response.content)
                    updated_files.append(path_str)
        
        if not updated_files:
            log("No page library files needed updating.")
            return {
                "status": "success",
                "message": "Page library is already up to date.",
                "updated_files": [],
                "skipped_files": skipped_files
            }
        
        log(f"Page library updated successfully. Updated {len(updated_files)} files.")
        return {
            "status": "success",
            "message": f"Page library updated successfully. Updated {len(updated_files)} files.",
            "updated_files": updated_files,
            "skipped_files": skipped_files
        }
        
    except httpx.HTTPStatusError as e:
        log(f"HTTP error occurred while updating page library: {e.response.status_code} - {e.response.text}")
        return {
            "status": "error",
            "message": f"Failed to communicate with GitHub API: {e.response.status_code}"
        }
    except Exception as e:
        log(f"An unexpected error occurred while updating page library: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

def restart_application():
    """
    Checks for active downloads and restarts the application only when idle.
    Sends SIGHUP to PID 1 to allow the entrypoint script to handle the restart.
    """
    log("Preparing to restart application...")
    
    idle_check_url = "http://127.0.0.1:6275/server-status/json"
    max_retries = 5
    retry_delay = 10 # seconds

    for attempt in range(max_retries):
        try:
            # The /server-status/json endpoint requires authentication
            # We can't provide credentials here, so we assume the script is running on the same host
            # and can access the endpoint without auth. This is a limitation.
            with httpx.Client() as client:
                response = client.get(idle_check_url, timeout=10)
                response.raise_for_status()
                data = response.json()
                active_tasks = data.get("application", {}).get("active_tasks", 0)
                
                if active_tasks == 0:
                    log("No active tasks. Proceeding with restart.")
                    os.kill(1, signal.SIGHUP)
                    return # Exit after sending signal
                else:
                    log(f"There are {active_tasks} active tasks. Aborting restart.")
                    log("Please wait for tasks to complete and restart manually.")
                    return # Exit, do not proceed
        except httpx.RequestError as e:
            log(f"Could not connect to the application to check for active tasks (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                log(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                log("Could not connect to the application after multiple retries. Aborting restart.")
                log("The application might be in a broken state. Please check the logs and restart manually.")
                return # Exit, do not proceed
        except Exception as e:
            log(f"An unexpected error occurred during idle check: {e}")
            log("Aborting restart due to an unexpected error.")
            return # Exit, do not proceed


def run_update():
    """Main function to run the update process."""
    log("Starting update process via raw file download...")
    try:
        log("Fetching latest version information from GitHub...")
        new_sha = get_latest_commit_sha()
        old_sha = get_local_commit_sha()

        log(f"Local version: {old_sha or 'N/A'}")
        log(f"Remote version: {new_sha}")

        if new_sha == old_sha:
            log("Application is already up to date.")
            return {"status": "success", "message": "Already up to date."}

        log("New version available. Fetching file tree...")
        file_tree = get_file_tree(new_sha)

        ignore_list = {".git", ".github", ".gitignore", "Dockerfile", "entrypoint.sh"}
        
        with httpx.Client(timeout=60) as client:
            for item in file_tree:
                if item["type"] == "blob": # It's a file
                    path_str = item["path"]
                    
                    # Skip files we don't want to overwrite
                    if any(part in ignore_list for part in path_str.split('/')):
                        log(f"Skipping ignored file: {path_str}")
                        continue

                    local_path = BASE_DIR / path_str
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    download_url = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{new_sha}/{path_str}"
                    log(f"Downloading: {path_str}")
                    
                    response = client.get(download_url)
                    response.raise_for_status()
                    local_path.write_bytes(response.content)

        log("File download complete.")
        
        log("Updating dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)], check=True)
        log("Dependencies updated.")

        log("Updating changelog...")
        update_changelog(old_sha, new_sha)

        store_commit_sha(new_sha)
        log(f"Successfully updated to version {new_sha[:7]}.")

        return {"status": "success", "message": f"Update to version {new_sha[:7]} successful. Restarting..."}

    except httpx.HTTPStatusError as e:
        log(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        return {"status": "error", "message": f"Failed to communicate with GitHub API: {e.response.status_code}"}
    except Exception as e:
        log(f"An unexpected error occurred: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    run_update()
