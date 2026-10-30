"""Create a consistent online SQLite backup: python -m app.backup /tmp/family.db"""
import argparse
import sqlite3
from pathlib import Path
from .db import DATA

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    if args.destination.exists():
        parser.error('Bestand bestaat al; kies een nieuw back-upbestand.')
    if not (DATA / 'family.db').exists():
        parser.error('Database bestaat nog niet.')
    with sqlite3.connect(f'file:{DATA / "family.db"}?mode=ro', uri=True) as source, sqlite3.connect(args.destination) as destination:
        source.backup(destination)
        if destination.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError('Integriteitscontrole mislukt')
    args.destination.chmod(0o600)
    print('Back-up en integriteitscontrole voltooid.')
