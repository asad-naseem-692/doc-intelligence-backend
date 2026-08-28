import io
import time
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db, SessionLocal
from app.services.pipeline_service import _process_document_sync
from app.models.document import Document


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
def user1_headers(client):
    email = f"qtest1_{uuid.uuid4().hex[:6]}@example.com"
    client.post("/auth/signup", json={"name": "Q User 1", "email": email, "password": "Password123!"})
    res = client.post("/auth/login", json={"email": email, "password": "Password123!"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def user2_headers(client):
    email = f"qtest2_{uuid.uuid4().hex[:6]}@example.com"
    client.post("/auth/signup", json={"name": "Q User 2", "email": email, "password": "Password123!"})
    res = client.post("/auth/login", json={"email": email, "password": "Password123!"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _make_sample_pdf(text_content: str) -> bytes:
    """Create a minimal single-page PDF with custom text."""
    # Simple valid PDF
    stream_content = f"BT /F1 12 Tf 50 700 Td ({text_content}) Tj ET".encode("utf-8")
    stream_len = len(stream_content)
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]"
        b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
        b"4 0 obj<</Length " + str(stream_len).encode("utf-8") + b">>stream\n"
        + stream_content + b"\nendstream endobj\n"
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


def test_query_empty_question(client, user1_headers):
    """Empty question returns 400."""
    res = client.post("/query", headers=user1_headers, json={"question": ""})
    assert res.status_code == 400


def test_query_no_documents_fallback(client, user2_headers):
    """User with no uploaded documents gets fallback message."""
    res = client.post("/query", headers=user2_headers, json={"question": "What is our company revenue?"})
    assert res.status_code == 200
    data = res.json()
    assert data["is_fallback"] is True
    assert "couldn't find enough information" in data["answer"].lower()
    assert data["citations"] == []


def test_query_grounded_answer(client, user1_headers):
    """Upload document, process it synchronously for test, and query."""
    pdf_bytes = _make_sample_pdf("Acme Corporation Project Titan launched in March 2024 with a budget of 5 million dollars.")
    upload = client.post(
        "/documents",
        headers=user1_headers,
        files={"file": ("project_titan.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload.status_code == 201
    doc_id = upload.json()["id"]

    # Process synchronously to ensure embeddings and chunks are ready
    _process_document_sync(doc_id)

    # Query with relevant question
    res = client.post(
        "/query",
        headers=user1_headers,
        json={"question": "When was Project Titan launched and what was its budget?"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_fallback"] is False
    assert "March 2024" in data["answer"] or "2024" in data["answer"]
    assert "5 million" in data["answer"] or "million" in data["answer"]
    assert len(data["citations"]) > 0
    assert data["citations"][0]["filename"] == "project_titan.pdf"


def test_query_irrelevant_fallback(client, user1_headers):
    """Irrelevant question on user1 triggers fallback."""
    res = client.post(
        "/query",
        headers=user1_headers,
        json={"question": "How do you make strawberry ice cream with chocolate chips?"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_fallback"] is True
    assert "couldn't find enough information" in data["answer"].lower()


def test_query_isolation_between_users(client, user2_headers):
    """User 2 cannot query facts from User 1's document."""
    res = client.post(
        "/query",
        headers=user2_headers,
        json={"question": "What is the budget for Project Titan launched by Acme Corporation?"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_fallback"] is True
    assert data["citations"] == []
