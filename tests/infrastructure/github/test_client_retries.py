import time
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from triagit.infrastructure.github.client import GitHubClient
from triagit.infrastructure.github.config import GitHubConfig
from triagit.infrastructure.github.exceptions import (
    GitHubForbiddenError,
    GitHubNotFoundError,
    GitHubRateLimitError,
    GitHubServerError,
    GitHubTransportError,
    GitHubUnauthorizedError,
)


def make_config(**overrides) -> GitHubConfig:
    defaults = dict(
        token="test-token",
        retry_max_attempts=3,
        retry_rate_limit_threshold_seconds=60,
        retry_backoff_base_seconds=0.0,  # instant sleeps in tests
    )
    return GitHubConfig(**{**defaults, **overrides})


def make_response(
    status_code: int,
    json_data: dict | None = None,
    headers: dict | None = None,
) -> httpx.Response:
    return httpx.Response(
        status_code=status_code,
        headers=headers or {},
        json=json_data or ({"message": "error"} if status_code >= 400 else {}),
    )


def make_client(config: GitHubConfig, responses: list) -> GitHubClient:
    client = GitHubClient(config)
    mock_http = AsyncMock()
    mock_http.get.side_effect = responses
    client._client = mock_http
    return client


# --- 5xx retry tests ---

async def test_retries_on_5xx_and_succeeds():
    config = make_config()
    client = make_client(config, [
        make_response(500),
        make_response(200, {"id": 1}),
    ])
    with patch("asyncio.sleep"):
        result = await client._get("/repos/owner/repo")
    assert result == {"id": 1}
    assert client._client.get.call_count == 2


async def test_raises_after_exhausting_5xx_retries():
    config = make_config()
    client = make_client(config, [
        make_response(500),
        make_response(500),
        make_response(500),
    ])
    with patch("asyncio.sleep"):
        with pytest.raises(GitHubServerError):
            await client._get("/repos/owner/repo")
    assert client._client.get.call_count == 3


# --- Transport error retry tests ---

async def test_retries_on_transport_error_and_succeeds():
    config = make_config()
    client = make_client(config, [
        httpx.ConnectError("connection refused"),
        make_response(200, {"id": 1}),
    ])
    with patch("asyncio.sleep"):
        result = await client._get("/repos/owner/repo")
    assert result == {"id": 1}
    assert client._client.get.call_count == 2


async def test_raises_after_exhausting_transport_retries():
    config = make_config()
    client = make_client(config, [
        httpx.ConnectError("connection refused"),
        httpx.ConnectError("connection refused"),
        httpx.ConnectError("connection refused"),
    ])
    with patch("asyncio.sleep"):
        with pytest.raises(GitHubTransportError):
            await client._get("/repos/owner/repo")
    assert client._client.get.call_count == 3


# --- Rate limit (403) retry tests ---

async def test_retries_when_rate_limit_reset_within_threshold():
    config = make_config()
    future_reset = str(int(time.time()) + 30)  # 30s away, within 60s threshold
    client = make_client(config, [
        make_response(403, headers={
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": future_reset,
        }),
        make_response(200, {"id": 1}),
    ])
    with patch("asyncio.sleep") as mock_sleep:
        result = await client._get("/repos/owner/repo")
    assert result == {"id": 1}
    mock_sleep.assert_called_once()
    slept = mock_sleep.call_args[0][0]
    assert 29 <= slept <= 32  # ~30s + 1s buffer


async def test_raises_immediately_when_rate_limit_reset_beyond_threshold():
    config = make_config(retry_rate_limit_threshold_seconds=60)
    future_reset = str(int(time.time()) + 120)  # 120s away, beyond threshold
    client = make_client(config, [
        make_response(403, headers={
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": future_reset,
        }),
    ])
    with patch("asyncio.sleep") as mock_sleep:
        with pytest.raises(GitHubRateLimitError):
            await client._get("/repos/owner/repo")
    mock_sleep.assert_not_called()
    assert client._client.get.call_count == 1


# --- 429 retry tests ---

async def test_retries_on_429_when_retry_after_within_threshold():
    config = make_config()
    client = make_client(config, [
        make_response(429, headers={"Retry-After": "30"}),
        make_response(200, {"id": 1}),
    ])
    with patch("asyncio.sleep") as mock_sleep:
        result = await client._get("/repos/owner/repo")
    assert result == {"id": 1}
    mock_sleep.assert_called_once_with(30)


async def test_raises_immediately_on_429_when_retry_after_exceeds_threshold():
    config = make_config(retry_rate_limit_threshold_seconds=60)
    client = make_client(config, [
        make_response(429, headers={"Retry-After": "120"}),
    ])
    with patch("asyncio.sleep") as mock_sleep:
        with pytest.raises(GitHubRateLimitError):
            await client._get("/repos/owner/repo")
    mock_sleep.assert_not_called()
    assert client._client.get.call_count == 1


# --- Non-retriable error tests ---

async def test_does_not_retry_on_404():
    config = make_config()
    client = make_client(config, [make_response(404)])
    with patch("asyncio.sleep") as mock_sleep:
        with pytest.raises(GitHubNotFoundError):
            await client._get("/repos/owner/repo")
    mock_sleep.assert_not_called()
    assert client._client.get.call_count == 1


async def test_does_not_retry_on_401():
    config = make_config()
    client = make_client(config, [make_response(401)])
    with patch("asyncio.sleep") as mock_sleep:
        with pytest.raises(GitHubUnauthorizedError):
            await client._get("/repos/owner/repo")
    mock_sleep.assert_not_called()
    assert client._client.get.call_count == 1


async def test_does_not_retry_on_403_forbidden():
    config = make_config()
    client = make_client(config, [make_response(403)])
    with patch("asyncio.sleep") as mock_sleep:
        with pytest.raises(GitHubForbiddenError):
            await client._get("/repos/owner/repo")
    mock_sleep.assert_not_called()
    assert client._client.get.call_count == 1
