
import httpx
import logging
from datetime import datetime, timezone

from .config import GITHUB_TOKEN, GITHUB_BASE_URL


logger = logging.getLogger(__name__)


class GitHubAPIError(Exception):
    """Custom exception for GitHub API failures."""


class GitHubClient:

    def __init__(self):
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10"
        }

        if GITHUB_TOKEN:
            self.headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    async def get(self, endpoint, params=None):

        try:
            async with httpx.AsyncClient(
                base_url=GITHUB_BASE_URL,
                headers=self.headers,
                timeout=15.0
            ) as client:

                logger.info("GitHub API request: %s", endpoint)

                response = await client.get(
                    endpoint,
                    params=params
                )

                response.raise_for_status()

                logger.info(
                    "GitHub API response: %s",
                    response.status_code
                )

                return response.json()

        except httpx.HTTPStatusError as error:

            response = error.response
            status = response.status_code

            try:
                github_message = response.json().get("message", "")
            except ValueError:
                github_message = ""

            retry_after = response.headers.get("Retry-After")

            logger.error("GitHub API request failed: %s", status)

            reset_timestamp = response.headers.get(
                "X-RateLimit-Reset"
            )

            wait_seconds = 0

            if reset_timestamp:
                try:
                    reset_time = datetime.fromtimestamp(
                        int(reset_timestamp),
                        tz=timezone.utc
                    )

                    current_time = datetime.now(timezone.utc)

                    wait_seconds = max(
                        0,
                        int((reset_time - current_time).total_seconds())
                    )

                    logger.info(
                        "GitHub rate limit resets at: %s",
                        reset_time
                    )

                except (ValueError, OSError, OverflowError):
                    logger.warning(
                        "Invalid GitHub rate limit reset timestamp"
                    )

            if status == 401:
                message = "GitHub authentication failed. Check your token."

            elif status == 403:

                if response.headers.get("X-RateLimit-Remaining") == "0":

                    if wait_seconds > 0:
                        message = (
                            f"GitHub API primary rate limit exceeded. "
                            f"Try again in {wait_seconds} seconds."
                        )
                    else:
                        message = "GitHub API primary rate limit exceeded."

                elif (
                    "secondary rate limit" in github_message.lower()
                    or "abuse detection" in github_message.lower()
                ):

                    if retry_after:
                        message = (
                            f"GitHub secondary rate limit exceeded. "
                            f"Retry after {retry_after} seconds."
                        )
                    else:
                        message = (
                            "GitHub secondary rate limit exceeded. "
                            "Wait at least 1 minute before retrying."
                        )

                else:
                    message = "Access forbidden. Check your permissions."

            elif status == 404:
                message = "GitHub repository or resource not found."

            elif status == 422:
                message = (
                    "GitHub rejected the request. "
                    "Check your query or parameters."
                )

            elif status == 429:

                if retry_after:
                    message = (
                        f"GitHub API rate limit exceeded. "
                        f"Please retry after {retry_after} seconds."
                    )
                else:
                    message = (
                        "GitHub API rate limit exceeded. "
                        "Please try again later."
                    )

            elif status >= 500:
                message = "GitHub server error. Please try again later."

            else:
                message = f"GitHub API request failed with status {status}."

            raise GitHubAPIError(message) from error

        except httpx.TimeoutException as error:
            logger.error("GitHub API request timed out")
            raise GitHubAPIError(
                "GitHub API request timed out."
            ) from error

        except httpx.RequestError as error:
            logger.error("GitHub network connection failed")
            raise GitHubAPIError(
                "Unable to connect to GitHub API. Check your network."
            ) from error

        except ValueError as error:
            logger.error("GitHub returned an invalid JSON response")
            raise GitHubAPIError(
                "GitHub returned an invalid JSON response."
            ) from error
