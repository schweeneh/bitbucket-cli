"""
CSV export for pull request data.

Writes PullRequestCsvRow objects to a CSV file or stdout with a fixed
column schema.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import TextIO

from bitbucket_cli.models import PullRequestCsvRow

# Column headers in the output CSV, matching PullRequestCsvRow field order.
CSV_COLUMN_HEADERS: list[str] = [
    "ID",
    "Title",
    "Author",
    "State",
    "Source Branch",
    "Destination Branch",
    "Created On",
    "Updated On",
    "Link",
]

# Field names on PullRequestCsvRow, in the same order as CSV_COLUMN_HEADERS.
# Kept explicit rather than relying on model_fields iteration order to avoid
# accidental column reordering if model fields are reordered.
_ROW_FIELD_NAMES: list[str] = [
    "id",
    "title",
    "author",
    "state",
    "source_branch",
    "destination_branch",
    "created_on",
    "updated_on",
    "link",
]


def _write_rows_to_stream(
    rows: list[PullRequestCsvRow],
    output_stream: TextIO,
) -> None:
    """
    Write CSV header and row data to an open text stream.

    Args:
        rows: List of flat CSV row DTOs to write.
        output_stream: Writable text stream (file or stdout).
    """
    writer = csv.writer(output_stream)
    writer.writerow(CSV_COLUMN_HEADERS)

    for row in rows:
        row_dict = row.model_dump()
        writer.writerow([row_dict[field_name] for field_name in _ROW_FIELD_NAMES])


def write_pull_requests_to_csv(
    rows: list[PullRequestCsvRow],
    output_path: str | None,
) -> None:
    """
    Write pull request rows to a CSV file or stdout.

    When output_path is None, writes to stdout. When output_path is provided,
    writes to that file path (creating or overwriting as needed).

    Args:
        rows: List of PullRequestCsvRow DTOs to export.
        output_path: File path to write CSV to, or None for stdout.
    """
    if output_path is None:
        _write_rows_to_stream(rows, sys.stdout)
    else:
        file_path = Path(output_path)
        with file_path.open("w", newline="", encoding="utf-8") as csv_file:
            _write_rows_to_stream(rows, csv_file)
