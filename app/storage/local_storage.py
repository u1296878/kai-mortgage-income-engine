from pathlib import Path
from shutil import copyfileobj
from typing import BinaryIO
from uuid import UUID

from app.config import settings


def save_document_file(file: BinaryIO, document_id: UUID) -> Path:
    document_dir = Path(settings.storage_path) / str(document_id)
    document_dir.mkdir(parents=True, exist_ok=True)
    storage_path = document_dir / "document"
    file.seek(0)
    with storage_path.open("wb") as stored_file:
        copyfileobj(file, stored_file)
    return storage_path
