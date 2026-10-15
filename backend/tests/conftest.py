"""Pytest configuration and shared fixtures."""
import asyncio
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_campussaarthi.db")
os.environ.setdefault("DATA_DIR", "./test_data")
os.environ.setdefault("VECTOR_INDEX_PATH", "./test_data/indexes/faiss.index")
os.environ.setdefault("MODEL_PROVIDER", "mock")
os.environ.setdefault("ADMIN_USERNAME", "testadmin")
os.environ.setdefault("ADMIN_PASSWORD", "testpass")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def app():
    from app.main import app as fastapi_app
    from app.core.database import init_db
    await init_db()
    yield fastapi_app
    # Cleanup
    import os, glob
    for f in glob.glob("test_campussaarthi*.db"):
        try:
            os.remove(f)
        except Exception:
            pass


@pytest_asyncio.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def admin_auth():
    """HTTP Basic auth headers for admin tests."""
    import base64
    creds = base64.b64encode(b"testadmin:testpass").decode()
    return {"Authorization": f"Basic {creds}"}
