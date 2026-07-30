"""Common utilities for tools: mock data loading and formatting."""

import json
import os
from pathlib import Path


def load_mock_data(filename: str) -> list[dict]:
    """Load mock data from JSON file in data directory."""
    data_dir = Path(__file__).parent.parent.parent / "data"
    file_path = data_dir / filename

    if not file_path.exists():
        return []

    try:
        with open(file_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def find_mock_record(data: list[dict], key: str, value: str) -> dict | None:
    """Find a single record in mock data by key-value pair."""
    for record in data:
        if record.get(key) == value:
            return record
    return None


def filter_mock_records(
    data: list[dict], key: str, search_term: str
) -> list[dict]:
    """Filter mock records by partial match on a key."""
    return [
        r
        for r in data
        if search_term.lower() in str(r.get(key, "")).lower()
    ]
