from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from app.core.config import settings

def sqlite_path(database_url: str | None = None) -> Path:
    url = database_url or settings.database_url
    if not url.startswith("sqlite:///"):
        raise ValueError(
            "Phase 1 local runtime supports sqlite:/// URLs only."
        )
    return Path(url.removeprefix("sqlite:///"))

def check_database(
    database_url: str | None = None,
) -> tuple[bool, str | None]:
    try:
        path = sqlite_path(database_url)
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(path)) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        return True, None
    except Exception as exc:
        return False, str(exc)