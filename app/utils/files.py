from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import AppException


def ensure_storage_path(*parts: str) -> Path:
    base = Path(settings.media_root)
    base.mkdir(parents=True, exist_ok=True)
    target = base.joinpath(*parts)
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


async def validate_upload(upload: UploadFile) -> None:
    allowed_content_types = {
        "image/png",
        "image/jpeg",
        "image/webp",
        "application/pdf",
        "application/zip",
        "application/postscript",
        "application/illustrator",
    }
    if upload.content_type not in allowed_content_types:
        raise AppException("Unsupported file type", 400)


async def save_upload(upload: UploadFile, *parts: str) -> tuple[str, int]:
    await validate_upload(upload)
    extension = Path(upload.filename or "file").suffix
    target = ensure_storage_path(*parts, f"{uuid4().hex}{extension}")
    content = await upload.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise AppException(f"File exceeds {settings.max_upload_size_mb} MB limit", 400)
    target.write_bytes(content)
    return str(target), len(content)


def safe_relative_storage_path(absolute_path: str) -> str:
    base = Path(settings.media_root).resolve()
    path = Path(absolute_path).resolve()
    if not str(path).startswith(str(base)):
        raise AppException("Invalid file path", 400)
    return str(path.relative_to(base)).replace("\\", "/")
