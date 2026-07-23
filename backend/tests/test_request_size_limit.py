import asyncio

import pytest

from main import (
    MAX_DIFF_REQUEST_BODY_SIZE,
    MAX_REQUEST_BODY_SIZE,
    UPLOAD_BODY_LIMITS,
    RequestSizeLimitMiddleware,
)


def _scope(path: str, content_length: int | None = None) -> dict:
    headers = []
    if content_length is not None:
        headers.append((b"content-length", str(content_length).encode()))
    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "https",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": headers,
        "client": ("127.0.0.1", 1234),
        "server": ("testserver", 443),
    }


async def _consume_body(scope, receive, send) -> None:
    while True:
        message = await receive()
        if not message.get("more_body", False):
            break
    await send({"type": "http.response.start", "status": 204, "headers": []})
    await send({"type": "http.response.body", "body": b""})


def _run(path: str, chunks: list[bytes], content_length: int | None = None):
    sent = []
    pending = list(chunks)
    receive_calls = 0

    async def receive():
        nonlocal receive_calls
        receive_calls += 1
        body = pending.pop(0)
        return {
            "type": "http.request",
            "body": body,
            "more_body": bool(pending),
        }

    async def send(message):
        sent.append(message)

    middleware = RequestSizeLimitMiddleware(
        _consume_body,
        limits_by_path=UPLOAD_BODY_LIMITS,
    )
    asyncio.run(middleware(_scope(path, content_length), receive, send))
    response_start = next(
        message for message in sent if message["type"] == "http.response.start"
    )
    return response_start["status"], receive_calls


@pytest.mark.parametrize("path, limit", sorted(UPLOAD_BODY_LIMITS.items()))
def test_rejects_oversized_content_length_without_reading_body(
    path: str, limit: int,
) -> None:
    status, receive_calls = _run(
        path,
        [b"not read"],
        content_length=limit + 1,
    )

    assert status == 413
    assert receive_calls == 0


@pytest.mark.parametrize("path, limit", sorted(UPLOAD_BODY_LIMITS.items()))
def test_rejects_streamed_body_when_cumulative_bytes_exceed_limit(
    path: str, limit: int,
) -> None:
    status, receive_calls = _run(
        path,
        [b"x" * limit, b"x"],
    )

    assert status == 413
    assert receive_calls == 2


@pytest.mark.parametrize("path, limit", sorted(UPLOAD_BODY_LIMITS.items()))
def test_allows_upload_body_at_exact_limit(path: str, limit: int) -> None:
    status, receive_calls = _run(
        path,
        [b"x" * limit],
        content_length=limit,
    )

    assert status == 204
    assert receive_calls == 1


def test_company_diff_allows_body_above_single_upload_limit() -> None:
    body_size = MAX_REQUEST_BODY_SIZE + 1

    status, receive_calls = _run(
        "/api/company-diff",
        [b"x" * body_size],
        content_length=body_size,
    )

    assert body_size < MAX_DIFF_REQUEST_BODY_SIZE
    assert status == 204
    assert receive_calls == 1


def test_does_not_limit_non_upload_routes() -> None:
    status, receive_calls = _run(
        "/api/other",
        [b"small body"],
        content_length=MAX_REQUEST_BODY_SIZE + 1,
    )

    assert status == 204
    assert receive_calls == 1
