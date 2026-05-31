from pathlib import Path
from typing import BinaryIO, Protocol
from uuid import UUID


class StorageBackend(Protocol):
    def save_document_file(self, file: BinaryIO, document_id: UUID) -> Path: ...

    def delete_document_file(self, document_id: UUID) -> None: ...

    def get_document_path(self, document_id: UUID) -> Path: ...
