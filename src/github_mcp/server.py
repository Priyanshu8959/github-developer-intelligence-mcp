
import base64
import json

from mcp.server.fastmcp import FastMCP

from .github_client import GitHubClient

mcp = FastMCP("GitHub Developer Intelligence")
github = GitHubClient()

# Maximum README text returned to an MCP client (about 5,000 tokens, depending on content).
MAX_README_CHARS = 20_000


def limit_text(content: str, max_chars: int):
    """Limit text size and report whether truncation was necessary."""

    was_truncated = len(content) > max_chars
    return content[:max_chars], was_truncated


## Utility functions for validation 
def validate_repository(owner: str, repo: str):
    """Validate GitHub repository owner and name."""

    owner = owner.strip()
    repo = repo.strip()

    if not owner or not repo:
        raise ValueError("Owner and repository are required")

    invalid_chars = ["/", "\\", "?", "#", " "]

    if any(char in owner or char in repo for char in invalid_chars):
        raise ValueError("Invalid owner or repository name")

    return owner, repo


def validate_pagination(limit: int, page: int):
    """Validate pagination parameters."""

    if not 1 <= limit <= 30:
        raise ValueError("Limit must be between 1 and 30")

    if page < 1:
        raise ValueError("Page must be at least 1")


def validate_search_query(query: str):
    """Validate GitHub search query."""

    query = query.strip()

    if not query:
        raise ValueError("Search query cannot be empty")

    if len(query) > 256:
        raise ValueError("Search query cannot exceed 256 characters")

    return query


@mcp.tool()
async def search_repositories(
    query: str,
    limit: int = 5,
    page: int = 1
) -> dict:
    """
    Search GitHub repositories by keywords.

    Returns repository names, descriptions,
    stars, languages and URLs.
    """

    query = validate_search_query(query)
    validate_pagination(limit, page)

    data = await github.get(
        "/search/repositories",
        params={
            "q": query,
            "per_page": limit,
            "page": page,
            "sort": "stars",
            "order": "desc"
        }
    )

    repositories = []

    for repo in data["items"]:
        repositories.append({
            "name": repo["full_name"],
            "description": repo["description"],
            "stars": repo["stargazers_count"],
            "language": repo["language"],
            "url": repo["html_url"]
        })

    return {
        "query": query,
        "page": page,
        "per_page": limit,
        "total_count": data["total_count"],
        "repositories_returned": len(repositories),
        "repositories": repositories
    }

# TOOL 2: Get repository details


@mcp.tool()
async def get_repo_details(owner: str, repo: str) -> dict:
    """
    Get detailed information about a GitHub repository.
    """

    owner, repo = validate_repository(owner, repo)

    data = await github.get(f"/repos/{owner}/{repo}")

    return {
        "name": data["full_name"],
        "description": data["description"],
        "stars": data["stargazers_count"],
        "forks": data["forks_count"],
        "open_issues": data["open_issues_count"],
        "language": data["language"],
        "default_branch": data["default_branch"],
        "created_at": data["created_at"],
        "updated_at": data["updated_at"],
        "url": data["html_url"]
    }


# Tool 3: Get repository languages

@mcp.tool()
async def get_repository_languages(
    owner: str,
    repo: str
) -> dict:
    """
    Get programming languages used in a GitHub repository
    with their code distribution percentages.
    """

    owner, repo = validate_repository(owner, repo)

    data = await github.get(
        f"/repos/{owner}/{repo}/languages"
    )

    total_bytes = sum(data.values())

    if total_bytes == 0:
        return {
            "repository": f"{owner}/{repo}",
            "total_bytes": 0,
            "languages": []
        }

    languages = []

    for language, size in data.items():
        percentage = (size / total_bytes) * 100

        languages.append({
            "language": language,
            "bytes": size,
            "percentage": round(percentage, 2)
        })

    return {
        "repository": f"{owner}/{repo}",
        "total_bytes": total_bytes,
        "languages": languages
    }


# Tool 4: Get commit history

@mcp.tool()
async def get_commit_history(
    owner: str,
    repo: str,
    limit: int = 5,
    page: int = 1
) -> dict:
    """
    Get the latest commits from a GitHub repository.
    """

    owner, repo = validate_repository(owner, repo)

    validate_pagination(limit, page)

    data = await github.get(
        f"/repos/{owner}/{repo}/commits",
        params={
            "page": page,
            "per_page": limit
        }
    )

    commits = []

    for item in data:
        commits.append({
            "sha": item["sha"],
            "message": item["commit"]["message"],
            "author": item["commit"]["author"]["name"],
            "date": item["commit"]["author"]["date"],
            "url": item["html_url"]
        })

    return {
        "repository": f"{owner}/{repo}",
        "total_commits_returned": len(commits),
        "commits": commits,
        "page": page,
        "per_page": limit
    }


# Tool 5: Get contributors


@mcp.tool()
async def get_contributors(
    owner: str,
    repo: str,
    limit: int = 10,
    page: int = 1
) -> dict:
    """
    Get contributors of a GitHub repository.
    """

    owner, repo = validate_repository(owner, repo)

    validate_pagination(limit, page)

    data = await github.get(
        f"/repos/{owner}/{repo}/contributors",
        params={
            "per_page": limit,
            "page": page
        }
    )

    contributors = []

    for item in data:
        contributors.append({
            "username": item["login"],
            "contributions": item["contributions"],
            "profile_url": item["html_url"],
            "avatar_url": item["avatar_url"]
        })

    return {
        "repository": f"{owner}/{repo}",
        "page": page,
        "per_page": limit,
        "total_contributors_returned": len(contributors),
        "contributors": contributors
    }

# Tool 6: Get README

@mcp.tool()
async def get_readme(
    owner: str,
    repo: str
) -> dict:
    """
    Fetch and decode the README of a GitHub repository.
    """

    owner, repo = validate_repository(owner, repo)

    data = await github.get(
        f"/repos/{owner}/{repo}/readme"
    )

    readme_content = base64.b64decode(
        data["content"]
    ).decode("utf-8", errors="replace")

    original_characters = len(readme_content)
    readme_content, was_truncated = limit_text(
        readme_content,
        MAX_README_CHARS
    )

    if was_truncated:
        readme_content += (
            "\n\n[README truncated: showing the first "
            f"{MAX_README_CHARS:,} characters. "
            "Use the repository's GitHub page to read the complete file.]"
        )

    return {
        "repository": f"{owner}/{repo}",
        "filename": data["name"],
        "content": readme_content,
        "truncated": was_truncated,
        "original_characters": original_characters,
        "max_characters": MAX_README_CHARS
    }


# Tool 7: Search code


@mcp.tool()
async def search_code(
    query: str,
    limit: int = 5,
    page: int = 1
) -> dict:
    """
    Search code on GitHub using keywords.
    """

    query = validate_search_query(query)
    validate_pagination(limit, page)

    data = await github.get(
        "/search/code",
        params={
            "q": query,
            "per_page": limit,
            "page": page
        }
    )

    results = []

    for item in data["items"]:
        results.append({
            "repository": item["repository"]["full_name"],
            "filename": item["name"],
            "path": item["path"],
            "url": item["html_url"]
        })

    return {
        "query": query,
        "page": page,
        "per_page": limit,
        "total_count": data["total_count"],
        "results_returned": len(results),
        "results": results
    }

# MCP Resource: GitHub Repository Details

@mcp.resource("github://repository/{owner}/{repo}/details")
async def repository_details(owner: str, repo: str) -> str:
    """
    Expose GitHub repository details as an MCP resource.
    """

    owner, repo = validate_repository(owner, repo)

    data = await github.get(
        f"/repos/{owner}/{repo}"
    )

    details = {
        "name": data["full_name"],
        "description": data["description"],
        "stars": data["stargazers_count"],
        "forks": data["forks_count"],
        "language": data["language"],
        "url": data["html_url"]
    }

    return json.dumps(details, indent=2)


# MCP Resource: GitHub Repository README

@mcp.resource("github://repository/{owner}/{repo}/readme")
async def repository_readme(owner: str, repo: str) -> str:
    """
    Expose repository README as an MCP resource.
    """

    owner, repo = validate_repository(owner, repo)

    data = await github.get(
        f"/repos/{owner}/{repo}/readme"
    )

    content = base64.b64decode(
        data["content"]
    ).decode("utf-8", errors="replace")

    content, was_truncated = limit_text(
        content,
        MAX_README_CHARS
    )

    if was_truncated:
        content += (
            "\n\n[README truncated: showing the first "
            f"{MAX_README_CHARS:,} characters. "
            "Use the repository's GitHub page to read the complete file.]"
        )

    return content

# MCP Prompt: Analyze GitHub Repository

@mcp.prompt()
def analyze_repository(owner: str, repo: str) -> str:
    """
    Generate instructions to analyse a GitHub repository.
    """

    owner, repo = validate_repository(owner, repo)

    return f"""
    Analyse the GitHub repository: {owner}/{repo}

    Focus on the following areas:

    1. Project overview and purpose.
    2. Main programming languages and technologies.
    3. Repository structure and important files.
    4. Main features and functionality.
    5. Dependencies and architecture.
    6. Code quality and maintainability.
    7. Potential improvements.

    Provide a structured technical report.
    Explain technical concepts clearly.
    Do not assume information that is not available.
    """


# MCP Prompt: Review GitHub Repository

@mcp.prompt()
def review_repository(owner: str, repo: str) -> str:
    """
    Generate instructions for reviewing a GitHub repository.
    """

    owner, repo = validate_repository(owner, repo)

    return f"""
    Perform a technical code review of the GitHub repository:
    {owner}/{repo}

    Review the project from a senior software engineer's perspective.

    Focus on:

    1. Code quality and readability.
    2. Potential bugs and logical errors.
    3. Security vulnerabilities.
    4. Performance bottlenecks.
    5. Error handling and edge cases.
    6. Code organization and maintainability.
    7. Best practices and design patterns.

    For every issue found:
    - Explain the problem.
    - Identify the affected file or code location.
    - Explain its impact.
    - Suggest a practical improvement.

    Do not invent issues.
    Clearly distinguish confirmed issues from recommendations.
    Provide a prioritized review report.
    """


if __name__ == "__main__":
    mcp.run(transport="stdio")
