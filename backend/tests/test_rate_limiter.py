import asyncio

import pytest
from fastapi import Request
from fastapi.responses import JSONResponse

import main


def _request(
    *,
    method: str = "GET",
    client: str = "203.0.113.10",
    forwarded_for: str | None = None,
) -> Request:
    headers = []
    if forwarded_for is not None:
        headers.append((b"x-forwarded-for", forwarded_for.encode()))
    return Request(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": method,
            "scheme": "https",
            "path": "/api/demo",
            "raw_path": b"/api/demo",
            "query_string": b"",
            "root_path": "",
            "headers": headers,
            "client": (client, 1234),
            "server": ("testserver", 443),
        }
    )


def test_limiter_expires_requests_and_reports_retry_after() -> None:
    limiter = main.InMemoryRateLimiter(window_seconds=60, max_buckets=10)
    bucket = ("write", "203.0.113.10")

    assert limiter.check(bucket, 2, now=0) is None
    assert limiter.check(bucket, 2, now=1) is None
    assert limiter.check(bucket, 2, now=2) == 58
    assert limiter.check(bucket, 2, now=60) is None


def test_blocked_requests_do_not_grow_client_history() -> None:
    limiter = main.InMemoryRateLimiter(window_seconds=60, max_buckets=10)
    bucket = ("write", "203.0.113.10")

    assert limiter.check(bucket, 1, now=0) is None
    for timestamp in range(1, 10):
        assert limiter.check(bucket, 1, now=timestamp) is not None

    assert len(limiter._requests[bucket]) == 1


def test_limiter_evicts_least_recently_used_bucket() -> None:
    limiter = main.InMemoryRateLimiter(window_seconds=60, max_buckets=2)
    first = ("read", "203.0.113.1")
    second = ("read", "203.0.113.2")
    third = ("read", "203.0.113.3")

    limiter.check(first, 60, now=0)
    limiter.check(second, 60, now=0)
    limiter.check(first, 60, now=1)
    limiter.check(third, 60, now=1)

    assert limiter.tracked_buckets == 2
    assert first in limiter._requests
    assert second not in limiter._requests
    assert third in limiter._requests


def test_untrusted_peer_cannot_spoof_forwarded_identity() -> None:
    resolved = main._resolve_client_ip(
        "203.0.113.10",
        "198.51.100.99",
        main._parse_trusted_proxy_networks("10.0.0.0/8"),
    )

    assert resolved == "203.0.113.10"


def test_trusted_proxy_chain_uses_nearest_untrusted_address() -> None:
    resolved = main._resolve_client_ip(
        "10.0.0.3",
        "192.0.2.50, 198.51.100.4, 10.0.0.2",
        main._parse_trusted_proxy_networks("10.0.0.0/8"),
    )

    assert resolved == "198.51.100.4"


@pytest.mark.parametrize("forwarded_for", [None, "", "invalid, 192.0.2.1"])
def test_missing_or_invalid_forwarded_chain_falls_back_to_direct_peer(
    forwarded_for: str | None,
) -> None:
    resolved = main._resolve_client_ip(
        "10.0.0.3",
        forwarded_for,
        main._parse_trusted_proxy_networks("10.0.0.0/8"),
    )

    assert resolved == "10.0.0.3"


def test_middleware_returns_retry_after_without_mixing_read_and_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    limiter = main.InMemoryRateLimiter(window_seconds=60, max_buckets=10)
    monkeypatch.setattr(main, "_RATE_LIMITER", limiter)

    async def call_next(_request):
        return JSONResponse({"ok": True})

    for _ in range(main._UPLOAD_LIMIT):
        response = asyncio.run(
            main.rate_limit_middleware(_request(method="POST"), call_next)
        )
        assert response.status_code == 200

    blocked = asyncio.run(
        main.rate_limit_middleware(_request(method="POST"), call_next)
    )
    read = asyncio.run(main.rate_limit_middleware(_request(method="GET"), call_next))

    assert blocked.status_code == 429
    assert blocked.headers["retry-after"] == "60"
    assert read.status_code == 200
