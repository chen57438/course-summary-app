from __future__ import annotations


def normalize_text(text: str) -> str:
    return " ".join(text.split()).strip()


def chunk_text(text: str, max_chars: int = 6000, overlap_chars: int = 400) -> list[str]:
    normalized = normalize_text(text)
    if not normalized:
        return []

    if len(normalized) <= max_chars:
        return [normalized]

    chunks: list[str] = []
    start = 0

    while start < len(normalized):
        end = min(start + max_chars, len(normalized))
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(normalized):
            break

        start = max(end - overlap_chars, start + 1)

    return chunks
