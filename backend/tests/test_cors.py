import asyncio

from main import app


def _preflight(origin: str) -> tuple[int, dict[str, str]]:
    messages: list[dict] = []
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "OPTIONS",
        "scheme": "https",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "root_path": "",
        "headers": [
            (b"origin", origin.encode()),
            (b"access-control-request-method", b"GET"),
        ],
        "client": ("127.0.0.1", 1234),
        "server": ("testserver", 443),
    }

    async def receive() -> dict:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict) -> None:
        messages.append(message)

    asyncio.run(app(scope, receive, send))
    response_start = next(
        message for message in messages if message["type"] == "http.response.start"
    )
    headers = {
        key.decode("latin-1"): value.decode("latin-1")
        for key, value in response_start["headers"]
    }
    return response_start["status"], headers


def test_cors_allows_modelguard_vercel_preview_origin() -> None:
    origin = "https://modelguard-ai-git-feature-user.vercel.app"

    status, headers = _preflight(origin)

    assert status == 200
    assert headers["access-control-allow-origin"] == origin


def test_cors_rejects_unrelated_lookalike_origin() -> None:
    status, headers = _preflight("https://modelguard-ai.attacker.vercel.app")

    assert status == 400
    assert "access-control-allow-origin" not in headers
