from io import BytesIO
from uuid import uuid4

from app.storage import local_storage


def test_save_document_file_uses_internal_document_path(tmp_path, monkeypatch):
    monkeypatch.setattr(local_storage.settings, "storage_path", str(tmp_path))
    document_id = uuid4()
    file = BytesIO(b"document bytes")

    storage_path = local_storage.save_document_file(file, document_id)

    assert storage_path == tmp_path / str(document_id) / "document"


def test_save_document_file_writes_contents(tmp_path, monkeypatch):
    monkeypatch.setattr(local_storage.settings, "storage_path", str(tmp_path))
    document_id = uuid4()
    file = BytesIO(b"document bytes")

    storage_path = local_storage.save_document_file(file, document_id)

    assert storage_path.read_bytes() == b"document bytes"
