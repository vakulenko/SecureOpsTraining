"""Read/write access to the mock data, so approved actions actually change state.

Read-only tools can load the JSON files directly. Tools that change something (unlock an
account, request a password reset) need their change to stick, so a later status check
reflects it.

Writes go to a runtime copy under data/runtime/ instead of the tracked seed files in
data/. That keeps `git status` clean after a demo, and resetting is just deleting the
runtime folder -- see reset_runtime_data().
"""

import json
import os
from pathlib import Path

from src.tools.common import load_mock_data

DATA_DIR = Path(__file__).parent.parent.parent / "data"
DEFAULT_RUNTIME_DIR = DATA_DIR / "runtime"


def runtime_dir() -> Path:
    """Where writes go. Overridable with SOC_RUNTIME_DIR so tests use a temp folder."""
    override = os.getenv("SOC_RUNTIME_DIR")

    return Path(override) if override else DEFAULT_RUNTIME_DIR


def load_records(filename: str) -> list[dict]:
    """Load the runtime copy if something has been written, else the pristine seed."""
    runtime_file = runtime_dir() / filename

    if runtime_file.exists():
        try:
            with open(runtime_file, encoding="utf-8") as handle:
                return json.load(handle)
        except (json.JSONDecodeError, OSError):
            # A corrupt runtime file should not break the app; fall back to the seed.
            pass

    return load_mock_data(filename)


def save_records(filename: str, records: list[dict]) -> bool:
    """Write records to the runtime copy. Returns False if the write failed."""
    try:
        target_dir = runtime_dir()
        target_dir.mkdir(parents=True, exist_ok=True)

        with open(target_dir / filename, "w", encoding="utf-8") as handle:
            json.dump(records, handle, indent=2)
    except OSError:
        return False

    return True


def update_record(filename: str, key: str, value: str, changes: dict) -> dict | None:
    """Apply `changes` to the one record where record[key] == value.

    Returns the updated record, or None if no record matched or the write failed.
    """
    records = load_records(filename)

    for record in records:
        if record.get(key) == value:
            record.update(changes)
            return record if save_records(filename, records) else None

    return None


def reset_runtime_data() -> None:
    """Discard every write, returning the mock data to its seeded state."""
    target_dir = runtime_dir()

    if not target_dir.exists():
        return

    for path in target_dir.glob("*.json"):
        try:
            path.unlink()
        except OSError:
            pass
