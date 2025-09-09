from pathlib import Path

from .candidate_models import migrate as migrate_candidates


def migrate_db(db_path: Path) -> None:
    """CLI-friendly helper to upgrade the candidate database."""

    migrate_candidates(db_path)


__all__ = ["migrate_db"]
