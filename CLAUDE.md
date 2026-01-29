# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Run Commands

```bash
# Install dependencies
uv sync

# Run the CLI
uv run bitbucket-cli WORKSPACE REPO_SLUG [OPTIONS]

# Run with pip (alternative)
pip install -e .
bitbucket-cli WORKSPACE REPO_SLUG [OPTIONS]
```

There are no tests in this codebase currently.

## Architecture Overview

This is a single-purpose CLI tool that exports Bitbucket Cloud pull requests to CSV format. The data flow is linear:

```
main.py (CLI parsing)
    → auth.py (credential resolution)
    → api_client.py (API calls with pagination)
    → models.py (Pydantic parsing + DTO transformation)
    → csv_writer.py (output)
```

### Key Design Patterns

**DTO Transformation**: `PullRequestResource` (nested API response) is transformed to `PullRequestCsvRow` (flat DTO) via `PullRequestCsvRow.from_api_resource()`. This decouples CSV output format from API structure.

**Credential Priority Chain**: CLI arguments (`--email`, `--api-token`) override environment variables (`BITBUCKET_EMAIL`, `BITBUCKET_API_TOKEN`). See `auth.py:resolve_credentials()`.

**Defensive Client-Side Filtering**: The API client re-filters results locally after pagination because Bitbucket's API may not consistently apply query params across paginated responses. See `api_client.py:196-209`.

**Pagination Handling**: Uses the `next` URL from paginated responses to iterate all pages. The initial request includes query params; subsequent pages use the full `next` URL from the API.

### Authentication

Uses Bitbucket Cloud API tokens via HTTP Basic Auth where:
- Username = Atlassian account email
- Password = API token

## Environment Variables

| Variable | Description |
|----------|-------------|
| `BITBUCKET_EMAIL` | Atlassian account email |
| `BITBUCKET_API_TOKEN` | Bitbucket Cloud API token |
