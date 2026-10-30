"""Save / restore a DB snapshot for offline fallback demo.

Usage:
    python -m app.db.snapshot save
    python -m app.db.snapshot restore
"""

from __future__ import annotations

import os
import shutil
import sys

from app.config import settings


def _db_path() -> str:
    return settings.DB_URL.replace("sqlite:///", "")


def save_snapshot() -> None:
    src = _db_path()
    dst = settings.SNAPSHOT_PATH
    if not os.path.exists(src):
        print(f"âœ— Database file not found: {src}")
        return
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    shutil.copy2(src, dst)
    print(f"âœ“ Snapshot saved to {dst}")


def restore_snapshot() -> None:
    src = settings.SNAPSHOT_PATH
    dst = _db_path()
    if not os.path.exists(src):
        print(f"âœ— Snapshot file not found: {src}")
        return
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    shutil.copy2(src, dst)
    print(f"âœ“ Snapshot restored to {dst}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.db.snapshot save|restore")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "save":
        save_snapshot()
    elif cmd == "restore":
        restore_snapshot()
    else:
        print(f"Unknown command: {cmd}. Use 'save' or 'restore'.")
        sys.exit(1)

