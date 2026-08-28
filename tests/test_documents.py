import io
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db, SessionLocal
from app.models.user import User
from app.core.security import get_password_hash


@pytest.fixture(scope="module")
def client():
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def auth_headers(client):
    """Create a test user and return auth headers."""
    email = f"doctest_{uuid.uuid4().hex[:6]}@example.com"
    client.post("/auth/signup", json={
        "name": "Doc Test User",
        "email": email,
        "password": "TestPassword123!"
    })
    login = client.post("/auth/login", json={
        "email": email,
        "password": "TestPassword123!"
    })
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _make_pdf_bytes():
    """Create a minimal valid PDF in memory."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]"
        b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
        b"4 0 obj<</Length 44>>stream\n"
        b"BT /F1 12 Tf 100 700 Td (Hello World Test PDF) Tj ET\n"
        b"endstream endobj\n"
        b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"xref\n0 6\n"
        b"0000000000 65535 f\n"
        b"0000000009 00000 n\n"
        b"0000000058 00000 n\n"
        b"0000000115 00000 n\n"
        b"0000000266 00000 n\n"
        b"0000000360 00000 n\n"
        b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n430\n%%EOF"
    )


def test_upload_invalid_type(client, auth_headers):
    """Non-PDF/DOCX files must be rejected."""
    response = client.post(
        "/documents",
        headers=auth_headers,
        files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"] or "DOCX" in response.json()["detail"]


def test_upload_document(client, auth_headers):
    """Upload a PDF and confirm 201 + processing status."""
    pdf_bytes = _make_pdf_bytes()
    response = client.post(
        "/documents",
        headers=auth_headers,
        files={"file": ("test_document.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test_document.pdf"
    assert data["status"] == "processing"
    assert "id" in data
    assert "owner_id" in data
    return data["id"]


def test_list_documents(client, auth_headers):
    """GET /documents returns only the authenticated user's documents."""
    response = client.get("/documents", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_document_status(client, auth_headers):
    """GET /documents/{id} returns the correct document."""
    # Upload first
    pdf_bytes = _make_pdf_bytes()
    upload = client.post(
        "/documents",
        headers=auth_headers,
        files={"file": ("status_check.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    doc_id = upload.json()["id"]

    response = client.get(f"/documents/{doc_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == doc_id
    assert response.json()["status"] in ("processing", "ready", "failed")


def test_delete_document(client, auth_headers):
    """DELETE /documents/{id} removes the document."""
    pdf_bytes = _make_pdf_bytes()
    upload = client.post(
        "/documents",
        headers=auth_headers,
        files={"file": ("to_delete.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    doc_id = upload.json()["id"]

    del_response = client.delete(f"/documents/{doc_id}", headers=auth_headers)
    assert del_response.status_code == 200
    assert del_response.json()["detail"] == "Document deleted successfully"

    # Confirm it's gone
    get_response = client.get(f"/documents/{doc_id}", headers=auth_headers)
    assert get_response.status_code == 404


def test_document_ownership_isolation(client, auth_headers):
    """A user cannot access another user's document."""
    # Create a second user
    email2 = f"other_{uuid.uuid4().hex[:6]}@example.com"
    client.post("/auth/signup", json={
        "name": "Other User",
        "email": email2,
        "password": "OtherPassword123!"
    })
    login2 = client.post("/auth/login", json={
        "email": email2,
        "password": "OtherPassword123!"
    })
    token2 = login2.json()["access_token"]
    other_headers = {"Authorization": f"Bearer {token2}"}

    # Upload doc as user 1
    pdf_bytes = _make_pdf_bytes()
    upload = client.post(
        "/documents",
        headers=auth_headers,
        files={"file": ("owner_doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    doc_id = upload.json()["id"]

    # User 2 must not see user 1's document
    response = client.get(f"/documents/{doc_id}", headers=other_headers)
    assert response.status_code == 404
