"""Filesystem API for native folder picker."""

import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/fs", tags=["filesystem"])


class FolderPickerResult(BaseModel):
    """Result of folder picker dialog."""

    path: str | None
    cancelled: bool = False
    error: str | None = None


@router.post("/pick-folder", response_model=FolderPickerResult)
async def pick_folder() -> FolderPickerResult:
    """
    Open native folder picker dialog and return selected path.

    Uses osascript on macOS, zenity on Linux.
    """
    if sys.platform == "darwin":
        # macOS: Use osascript to open native folder picker
        script = '''
        tell application "System Events"
            activate
            set folderPath to choose folder with prompt "Select a project folder"
            return POSIX path of folderPath
        end tell
        '''
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=120,  # 2 minutes timeout
            )
            if result.returncode == 0:
                path = result.stdout.strip().rstrip("/")
                return FolderPickerResult(path=path)
            else:
                # User cancelled or error
                if "User canceled" in result.stderr:
                    return FolderPickerResult(path=None, cancelled=True)
                return FolderPickerResult(
                    path=None, error=result.stderr.strip() or "Folder picker cancelled"
                )
        except subprocess.TimeoutExpired:
            return FolderPickerResult(path=None, error="Folder picker timed out")
        except Exception as e:
            return FolderPickerResult(path=None, error=str(e))

    elif sys.platform == "linux":
        # Linux: Try zenity first, then kdialog
        try:
            result = subprocess.run(
                ["zenity", "--file-selection", "--directory", "--title=Select a project folder"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                return FolderPickerResult(path=result.stdout.strip())
            return FolderPickerResult(path=None, cancelled=True)
        except FileNotFoundError:
            # Try kdialog if zenity not available
            try:
                result = subprocess.run(
                    ["kdialog", "--getexistingdirectory", Path.home()],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if result.returncode == 0:
                    return FolderPickerResult(path=result.stdout.strip())
                return FolderPickerResult(path=None, cancelled=True)
            except FileNotFoundError:
                return FolderPickerResult(
                    path=None, error="No folder picker available (install zenity or kdialog)"
                )
        except Exception as e:
            return FolderPickerResult(path=None, error=str(e))

    else:
        return FolderPickerResult(
            path=None, error=f"Folder picker not supported on {sys.platform}"
        )


@router.get("/home")
async def get_home_directory() -> dict:
    """Get the user's home directory path."""
    return {"path": str(Path.home())}
