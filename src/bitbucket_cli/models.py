"""
Pydantic models for Bitbucket Cloud Pull Request API responses and CSV export DTO.

These models map directly to the Bitbucket Cloud REST API v2 response shapes.
See: https://developer.atlassian.com/cloud/bitbucket/rest/api-group-pullrequests/
"""

from __future__ import annotations

import enum
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PullRequestState(str, enum.Enum):
    """
    Enum of possible pull request states in Bitbucket Cloud.

    Bitbucket Cloud uses uppercase strings for state values in the API.
    Using str mixin so the enum serializes cleanly to/from JSON strings.
    """

    OPEN = "OPEN"
    MERGED = "MERGED"
    DECLINED = "DECLINED"
    SUPERSEDED = "SUPERSEDED"


class PullRequestAuthor(BaseModel):
    """Represents the author of a pull request (subset of Bitbucket 'account' object)."""

    model_config = ConfigDict(strict=True)

    display_name: str


class BranchReference(BaseModel):
    """A reference to a branch by name."""

    model_config = ConfigDict(strict=True)

    name: str


class PullRequestEndpoint(BaseModel):
    """
    Source or destination endpoint of a pull request.

    Contains a branch reference. The branch may be None if the source branch
    was deleted after the PR was merged or declined.
    """

    model_config = ConfigDict(strict=True)

    branch: BranchReference | None = None


class PullRequestHtmlLink(BaseModel):
    """A single HTML link object from the Bitbucket API '_links' structure."""

    model_config = ConfigDict(strict=True)

    href: str


class PullRequestLinks(BaseModel):
    """Links associated with a pull request resource."""

    model_config = ConfigDict(strict=True)

    html: PullRequestHtmlLink


class PullRequestResource(BaseModel):
    """
    A single pull request as returned by the Bitbucket Cloud API.

    Maps to the objects in the 'values' array of the paginated list endpoint:
    GET /2.0/repositories/{workspace}/{repo_slug}/pullrequests
    """

    model_config = ConfigDict(strict=True)

    id: int
    title: str
    author: PullRequestAuthor
    state: PullRequestState
    source: PullRequestEndpoint
    destination: PullRequestEndpoint
    created_on: datetime
    updated_on: datetime
    links: PullRequestLinks


class PaginatedPullRequestResponse(BaseModel):
    """
    Paginated response wrapper from the Bitbucket Cloud API.

    The 'next' field contains the URL for the next page of results.
    When 'next' is None, there are no more pages to fetch.
    """

    model_config = ConfigDict(strict=True)

    size: int
    page: int
    pagelen: int
    next: str | None = None
    previous: str | None = None
    values: list[PullRequestResource]


class PullRequestCsvRow(BaseModel):
    """
    Flat data transfer object for writing a pull request to CSV.

    This DTO decouples the CSV output format from the nested API response structure.
    All fields are simple strings suitable for direct CSV serialization.
    """

    model_config = ConfigDict(strict=True)

    id: int
    title: str
    author: str
    state: str
    source_branch: str
    destination_branch: str
    created_on: str
    updated_on: str
    link: str

    @classmethod
    def from_api_resource(cls, resource: PullRequestResource) -> PullRequestCsvRow:
        """
        Transform a nested API resource into a flat CSV row.

        Handles the case where source/destination branches may be None
        (e.g., branch deleted after PR was merged) by substituting an empty string.
        """
        source_branch_name = (
            resource.source.branch.name
            if resource.source.branch is not None
            else ""
        )
        destination_branch_name = (
            resource.destination.branch.name
            if resource.destination.branch is not None
            else ""
        )

        return cls(
            id=resource.id,
            title=resource.title,
            author=resource.author.display_name,
            state=resource.state.value,
            source_branch=source_branch_name,
            destination_branch=destination_branch_name,
            created_on=resource.created_on.isoformat(),
            updated_on=resource.updated_on.isoformat(),
            link=resource.links.html.href,
        )
