"""Integration tests for the chat API endpoint."""
import pytest
import pytest_asyncio


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "model_available" in data


@pytest.mark.asyncio
async def test_public_config(client):
    response = await client.get("/api/v1/config")
    assert response.status_code == 200
    data = response.json()
    assert "model_provider" in data
    assert "features" in data
    # Secrets must not be present
    assert "ADMIN_PASSWORD" not in str(data)
    assert "SECRET_KEY" not in str(data)


@pytest.mark.asyncio
async def test_chat_abstains_on_empty_index(client):
    """When no documents are indexed, the assistant must abstain."""
    response = await client.post("/api/v1/chat", json={
        "question": "What is the fee for BTech first year?",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["abstained"] is True
    assert data["citations"] == []
    assert "conversation_id" in data
    assert "request_id" in data


@pytest.mark.asyncio
async def test_chat_validates_question_length(client):
    response = await client.post("/api/v1/chat", json={
        "question": "",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_returns_required_fields(client):
    response = await client.post("/api/v1/chat", json={
        "question": "Tell me about registration procedures.",
    })
    assert response.status_code == 200
    data = response.json()
    required = {"request_id", "conversation_id", "answer", "abstained", "citations", "processing_time_ms"}
    assert required.issubset(data.keys())


@pytest.mark.asyncio
async def test_documents_list_unauthenticated(client):
    response = await client.get("/api/v1/documents")
    assert response.status_code == 200  # listing is public


@pytest.mark.asyncio
async def test_documents_upload_requires_auth(client):
    import io
    response = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", io.BytesIO(b"Hello world"), "text/plain")},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_documents_upload_txt(client, admin_auth):
    import io
    content = b"DEMO: This is a test document about examination procedures. Exams start on 20 November 2026."
    response = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("demo_exam.txt", io.BytesIO(content), "text/plain")},
        data={"category": "exams", "is_demo": "true"},
        headers=admin_auth,
    )
    assert response.status_code == 200
    data = response.json()
    assert "document_id" in data
    assert data["status"] in ("pending", "indexed", "processing")
    return data["document_id"]


@pytest.mark.asyncio
async def test_documents_upload_invalid_type(client, admin_auth):
    import io
    response = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("malware.exe", io.BytesIO(b"MZ fake binary"), "application/octet-stream")},
        headers=admin_auth,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_admin_stats_requires_auth(client):
    response = await client.get("/api/v1/admin/stats")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_stats_with_auth(client, admin_auth):
    response = await client.get("/api/v1/admin/stats", headers=admin_auth)
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "vector_store" in data
