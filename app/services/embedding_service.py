import time
import logging
from typing import List
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

# Gemini via OpenAI-compatible endpoint
_client = OpenAI(
    api_key=settings.GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2.0   # seconds
BATCH_SIZE = 20             # max texts per API call


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Convert a list of text strings to embedding vectors using Gemini.
    Batches requests and retries with exponential backoff on failure.
    Returns a list of float vectors, one per input text.
    """
    all_embeddings: List[List[float]] = []

    for batch_start in range(0, len(texts), BATCH_SIZE):
        batch = texts[batch_start: batch_start + BATCH_SIZE]
        embeddings = _embed_batch_with_retry(batch)
        all_embeddings.extend(embeddings)

    return all_embeddings


def embed_single(text: str) -> List[float]:
    """Embed a single text (for query-time embedding)."""
    results = embed_texts([text])
    return results[0]


def _embed_batch_with_retry(texts: List[str]) -> List[List[float]]:
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = _client.embeddings.create(
                model=settings.GEMINI_EMBEDDING_MODEL,
                input=texts,
            )
            # Gemini returns response.data in input order (index may be None for first element)
            return [item.embedding for item in response.data]
        except Exception as e:
            last_error = e
            wait_time = RETRY_BACKOFF_BASE ** attempt
            logger.warning(
                f"Embedding attempt {attempt + 1}/{MAX_RETRIES} failed: {e}. "
                f"Retrying in {wait_time:.1f}s..."
            )
            time.sleep(wait_time)

    raise RuntimeError(
        f"Embedding generation failed after {MAX_RETRIES} attempts: {last_error}"
    )
