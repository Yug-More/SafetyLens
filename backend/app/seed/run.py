"""Idempotent database seed entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow `python -m app.seed.run` from backend/
BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.database.session import SessionLocal, init_db
from app.seed.seed_data import seed_database


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        counts = seed_database(db)
        print("Seed completed successfully.")
        for key, value in counts.items():
            print(f"  {key}: {value}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
