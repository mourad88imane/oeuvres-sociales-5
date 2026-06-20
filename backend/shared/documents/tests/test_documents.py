import io
import tempfile

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="admin@t.dz", password="P@ss123!",
        first_name="Admin", last_name="Test", role="admin",
    )


@pytest.fixture
def api_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def sample_file():
    return SimpleUploadedFile(
        "test.pdf",
        b"%PDF-1.4 fake pdf content for testing",
        content_type="application/pdf",
    )


class TestDocumentModel:

    def test_create_document(self, admin_user):
        from shared.documents.models import Document
        doc = Document.objects.create(
            title="Test Document",
            description="A test",
            category="general",
            file_name="test.pdf",
            uploaded_by=admin_user,
        )
        assert doc.id is not None
        assert doc.category == "general"
        assert str(doc) == "Test Document"
        assert doc.is_deleted is False

    def test_soft_delete(self, admin_user):
        from shared.documents.models import Document
        doc = Document.objects.create(
            title="Delete test",
            category="contract",
            file_name="contract.pdf",
            uploaded_by=admin_user,
        )
        doc.is_deleted = True
        doc.save(update_fields=["is_deleted"])
        assert doc.is_deleted is True


class TestDocumentAPI:

    def test_upload_document(self, api_client, sample_file):
        resp = api_client.post(
            "/api/v1/documents/upload/",
            {"title": "Uploaded Doc", "file": sample_file, "category": "report"},
            format="multipart",
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "success"
        assert data["data"]["title"] == "Uploaded Doc"

    def test_list_documents(self, api_client, admin_user):
        from shared.documents.models import Document
        Document.objects.create(
            title="Doc A", category="general", file_name="a.pdf",
            uploaded_by=admin_user,
        )
        Document.objects.create(
            title="Doc B", category="contract", file_name="b.pdf",
            uploaded_by=admin_user,
        )
        resp = api_client.get("/api/v1/documents/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2

    def test_filter_by_category(self, api_client, admin_user):
        from shared.documents.models import Document
        Document.objects.create(
            title="Medical Doc", category="medical", file_name="m.pdf",
            uploaded_by=admin_user,
        )
        resp = api_client.get("/api/v1/documents/?category=medical")
        assert resp.status_code == 200
        assert all(d["category"] == "medical" for d in resp.json())

    def test_categories_endpoint(self, api_client):
        resp = api_client.get("/api/v1/documents/categories/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        categories = data["data"]
        assert any(c["value"] == "medical" for c in categories)
        assert any(c["value"] == "contract" for c in categories)

    def test_soft_delete_document(self, api_client, admin_user):
        from shared.documents.models import Document
        doc = Document.objects.create(
            title="To delete", category="other", file_name="del.pdf",
            uploaded_by=admin_user,
        )
        resp = api_client.delete(f"/api/v1/documents/{doc.id}/")
        assert resp.status_code == 204
        doc.refresh_from_db()
        assert doc.is_deleted is True

    def test_upload_requires_auth(self, sample_file):
        client = APIClient()
        resp = client.post(
            "/api/v1/documents/upload/",
            {"title": "No auth", "file": sample_file},
            format="multipart",
        )
        assert resp.status_code == 401
