"""
Credential resolution for Bitbucket Cloud API authentication.

Bitbucket Cloud API tokens are the modern replacement for app passwords.
They use HTTP Basic Auth with the Atlassian account email as the username
and the API token as the password.

See: https://support.atlassian.com/bitbucket-cloud/docs/api-tokens/

Resolves credentials using a priority chain: CLI arguments take precedence
over environment variables. Raises CredentialError with actionable messages
when credentials cannot be resolved.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

BITBUCKET_EMAIL_ENV_VAR = "BITBUCKET_EMAIL"
BITBUCKET_API_TOKEN_ENV_VAR = "BITBUCKET_API_TOKEN"


class CredentialError(Exception):
    """
    Raised when Bitbucket credentials cannot be resolved.

    The message includes actionable instructions for the user to provide
    credentials via CLI arguments or environment variables.
    """


@dataclass(frozen=True)
class BitbucketCredentials:
    """
    Immutable container for Bitbucket Cloud API token credentials.

    Uses the Atlassian account email and an API token for HTTP Basic Auth.
    API tokens are workspace-scoped and replace the legacy app password mechanism.
    """

    email: str
    api_token: str


def resolve_credentials(
    cli_email: str | None,
    cli_api_token: str | None,
) -> BitbucketCredentials:
    """
    Resolve Bitbucket credentials from CLI arguments or environment variables.

    Priority order:
        1. CLI arguments (--email, --api-token)
        2. Environment variables (BITBUCKET_EMAIL, BITBUCKET_API_TOKEN)

    Both email and api_token must be resolved from available sources.
    Both values must be present for authentication to succeed.

    Args:
        cli_email: Atlassian account email provided via CLI --email flag, or None.
        cli_api_token: API token provided via CLI --api-token flag, or None.

    Returns:
        BitbucketCredentials with resolved email and api_token.

    Raises:
        CredentialError: If either email or api_token cannot be resolved
            from any source.
    """
    email = cli_email or os.environ.get(BITBUCKET_EMAIL_ENV_VAR)
    api_token = cli_api_token or os.environ.get(BITBUCKET_API_TOKEN_ENV_VAR)

    missing_fields: list[str] = []

    if not email:
        missing_fields.append("email")
    if not api_token:
        missing_fields.append("API token")

    if missing_fields:
        missing_description = " and ".join(missing_fields)
        raise CredentialError(
            f"Missing Bitbucket {missing_description}. "
            f"Provide credentials via CLI flags (--email, --api-token) "
            f"or environment variables ({BITBUCKET_EMAIL_ENV_VAR}, {BITBUCKET_API_TOKEN_ENV_VAR})."
        )

    # At this point both values are guaranteed to be non-None strings.
    # The assertions satisfy the type checker without using cast().
    assert email is not None
    assert api_token is not None

    return BitbucketCredentials(email=email, api_token=api_token)
