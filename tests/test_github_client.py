
import httpx
import pytest
from unittest.mock import AsyncMock, patch

from github_mcp.github_client import GitHubClient, GitHubAPIError


@pytest.fixture
def github_client():
    return GitHubClient()


@pytest.mark.asyncio
async def test_successful_get_request(github_client):
    mock_response = httpx.Response(
        200,
        json={"name": "test-repo"},
        request=httpx.Request("GET", "https://api.github.com/repos/test/test-repo")
    )

    with patch("github_mcp.github_client.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value.__aenter__.return_value
        mock_instance.get = AsyncMock(return_value=mock_response)

        result = await github_client.get("/repos/test/test-repo")

    assert result == {"name": "test-repo"}


@pytest.mark.asyncio
async def test_repository_not_found(github_client):
    mock_response = httpx.Response(
        404,
        json={"message": "Not Found"},
        request=httpx.Request("GET", "https://api.github.com/repos/test/unknown")
    )

    with patch("github_mcp.github_client.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value.__aenter__.return_value
        mock_instance.get = AsyncMock(return_value=mock_response)

        with pytest.raises(GitHubAPIError, match="not found"):
            await github_client.get("/repos/test/unknown")


@pytest.mark.asyncio
async def test_authentication_error(github_client):
    mock_response = httpx.Response(
        401,
        json={"message": "Bad credentials"},
        request=httpx.Request("GET", "https://api.github.com/user")
    )

    with patch("github_mcp.github_client.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value.__aenter__.return_value
        mock_instance.get = AsyncMock(return_value=mock_response)

        with pytest.raises(GitHubAPIError, match="authentication failed"):
            await github_client.get("/user")


@pytest.mark.asyncio
async def test_timeout_error(github_client):
    with patch("github_mcp.github_client.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value.__aenter__.return_value
        mock_instance.get = AsyncMock(
            side_effect=httpx.TimeoutException("Request timed out")
        )

        with pytest.raises(GitHubAPIError, match="timed out"):
            await github_client.get("/repos/test/test-repo")


@pytest.mark.asyncio
async def test_network_error(github_client):
    with patch("github_mcp.github_client.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value.__aenter__.return_value
        mock_instance.get = AsyncMock(
            side_effect=httpx.RequestError("Connection failed")
        )

        with pytest.raises(GitHubAPIError, match="Unable to connect"):
            await github_client.get("/repos/test/test-repo")


@pytest.mark.asyncio
async def test_server_error(github_client):
    mock_response = httpx.Response(
        500,
        json={"message": "Internal Server Error"},
        request=httpx.Request("GET", "https://api.github.com/repos/test/test-repo")
    )

    with patch("github_mcp.github_client.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value.__aenter__.return_value
        mock_instance.get = AsyncMock(return_value=mock_response)

        with pytest.raises(GitHubAPIError, match="server error"):
            await github_client.get("/repos/test/test-repo")


@pytest.mark.asyncio
async def test_invalid_json_response(github_client):
    mock_response = httpx.Response(
        200,
        content=b"Invalid JSON",
        headers={"Content-Type": "application/json"},
        request=httpx.Request("GET", "https://api.github.com/repos/test/test-repo")
    )

    with patch("github_mcp.github_client.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value.__aenter__.return_value
        mock_instance.get = AsyncMock(return_value=mock_response)

        with pytest.raises(GitHubAPIError, match="invalid JSON"):
            await github_client.get("/repos/test/test-repo")
