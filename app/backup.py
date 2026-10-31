"""Create a consistent online SQLite backup: python -m app.backup /tmp/family.db"""

import argparse
import os
import sqlite3
from pathlib import Path

from .db import DATA


def create_backup(destination, source_path=None):
    destination = Path(destination)
    source_path = source_path or DATA / "family.db"
    if not source_path.exists():
        raise FileNotFoundError("Database bestaat nog niet.")

    descriptor = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    completed = False
    try:
        with (
            sqlite3.connect(f"file:{source_path}?mode=ro", uri=True) as source,
            sqlite3.connect(destination) as backup,
        ):
            source.backup(backup)
            if backup.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("Integriteitscontrole mislukt")
        completed = True
    finally:
        if not completed:
            destination.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    try:
        create_backup(args.destination)
    except FileExistsError:
        parser.error("Bestand bestaat al; kies een nieuw back-upbestand.")
    except FileNotFoundError as error:
        parser.error(str(error))
    print("Back-up en integriteitscontrole voltooid.")
