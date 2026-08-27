"""
Storage client — abstracts local filesystem vs S3/GCS.
In dev, files are saved to LOCAL_STORAGE_PATH.
Switch STORAGE_BACKEND=s3 for production.
"""

import os
import uuid
import aiofiles
from pathlib import Path

STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")
LOCAL_STORAGE_PATH = Path(os.getenv("LOCAL_STORAGE_PATH", "./uploads"))


async def save_file(file_bytes: bytes, filename: str, folder: str = "products") -> str:
    """
    Save file_bytes and return a public URL (or local path in dev).

    Args:
        file_bytes: Raw bytes of the file.
        filename:   Original filename with extension.
        folder:     Sub-folder inside the storage bucket / local dir.

    Returns:
        URL string pointing to the saved file.
    """
    ext = Path(filename).suffix
    unique_name = f"{uuid.uuid4().hex}{ext}"

    if STORAGE_BACKEND == "local":
        dest = LOCAL_STORAGE_PATH / folder
        dest.mkdir(parents=True, exist_ok=True)
        file_path = dest / unique_name
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_bytes)
        return f"/uploads/{folder}/{unique_name}"

    elif STORAGE_BACKEND == "s3":
        # TODO: implement boto3 async upload
        raise NotImplementedError("S3 backend not yet implemented — set STORAGE_BACKEND=local")

    elif STORAGE_BACKEND == "gcs":
        # TODO: implement GCS async upload
        raise NotImplementedError("GCS backend not yet implemented — set STORAGE_BACKEND=local")

    else:
        raise ValueError(f"Unknown STORAGE_BACKEND: {STORAGE_BACKEND}")
