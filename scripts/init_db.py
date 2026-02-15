#!/usr/bin/env python3
"""Initialize the maverick database schema."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import init_db, get_db_path


def main():
    print("Initializing maverick database...")
    db_path = init_db()
    print(f"Database created at: {db_path}")
    print(f"Database size: {db_path.stat().st_size} bytes")

    # Verify tables exist
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()

    print(f"\nTables created ({len(tables)}):")
    for table in tables:
        print(f"  - {table}")


if __name__ == "__main__":
    main()
