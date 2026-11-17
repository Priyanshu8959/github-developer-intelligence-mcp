
import base64
from unittest.mock import AsyncMock

import pytest

from github_mcp import server


@pytest.fixture
def mock_github(monkeypatch):
    mock_get = AsyncMock()
    monkeypatch.setattr(server.github, "get", mock_get)
    return mock_get


@pytest.mark.asyncio
async def test_search_repositories(mock_github):
    mock_github.return_value = {
        "total_count": 1,
        "items": [
            {
                "full_name": "user/test-repo",
                "description": "Test repository",
                "stargazers_count": 100,
                "language": "Python",
                "html_url": "https://github.com/user/test-repo"
            }
        ]
    }

    result = await server.search_repositories(
        "python",
        limit=5,
        page=2
    )

    assert result["query"] == "python"
    assert result["total_count"] == 1
    assert result["repositories_returned"] == 1
    assert result["repositories"][0]["name"] == "user/test-repo"

    mock_github.assert_awaited_once_with(
        "/search/repositories",
        params={
            "q": "python",
            "per_page": 5,
            "page": 2,
            "sort": "stars",
            "order": "desc"
        }
    )


@pytest.mark.asyncio
async def test_get_repo_details(mock_github):
    mock_github.return_value = {
        "full_name": "user/test-repo",
        "description": "A test project",
        "stargazers_count": 50,
        "forks_count": 10,
        "open_issues_count": 2,
        "language": "Python",
        "default_branch": "main",
        "created_at": "2025-01-01",
        "updated_at": "2025-02-01",
        "html_url": "https://github.com/user/test-repo"
    }

    result = await server.get_repo_details(
        "user",
        "test-repo"
    )

    assert result["name"] == "user/test-repo"
    assert result["stars"] == 50
    assert result["forks"] == 10
    assert result["language"] == "Python"

    mock_github.assert_awaited_once_with(
        "/repos/user/test-repo"
    )


@pytest.mark.asyncio
async def test_get_repository_languages(mock_github):
    mock_github.return_value = {
        "Python": 750,
        "JavaScript": 250
    }

    result = await server.get_repository_languages(
        "user",
        "test-repo"
    )

    assert result["total_bytes"] == 1000
    assert result["languages"][0]["language"] == "Python"
    assert result["languages"][0]["percentage"] == 75.0
    assert result["languages"][1]["percentage"] == 25.0


@pytest.mark.asyncio
async def test_get_repository_languages_empty(mock_github):
    mock_github.return_value = {}

    result = await server.get_repository_languages(
        "user",
        "test-repo"
    )

    assert result["total_bytes"] == 0
    assert result["languages"] == []


@pytest.mark.asyncio
async def test_get_commit_history(mock_github):
    mock_github.return_value = [
        {
            "sha": "abc123",
            "commit": {
                "message": "Initial commit",
                "author": {
                    "name": "Test User",
                    "date": "2025-01-01T10:00:00Z"
                }
            },
            "html_url": "https://github.com/user/test-repo/commit/abc123"
        }
    ]

    result = await server.get_commit_history(
        "user",
        "test-repo",
        limit=5,
        page=1
    )

    assert result["total_commits_returned"] == 1
    assert result["commits"][0]["sha"] == "abc123"
    assert result["commits"][0]["message"] == "Initial commit"
    assert result["commits"][0]["author"] == "Test User"

    mock_github.assert_awaited_once_with(
        "/repos/user/test-repo/commits",
        params={"page": 1, "per_page": 5}
    )


@pytest.mark.asyncio
async def test_get_contributors(mock_github):
    mock_github.return_value = [
        {
            "login": "test-user",
            "contributions": 25,
            "html_url": "https://github.com/test-user",
            "avatar_url": "https://example.com/avatar.png"
        }
    ]

    result = await server.get_contributors(
        "user",
        "test-repo"
    )

    assert result["total_contributors_returned"] == 1
    assert result["contributors"][0]["username"] == "test-user"
    assert result["contributors"][0]["contributions"] == 25


@pytest.mark.asyncio
async def test_get_readme(mock_github):
    readme_text = "# Test Repository\nThis is a test README."

    encoded_content = base64.b64encode(
        readme_text.encode("utf-8")
    ).decode("utf-8")

    mock_github.return_value = {
        "name": "README.md",
        "content": encoded_content
    }

    result = await server.get_readme(
        "user",
        "test-repo"
    )

    assert result["filename"] == "README.md"
    assert result["content"] == readme_text
    assert result["truncated"] is False
    assert result["original_characters"] == len(readme_text)


@pytest.mark.asyncio
async def test_get_readme_truncation(mock_github, monkeypatch):
    readme_text = "A" * 100

    encoded_content = base64.b64encode(
        readme_text.encode("utf-8")
    ).decode("utf-8")

    mock_github.return_value = {
        "name": "README.md",
        "content": encoded_content
    }

    monkeypatch.setattr(server, "MAX_README_CHARS", 20)

    result = await server.get_readme(
        "user",
        "test-repo"
    )

    assert result["truncated"] is True
    assert result["original_characters"] == 100
    assert result["max_characters"] == 20
    assert result["content"].startswith("A" * 20)
    assert "README truncated" in result["content"]


@pytest.mark.asyncio
async def test_search_code(mock_github):
    mock_github.return_value = {
        "total_count": 1,
        "items": [
            {
                "repository": {
                    "full_name": "user/test-repo"
                },
                "name": "main.py",
                "path": "src/main.py",
                "html_url": "https://github.com/user/test-repo/blob/main/src/main.py"
            }
        ]
    }

    result = await server.search_code(
        "FastAPI",
        limit=5,
        page=1
    )

    assert result["total_count"] == 1
    assert result["results_returned"] == 1
    assert result["results"][0]["repository"] == "user/test-repo"
    assert result["results"][0]["filename"] == "main.py"
    assert result["results"][0]["path"] == "src/main.py"


@pytest.mark.asyncio
async def test_invalid_repository_does_not_call_github(mock_github):
    with pytest.raises(ValueError, match="Owner and repository are required"):
        await server.get_repo_details("", "test-repo")

    mock_github.assert_not_awaited()
