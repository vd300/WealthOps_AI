from dataclasses import dataclass
from uuid import UUID, uuid4

from app.services.text_extraction import ExtractedPage


@dataclass(frozen=True)
class DocumentChunk:
    id: UUID
    chunk_index: int
    content: str
    page_number: int
    start_char: int
    end_char: int

    def to_record(self) -> dict:
        return {
            "id": self.id,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "page_number": self.page_number,
            "metadata": {
                "page_number": self.page_number,
                "start_char": self.start_char,
                "end_char": self.end_char,
            },
        }


class DocumentChunker:
    def __init__(self, *, chunk_size: int, chunk_overlap: int) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("DOCUMENT_CHUNK_OVERLAP must be smaller than DOCUMENT_CHUNK_SIZE.")
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def chunk_pages(self, pages: list[ExtractedPage]) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        next_index = 0

        for page in pages:
            page_text = _normalize_text(page.text)
            if not page_text:
                continue

            start = 0
            while start < len(page_text):
                end = min(start + self._chunk_size, len(page_text))
                content = page_text[start:end].strip()
                if content:
                    chunks.append(
                        DocumentChunk(
                            id=uuid4(),
                            chunk_index=next_index,
                            content=content,
                            page_number=page.page_number,
                            start_char=start,
                            end_char=end,
                        )
                    )
                    next_index += 1

                if end == len(page_text):
                    break
                start = max(end - self._chunk_overlap, start + 1)

        return chunks


def _normalize_text(text: str) -> str:
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())
