from typing import List
from dataclasses import dataclass


CHUNK_SIZE = 400         # target tokens per chunk
CHUNK_OVERLAP = 50       # token overlap between chunks


@dataclass
class TextChunk:
    chunk_index: int
    text: str


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[TextChunk]:
    """
    Split text into overlapping chunks using LlamaIndex's token-aware splitter.
    No AI involved — this is deterministic text splitting.
    Each chunk tracks its index for citation reference.
    """
    from llama_index.core.node_parser import SentenceSplitter

    splitter = SentenceSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
    )
    # SentenceSplitter.split_text returns a list of raw strings
    raw_chunks = splitter.split_text(text)

    chunks = []
    for idx, chunk_text in enumerate(raw_chunks):
        stripped = chunk_text.strip()
        if stripped:
            chunks.append(TextChunk(chunk_index=idx, text=stripped))
    return chunks
