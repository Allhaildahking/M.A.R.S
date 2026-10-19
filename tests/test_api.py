from fastapi.testclient import TestClient

from mars.api import create_app
from mars.core import Mars
from mars.providers import EchoProvider


def make_client() -> TestClient:
    return TestClient(
        create_app(
            mars=Mars(provider=EchoProvider()),
            api_token="test-token",
        )
    )


def test_health_is_available_without_authentication() -> None:
    response = make_client().get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "mars-api"}


def test_chat_requires_bearer_token() -> None:
    response = make_client().post("/v1/chat", json={"message": "Hello MARS"})

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_chat_returns_model_response_with_valid_token() -> None:
    response = make_client().post(
        "/v1/chat",
        json={"message": "Hello MARS", "conversation_id": "test-session"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "MARS received: Hello MARS",
        "conversation_id": "test-session",
    }


def test_chat_rejects_blank_message() -> None:
    response = make_client().post(
        "/v1/chat",
        json={"message": "   "},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 422
