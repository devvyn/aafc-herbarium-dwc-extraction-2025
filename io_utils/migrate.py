from pathlib import Path

from .database import migrate as run_migrate


def migrate_db(db_path: Path) -> None:
    """CLI-friendly helper to run database migrations."""
    run_migrate(db_path)


__all__ = ["migrate_db"]
