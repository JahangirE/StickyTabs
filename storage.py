"""Persistence utilities for StickyTabs."""

import json
import os
import sys
from pathlib import Path


APP_NAME = "StickyTabs"
DATA_FILENAME = "notes_data.json"


def get_data_dir():
    """Return the platform-appropriate directory for StickyTabs user data."""

    if sys.platform == "win32":
        base_dir = Path(os.getenv("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base_dir = Path.home() / "Library" / "Application Support"
    else:
        base_dir = Path.home() / ".local" / "share"

    data_dir = base_dir / APP_NAME
    data_dir.mkdir(parents=True, exist_ok=True)

    return data_dir


DATA_FILE = get_data_dir() / DATA_FILENAME


def preserve_corrupt_file():
    """Rename an invalid save file so its contents are not overwritten."""

    corrupt_file = DATA_FILE.with_name(
        f"{DATA_FILE.stem}_corrupt{DATA_FILE.suffix}"
    )

    counter = 1

    while corrupt_file.exists():
        corrupt_file = DATA_FILE.with_name(
            f"{DATA_FILE.stem}_corrupt_{counter}{DATA_FILE.suffix}"
        )
        counter += 1

    DATA_FILE.replace(corrupt_file)


def load_data():
    """
    Load saved StickyTabs data.

    Returns None if no valid saved data is available.
    """

    if not DATA_FILE.exists():
        return None

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

    except json.JSONDecodeError:
        preserve_corrupt_file()
        return None

    except OSError:
        return None

    if not isinstance(data, dict):
        preserve_corrupt_file()
        return None

    return data


def save_data(data):
    """Save StickyTabs data dictionary to disk as JSON."""

    # Write to a temporary file first so an interrupted save
    # does not corrupt the existing notes file.
    temp_file = DATA_FILE.with_suffix(".tmp")

    with temp_file.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False,
        )

    temp_file.replace(DATA_FILE)