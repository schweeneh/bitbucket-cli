"""
Credential resolution for Bitbucket Cloud API authentication.

Resolves credentials using a priority chain: CLI arguments take precedence
over environment variables. Raises CredentialError with actionable messages
when credentials cannot be resolved.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

BITBUCKET_USERNAME_ENV_VAR = "BITBUCKET_USERNAME"
BITBUCKET_APP_PASSWORD_ENV_VAR = "BITBUCKET_APP_PASSWORD"


class CredentialError(Exception):
    """
    Raised when Bitbucket credentials cannot be resolved.

    The message includes actionable instructions for the user to provide
    credentials via CLI arguments or environment variables.
    """


@dataclass(frozen=True)
class BitbucketCredentials:
    """Immutable container for Bitbucket Cloud authentication credentials."""

    username: str
    app_password: str


def resolve_credentials(
    cli_username: str | None,
    cli_app_password: str | None,
) -> BitbucketCredentials:
    """
    Resolve Bitbucket credentials from CLI arguments or environment variables.

    Priority order:
        1. CLI arguments (--username, --app-password)
        2. Environment variables (BITBUCKET_USERNAME, BITBUCKET_APP_PASSWORD)

    Both username and app_password must be resolved from the same priority level
    or a mix of sources. Both values must be present for authentication to succeed.

    Args:
        cli_username: Username provided via CLI --username flag, or None.
        cli_app_password: App password provided via CLI --app-password flag, or None.

    Returns:
        BitbucketCredentials with resolved username and app_password.

    Raises:
        CredentialError: If either username or app_password cannot be resolved
            from any source.
    """
    username = cli_username or os.environ.get(BITBUCKET_USERNAME_ENV_VAR)
    app_password = cli_app_password or os.environ.get(BITBUCKET_APP_PASSWORD_ENV_VAR)

    missing_fields: list[str] = []

    if not username:
        missing_fields.append("username")
    if not app_password:
        missing_fields.append("app password")

    if missing_fields:
        missing_description = " and ".join(missing_fields)
        raise CredentialError(
            f"Missing Bitbucket {missing_description}. "
            f"Provide credentials via CLI flags (--username, --app-password) "
            f"or environment variables ({BITBUCKET_USERNAME_ENV_VAR}, {BITBUCKET_APP_PASSWORD_ENV_VAR})."
        )

    # At this point both values are guaranteed to be non-None strings.
    # The assertions satisfy the type checker without using cast().
    assert username is not None
    assert app_password is not None

    return BitbucketCredentials(username=username, app_password=app_password)
