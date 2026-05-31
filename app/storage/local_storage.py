from pathlib import Path
from shutil import copyfileobj
from typing import BinaryIO
from uuid import UUID

from app.config import settings


class LocalStorage:
    def save_document_file(self, file: BinaryIO, document_id: UUID) -> Path:
        storage_path = self.get_document_path(document_id)
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        file.seek(0)
        with storage_path.open("wb") as stored_file:
            copyfileobj(file, stored_file)
        return storage_path

    def delete_document_file(self, document_id: UUID) -> None:
        storage_path = self.get_document_path(document_id)
        if storage_path.exists():
            storage_path.unlink()
        document_dir = storage_path.parent
        if document_dir.exists():
            document_dir.rmdir()

    def get_document_path(self, document_id: UUID) -> Path:
        return Path(settings.storage_path) / str(document_id) / "document"
