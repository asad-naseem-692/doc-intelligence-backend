import os
import uuid
from pathlib import Path
from typing import Optional


UPLOAD_DIR = Path(__file__).parent.parent.parent / "storage" / "uploads"


def ensure_upload_dir() -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_DIR


def save_uploaded_file(file_content: bytes, original_filename: str) -> str:
    """Save uploaded file to storage and return the file path."""
    upload_dir = ensure_upload_dir()
    ext = Path(original_filename).suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = upload_dir / unique_name
    with open(file_path, "wb") as f:
        f.write(file_content)
    return str(file_path)


def delete_stored_file(file_path: Optional[str]) -> None:
    """Delete stored file if it exists."""
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass
