import pytest
from httpx import AsyncClient
from app.main import app
from app.services.vimeo_client import VimeoClient
from unittest.mock import AsyncMock

@pytest.fixture
def mock_vimeo_client():
    client = AsyncMock(spec=VimeoClient)
    return client

@pytest.fixture
async def client(mock_vimeo_client):
    # Override the dependency
    app.dependency_overrides[VimeoClient] = lambda: mock_vimeo_client
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides = {}
