
import pytest

from github_mcp.server import (
    validate_repository,
    validate_pagination,
    validate_search_query,
)


# Test repository validation

def test_validate_repository_valid_input():
    owner, repo = validate_repository(" facebook ", " react ")

    assert owner == "facebook"
    assert repo == "react"


@pytest.mark.parametrize(
    "owner, repo",
    [
        ("", "react"),
        ("facebook", ""),
        ("   ", "react"),
        ("facebook", "   "),
        ("face/book", "react"),
        ("facebook", "react/name"),
        ("facebook", "react?"),
        ("facebook", "react#"),
        ("face book", "react"),
    ],
)
def test_validate_repository_invalid_input(owner, repo):
    with pytest.raises(ValueError):
        validate_repository(owner, repo)


# Test pagination validation

@pytest.mark.parametrize(
    "limit, page",
    [
        (1, 1),
        (5, 2),
        (30, 1),
    ],
)
def test_validate_pagination_valid_input(limit, page):
    validate_pagination(limit, page)


@pytest.mark.parametrize(
    "limit, page",
    [
        (0, 1),
        (31, 1),
        (5, 0),
        (-1, 1),
    ],
)
def test_validate_pagination_invalid_input(limit, page):
    with pytest.raises(ValueError):
        validate_pagination(limit, page)


# Test search query validation

def test_validate_search_query_valid_input():
    query = validate_search_query("  python machine learning  ")

    assert query == "python machine learning"


def test_validate_search_query_maximum_length():
    query = "a" * 256

    assert validate_search_query(query) == query


@pytest.mark.parametrize(
    "query",
    [
        "",
        "   ",
        "a" * 257,
    ],
)
def test_validate_search_query_invalid_input(query):
    with pytest.raises(ValueError):
        validate_search_query(query)
