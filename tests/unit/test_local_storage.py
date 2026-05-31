from io import BytesIO
from uuid import uuid4

from app.storage import local_storage


def test_save_document_file_uses_internal_document_path(tmp_path, monkeypatch):
    monkeypatch.setattr(local_storage.settings, "storage_path", str(tmp_path))
    document_id = uuid4()
    file = BytesIO(b"document bytes")
    storage = local_storage.LocalStorage()

    storage_path = storage.save_document_file(file, document_id)

    assert storage_path == tmp_path / str(document_id) / "document"


def test_save_document_file_writes_contents(tmp_path, monkeypatch):
    monkeypatch.setattr(local_storage.settings, "storage_path", str(tmp_path))
    document_id = uuid4()
    file = BytesIO(b"document bytes")
    storage = local_storage.LocalStorage()

    storage_path = storage.save_document_file(file, document_id)

    assert storage_path.read_bytes() == b"document bytes"


def test_get_document_path_returns_correct_path(tmp_path, monkeypatch):
    monkeypatch.setattr(local_storage.settings, "storage_path", str(tmp_path))
    document_id = uuid4()

    storage_path = local_storage.LocalStorage().get_document_path(document_id)

    assert storage_path == tmp_path / str(document_id) / "document"


def test_delete_document_file_removes_file(tmp_path, monkeypatch):
    monkeypatch.setattr(local_storage.settings, "storage_path", str(tmp_path))
    document_id = uuid4()
    storage = local_storage.LocalStorage()
    file = BytesIO(b"document bytes")
    storage_path = storage.save_document_file(file, document_id)

    storage.delete_document_file(document_id)

    assert not storage_path.exists()
