# bitbucket-cli

A command-line tool that exports pull requests from Bitbucket Cloud repositories to CSV format. Supports filtering by PR state and date range, with automatic pagination across large result sets.

## Requirements

- Python 3.11+
- A Bitbucket Cloud account with an [API token](https://support.atlassian.com/bitbucket-cloud/docs/api-tokens/)

## Installation

```bash
# Using uv
uv sync

# Or with pip
pip install -e .
```

## Authentication

Provide your Atlassian account email and Bitbucket API token via environment variables or CLI arguments.

**Environment variables:**

```bash
export BITBUCKET_EMAIL="you@example.com"
export BITBUCKET_API_TOKEN="your-api-token"
```

CLI arguments (`--email` and `--api-token`) override environment variables when both are set.

## Usage

```
bitbucket-cli WORKSPACE REPO_SLUG [OPTIONS]
```

### Arguments

| Argument     | Description                          |
|--------------|--------------------------------------|
| `WORKSPACE`  | Bitbucket workspace slug             |
| `REPO_SLUG`  | Repository slug                      |

### Options

| Option                        | Description                                       |
|-------------------------------|---------------------------------------------------|
| `--state STATE`               | Filter by PR state: `OPEN`, `MERGED`, `DECLINED`, or `SUPERSEDED` |
| `--created-after YYYY-MM-DD`  | Include PRs created on or after this date          |
| `--created-before YYYY-MM-DD` | Include PRs created on or before this date         |
| `--output`, `-o FILE`         | Output file path (defaults to stdout)              |
| `--email EMAIL`               | Atlassian account email (overrides `BITBUCKET_EMAIL`) |
| `--api-token TOKEN`           | API token (overrides `BITBUCKET_API_TOKEN`)        |

### Examples

Export all pull requests to a file:

```bash
bitbucket-cli myteam my-repo -o pull-requests.csv
```

Export only merged PRs within a date range:

```bash
bitbucket-cli myteam my-repo --state MERGED --created-after 2025-12-01 --created-before 2025-12-31 -o december.csv
```

Print to stdout with explicit credentials:

```bash
bitbucket-cli myteam my-repo --email you@example.com --api-token abc123
```

## CSV Output

Each row represents a pull request with the following columns:

| Column             | Description                                |
|--------------------|--------------------------------------------|
| ID                 | Pull request number                        |
| Title              | Pull request title                         |
| Author             | Display name of the PR author              |
| State              | Current state (OPEN, MERGED, etc.)         |
| Source Branch       | Branch the PR is merging from (or `DELETED` if removed) |
| Destination Branch  | Branch the PR is merging into              |
| Created On         | ISO 8601 timestamp of PR creation          |
| Updated On         | ISO 8601 timestamp of last update          |
| Link               | URL to the pull request on Bitbucket       |

## Project Structure

```
src/bitbucket_cli/
    main.py          # CLI entrypoint and argument parsing
    auth.py          # Credential resolution (CLI args and env vars)
    api_client.py    # Bitbucket REST API client with pagination
    models.py        # Pydantic models for API responses and CSV rows
    csv_writer.py    # CSV file output
```
