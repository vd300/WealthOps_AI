from dataclasses import dataclass
from uuid import UUID

import httpx

from app.core.config import Settings


@dataclass(frozen=True)
class RetrievedChunk:
    document_id: UUID
    chunk_id: UUID
    content: str
    score: float
    filename: str | None = None
    chunk_index: int | None = None
    page_number: int | None = None


class QdrantVectorStore:
    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.qdrant_url.rstrip("/")
        self._collection = settings.qdrant_collection_name
        self._dimensions = settings.embedding_dimensions

    async def ensure_collection(self) -> None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self._base_url}/collections/{self._collection}")
            if response.status_code == 200:
                return
            response.raise_for_status() if response.status_code != 404 else None
            create_response = await client.put(
                f"{self._base_url}/collections/{self._collection}",
                json={
                    "vectors": {
                        "size": self._dimensions,
                        "distance": "Cosine",
                    }
                },
            )
            create_response.raise_for_status()

    async def upsert_chunks(
        self,
        *,
        document_id: UUID,
        filename: str,
        chunks: list[dict],
        vectors: list[list[float]],
    ) -> None:
        points = []
        for chunk, vector in zip(chunks, vectors, strict=True):
            points.append(
                {
                    "id": str(chunk["id"]),
                    "vector": vector,
                    "payload": {
                        "document_id": str(document_id),
                        "filename": filename,
                        "chunk_id": str(chunk["id"]),
                        "chunk_index": chunk["chunk_index"],
                        "page_number": chunk.get("page_number"),
                        "content": chunk["content"],
                        **chunk.get("metadata", {}),
                    },
                }
            )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{self._base_url}/collections/{self._collection}/points",
                params={"wait": "true"},
                json={"points": points},
            )
            response.raise_for_status()

    async def search_chunks(
        self,
        *,
        query_vector: list[float],
        top_k: int,
        document_ids: list[UUID] | None = None,
    ) -> list[RetrievedChunk]:
        payload: dict = {
            "vector": query_vector,
            "limit": top_k,
            "with_payload": True,
            "with_vector": False,
        }
        if document_ids:
            payload["filter"] = {
                "must": [
                    {
                        "key": "document_id",
                        "match": {"any": [str(document_id) for document_id in document_ids]},
                    }
                ]
            }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self._base_url}/collections/{self._collection}/points/search",
                json=payload,
            )
            if response.status_code == 404:
                return []
            response.raise_for_status()

        points = response.json().get("result", [])
        return [_retrieved_chunk_from_point(point) for point in points]


def _retrieved_chunk_from_point(point: dict) -> RetrievedChunk:
    payload = point.get("payload") or {}
    return RetrievedChunk(
        document_id=UUID(payload["document_id"]),
        chunk_id=UUID(payload.get("chunk_id") or point["id"]),
        content=payload.get("content", ""),
        score=float(point.get("score", 0.0)),
        filename=payload.get("filename"),
        chunk_index=payload.get("chunk_index"),
        page_number=payload.get("page_number"),
    )
