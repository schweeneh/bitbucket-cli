"""
CLI entrypoint for the Bitbucket Cloud PR CSV Exporter.

Parses command-line arguments, resolves credentials, fetches pull requests
from the Bitbucket Cloud API, transforms them to flat CSV rows, and writes
the output to a file or stdout.

Authentication uses Bitbucket Cloud API tokens (email + token) via HTTP Basic Auth.
See: https://support.atlassian.com/bitbucket-cloud/docs/api-tokens/
"""

from __future__ import annotations

import argparse
import sys
from datetime import date

import httpx

from bitbucket_cli.api_client import BitbucketApiError, fetch_all_pull_requests
from bitbucket_cli.auth import CredentialError, resolve_credentials
from bitbucket_cli.csv_writer import write_pull_requests_to_csv
from bitbucket_cli.models import PullRequestCsvRow, PullRequestState


def _build_argument_parser() -> argparse.ArgumentParser:
    """
    Build the argparse parser with all CLI arguments.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="bitbucket-cli",
        description="Export pull requests from a Bitbucket Cloud repository to CSV.",
    )

    parser.add_argument(
        "workspace",
        help="Bitbucket workspace slug (e.g., 'myteam').",
    )
    parser.add_argument(
        "repo_slug",
        help="Repository slug (e.g., 'my-repo').",
    )
    parser.add_argument(
        "--state",
        type=str,
        choices=[state.value for state in PullRequestState],
        default=None,
        help="Filter pull requests by state. If omitted, returns all states.",
    )
    parser.add_argument(
        "--created-after",
        type=str,
        default=None,
        help=(
            "Include only pull requests created on or after this date (inclusive). "
            "Format: YYYY-MM-DD."
        ),
    )
    parser.add_argument(
        "--created-before",
        type=str,
        default=None,
        help=(
            "Include only pull requests created on or before this date (inclusive). "
            "Format: YYYY-MM-DD."
        ),
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output file path for CSV. If omitted, writes to stdout.",
    )
    parser.add_argument(
        "--email",
        type=str,
        default=None,
        help="Atlassian account email. Overrides BITBUCKET_EMAIL env var.",
    )
    parser.add_argument(
        "--api-token",
        type=str,
        default=None,
        help="Bitbucket API token. Overrides BITBUCKET_API_TOKEN env var.",
    )

    return parser


def main() -> None:
    """
    Main entrypoint: parse args -> resolve creds -> fetch PRs -> write CSV.

    Exits with code 1 on credential errors, API errors, or network failures.
    Prints a summary count of exported pull requests to stderr so it does not
    interfere with CSV output on stdout.
    """
    parser = _build_argument_parser()
    args = parser.parse_args()

    # --- Step 1: Resolve credentials ---
    try:
        credentials = resolve_credentials(
            cli_email=args.email,
            cli_api_token=args.api_token,
        )
    except CredentialError as credential_error:
        print(f"Error: {credential_error}", file=sys.stderr)
        sys.exit(1)

    # --- Step 2: Parse optional state filter ---
    state_filter: PullRequestState | None = None
    if args.state is not None:
        state_filter = PullRequestState(args.state)

    # --- Step 3: Parse optional created date range filters ---
    created_after_date: date | None = None
    if args.created_after is not None:
        try:
            created_after_date = date.fromisoformat(args.created_after)
        except ValueError:
            print(
                f"Error: Invalid date format for --created-after: '{args.created_after}'. "
                "Expected YYYY-MM-DD.",
                file=sys.stderr,
            )
            sys.exit(1)

    created_before_date: date | None = None
    if args.created_before is not None:
        try:
            created_before_date = date.fromisoformat(args.created_before)
        except ValueError:
            print(
                f"Error: Invalid date format for --created-before: '{args.created_before}'. "
                "Expected YYYY-MM-DD.",
                file=sys.stderr,
            )
            sys.exit(1)

    # --- Step 4: Fetch pull requests from API ---
    try:
        pull_request_resources = fetch_all_pull_requests(
            workspace=args.workspace,
            repo_slug=args.repo_slug,
            credentials=credentials,
            state=state_filter,
            created_after=created_after_date,
            created_before=created_before_date,
        )
    except BitbucketApiError as api_error:
        print(f"Error: {api_error}", file=sys.stderr)
        sys.exit(1)
    except httpx.RequestError as network_error:
        print(
            f"Error: Network request failed: {network_error}",
            file=sys.stderr,
        )
        sys.exit(1)

    # --- Step 5: Transform API resources to flat CSV rows ---
    csv_rows: list[PullRequestCsvRow] = [
        PullRequestCsvRow.from_api_resource(resource)
        for resource in pull_request_resources
    ]

    # --- Step 6: Write CSV output ---
    write_pull_requests_to_csv(rows=csv_rows, output_path=args.output)

    # --- Step 7: Summary to stderr ---
    filter_parts: list[str] = []
    if state_filter is not None:
        filter_parts.append(f"state={state_filter.value}")
    if created_after_date is not None:
        filter_parts.append(f"created>={created_after_date.isoformat()}")
    if created_before_date is not None:
        filter_parts.append(f"created<={created_before_date.isoformat()}")

    filter_description = f" ({', '.join(filter_parts)})" if filter_parts else ""
    print(
        f"Exported {len(csv_rows)} pull request(s){filter_description}.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
