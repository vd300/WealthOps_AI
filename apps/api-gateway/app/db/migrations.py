from pathlib import Path

import asyncpg

from app.core.config import Settings


MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


async def run_migrations(settings: Settings) -> None:
    connection = await asyncpg.connect(settings.database_url)
    try:
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )

        for migration_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
            version = migration_file.stem
            already_applied = await connection.fetchval(
                "SELECT 1 FROM schema_migrations WHERE version = $1",
                version,
            )
            if already_applied:
                continue

            async with connection.transaction():
                await connection.execute(migration_file.read_text(encoding="utf-8"))
                await connection.execute(
                    "INSERT INTO schema_migrations (version) VALUES ($1)",
                    version,
                )
    finally:
        await connection.close()
