
import base64
import json
from unittest.mock import AsyncMock

import pytest

from github_mcp import server


@pytest.fixture
def mock_github(monkeypatch):
    mock_get = AsyncMock()
    monkeypatch.setattr(server.github, "get", mock_get)
    return mock_get


# RESOURCE TESTS


@pytest.mark.asyncio
async def test_repository_details_resource(mock_github):
    mock_github.return_value = {
        "full_name": "user/test-repo",
        "description": "Test repository",
        "stargazers_count": 100,
        "forks_count": 20,
        "language": "Python",
        "html_url": "https://github.com/user/test-repo"
    }

    result = await server.repository_details(
        "user",
        "test-repo"
    )

    details = json.loads(result)

    assert details["name"] == "user/test-repo"
    assert details["description"] == "Test repository"
    assert details["stars"] == 100
    assert details["forks"] == 20
    assert details["language"] == "Python"

    mock_github.assert_awaited_once_with(
        "/repos/user/test-repo"
    )


@pytest.mark.asyncio
async def test_repository_readme_resource(mock_github):
    readme_text = "# Test Repository\nThis is a README."

    encoded_content = base64.b64encode(
        readme_text.encode("utf-8")
    ).decode("utf-8")

    mock_github.return_value = {
        "content": encoded_content
    }

    result = await server.repository_readme(
        "user",
        "test-repo"
    )

    assert result == readme_text

    mock_github.assert_awaited_once_with(
        "/repos/user/test-repo/readme"
    )


@pytest.mark.asyncio
async def test_repository_readme_truncation(mock_github, monkeypatch):
    readme_text = "A" * 100

    encoded_content = base64.b64encode(
        readme_text.encode("utf-8")
    ).decode("utf-8")

    mock_github.return_value = {
        "content": encoded_content
    }

    monkeypatch.setattr(
        server,
        "MAX_README_CHARS",
        20
    )

    result = await server.repository_readme(
        "user",
        "test-repo"
    )

    assert result.startswith("A" * 20)
    assert "README truncated" in result


# PROMPT TESTS


def test_analyze_repository_prompt():
    result = server.analyze_repository(
        "user",
        "test-repo"
    )

    assert "user/test-repo" in result
    assert "Project overview and purpose" in result
    assert "Main programming languages" in result
    assert "structured technical report" in result


def test_review_repository_prompt():
    result = server.review_repository(
        "user",
        "test-repo"
    )

    assert "user/test-repo" in result
    assert "Code quality and readability" in result
    assert "Security vulnerabilities" in result
    assert "prioritized review report" in result


# INPUT VALIDATION TESTS


@pytest.mark.asyncio
async def test_resource_invalid_repository(mock_github):
    with pytest.raises(
        ValueError,
        match="Owner and repository are required"
    ):
        await server.repository_details(
            "",
            "test-repo"
        )

    mock_github.assert_not_awaited()


def test_prompts_reject_invalid_repository():
    with pytest.raises(ValueError):
        server.analyze_repository("", "test-repo")

    with pytest.raises(ValueError):
        server.review_repository("user", "")
