"""
HTTP client for the Bitbucket Cloud REST API v2.

Authenticates using Bitbucket Cloud API tokens via HTTP Basic Auth,
where the username is the Atlassian account email and the password
is the API token.

See: https://support.atlassian.com/bitbucket-cloud/docs/api-tokens/

Handles authentication, pagination, and error translation for the
pull requests endpoint.
"""

from __future__ import annotations

import httpx

from bitbucket_cli.auth import BitbucketCredentials
from bitbucket_cli.models import (
    PaginatedPullRequestResponse,
    PullRequestResource,
    PullRequestState,
)

BITBUCKET_API_BASE_URL = "https://api.bitbucket.org/2.0"


class BitbucketApiError(Exception):
    """
    Raised when the Bitbucket API returns a non-2xx response.

    Includes the HTTP status code and response body for debugging.
    """

    def __init__(self, status_code: int, response_body: str) -> None:
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(
            f"Bitbucket API error (HTTP {status_code}): {response_body}"
        )


def _build_initial_url(workspace: str, repo_slug: str) -> str:
    """
    Build the initial URL for the pull requests list endpoint.

    Args:
        workspace: Bitbucket workspace slug (e.g., "myteam").
        repo_slug: Repository slug (e.g., "my-repo").

    Returns:
        Fully qualified URL for the pull requests endpoint.
    """
    return f"{BITBUCKET_API_BASE_URL}/repositories/{workspace}/{repo_slug}/pullrequests"


def fetch_all_pull_requests(
    workspace: str,
    repo_slug: str,
    credentials: BitbucketCredentials,
    state: PullRequestState | None = None,
) -> list[PullRequestResource]:
    """
    Fetch all pull requests from a Bitbucket Cloud repository, handling pagination.

    Authenticates via HTTP Basic Auth using the Atlassian account email
    and API token from the provided credentials.

    Iterates through all pages by following the 'next' URL in each paginated
    response until no more pages remain.

    Args:
        workspace: Bitbucket workspace slug.
        repo_slug: Repository slug.
        credentials: Authenticated Bitbucket credentials (email + API token).
        state: Optional filter for PR state (OPEN, MERGED, DECLINED, SUPERSEDED).
            When None, the API returns pull requests in all states.

    Returns:
        Complete list of PullRequestResource objects across all pages.

    Raises:
        BitbucketApiError: If the API returns a non-2xx HTTP status code.
        httpx.RequestError: If a network-level error occurs (connection refused,
            DNS failure, timeout, etc.).
    """
    all_pull_requests: list[PullRequestResource] = []

    # Bitbucket Cloud API tokens authenticate via HTTP Basic Auth:
    # username = Atlassian account email, password = API token.
    auth = httpx.BasicAuth(
        username=credentials.email,
        password=credentials.api_token,
    )

    query_params: dict[str, str] = {}
    if state is not None:
        query_params["state"] = state.value

    initial_url = _build_initial_url(workspace, repo_slug)

    # next_url is either the initial URL (first request) or the 'next' link
    # from the previous paginated response. None means no more pages.
    next_url: str | None = initial_url

    with httpx.Client(auth=auth) as http_client:
        while next_url is not None:
            # For the first request, attach query params. For subsequent pages,
            # the 'next' URL from the API already includes pagination params.
            if next_url == initial_url and query_params:
                response = http_client.get(next_url, params=query_params)
            else:
                response = http_client.get(next_url)

            if not response.is_success:
                raise BitbucketApiError(
                    status_code=response.status_code,
                    response_body=response.text,
                )

            paginated_response = PaginatedPullRequestResponse.model_validate(
                response.json()
            )

            all_pull_requests.extend(paginated_response.values)
            next_url = paginated_response.next

    return all_pull_requests
