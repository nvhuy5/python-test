import pytest
from httpx import AsyncClient
from asgi_lifespan import LifespanManager
from fastapi.testclient import TestClient
from fastapi_celery.main import app

client = TestClient(app)

def test_healthcheck_endpoint():
    response = client.get("/fastapi/healthz")
    assert response.status_code == 200
    # Adjust to actual response
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_lifespan_startup_event():
    with TestClient(app) as client:
        # Verify startup logic executed
        assert app.state.startup_triggered is True

        # Check healthcheck endpoint
        response = client.get("/fastapi/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
