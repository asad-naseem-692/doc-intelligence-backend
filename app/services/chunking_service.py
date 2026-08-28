import re
from typing import List
from dataclasses import dataclass


CHUNK_SIZE = 400         # target tokens per chunk
CHUNK_OVERLAP = 50       # token overlap between chunks


@dataclass
class TextChunk:
    chunk_index: int
    text: str


def _split_into_sentences(text: str) -> List[str]:
    """
    Deterministic sentence tokenizer using regex to avoid NLTK filesystem
    hardlink security restrictions (CWE-59 / pathsec) in containerized environments.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


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
        chunking_tokenizer_fn=_split_into_sentences,
    )
    raw_chunks = splitter.split_text(text)

    chunks = []
    for idx, chunk_text in enumerate(raw_chunks):
        stripped = chunk_text.strip()
        if stripped:
            chunks.append(TextChunk(chunk_index=idx, text=stripped))
    return chunks
