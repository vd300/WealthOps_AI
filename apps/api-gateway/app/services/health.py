import asyncpg
import httpx
import redis.asyncio as redis

from app.core.config import Settings


async def check_service_connections(settings: Settings) -> dict[str, dict[str, str]]:
    return {
        "postgresql": await _check_postgresql(settings),
        "redis": await _check_redis(settings),
        "qdrant": await _check_qdrant(settings),
    }


async def _check_postgresql(settings: Settings) -> dict[str, str]:
    connection = None
    try:
        connection = await asyncpg.connect(
            settings.database_url,
            timeout=settings.service_check_timeout_seconds,
        )
        await connection.execute("SELECT 1")
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}
    finally:
        if connection is not None:
            await connection.close()


async def _check_redis(settings: Settings) -> dict[str, str]:
    client = redis.from_url(
        settings.redis_url,
        socket_connect_timeout=settings.service_check_timeout_seconds,
        socket_timeout=settings.service_check_timeout_seconds,
    )
    try:
        await client.ping()
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}
    finally:
        await client.aclose()


async def _check_qdrant(settings: Settings) -> dict[str, str]:
    base_url = settings.qdrant_url.rstrip("/")
    timeout = settings.service_check_timeout_seconds

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{base_url}/readyz")
            if response.status_code == 404:
                response = await client.get(base_url)
            response.raise_for_status()
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}
