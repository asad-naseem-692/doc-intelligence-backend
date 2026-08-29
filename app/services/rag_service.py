import logging
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from openai import OpenAI

from app.core.config import settings
from app.models.document import Document
from app.models.chunk import Chunk
from app.models.qa_history import QAHistory
from app.models.user import User
from app.schemas.query import Citation, QueryResponse
from app.services.embedding_service import embed_single

logger = logging.getLogger(__name__)

# Gemini via OpenAI SDK
_client = OpenAI(
    api_key=settings.GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

TOP_K = 5
FALLBACK_MESSAGE = "I couldn't find enough information in your documents to answer this."


def retrieve_relevant_chunks(
    db: Session,
    user_id: UUID,
    query_vector: List[float],
    query_text: str,
    document_id: Optional[UUID] = None,
    top_k: int = TOP_K,
) -> List[Tuple[Chunk, Document, float]]:
    """
    Hybrid Retrieval:
    Combines dense vector similarity (pgvector cosine distance) with
    PostgreSQL full-text search (ts_rank), strictly scoped to the user's ready documents.
    Uses additive keyword boosting (dense similarity base + FTS boost) so pure semantic matches
    are never deflated when FTS is 0.
    Returns list of (Chunk, Document, hybrid_score) sorted by relevance.
    FEAT-15
    """
    # 1. Base query strictly scoped to current user's ready documents
    query = (
        db.query(
            Chunk,
            Document,
            Chunk.embedding.cosine_distance(query_vector).label("distance"),
            func.ts_rank(
                func.to_tsvector("english", Chunk.text),
                func.plainto_tsquery("english", query_text),
            ).label("fts_rank"),
        )
        .join(Document, Chunk.document_id == Document.id)
        .filter(
            Document.owner_id == user_id,
            Document.status == "ready",
        )
    )

    if document_id:
        query = query.filter(Document.id == document_id)

    # Fetch top candidates by vector distance
    results = query.order_by("distance").limit(top_k * 3).all()

    if not results:
        return []

    scored_chunks = []
    for chunk, doc, dist, fts_rank in results:
        # Cosine similarity: 1 - cosine_distance (distance in [0, 2])
        # Normalized similarity in [0, 1]
        cosine_sim = max(0.0, 1.0 - float(dist)) if dist is not None else 0.0
        
        # Additive keyword boost: exact FTS hits boost score up to +0.20
        keyword_boost = min(0.20, float(fts_rank) * 0.5) if fts_rank is not None else 0.0

        # Hybrid score: base cosine similarity + positive keyword boost (capped at 1.0)
        hybrid_score = min(1.0, cosine_sim + keyword_boost)
        scored_chunks.append((chunk, doc, hybrid_score))

    # Sort descending by hybrid score and take top_k
    scored_chunks.sort(key=lambda x: x[2], reverse=True)
    return scored_chunks[:top_k]


def generate_grounded_answer(
    question: str,
    context_chunks: List[Tuple[Chunk, Document, float]],
) -> str:
    """
    Generate an answer using ONLY the retrieved document chunks.
    No outside knowledge or hallucination allowed.
    FEAT-16
    """
    context_snippets = []
    for idx, (chunk, doc, score) in enumerate(context_chunks, 1):
        context_snippets.append(
            f"[Source {idx} - {doc.filename} (Chunk #{chunk.chunk_index})]:\n{chunk.text}"
        )

    context_block = "\n\n".join(context_snippets)

    system_prompt = (
        "You are an enterprise AI document assistant. Your task is to answer the user's question "
        "using ONLY the provided document excerpts below.\n\n"
        "Strict Guidelines:\n"
        "1. Answer strictly based on the provided context.\n"
        "2. Do NOT use any external knowledge, assumptions, or unverified claims.\n"
        "3. If the context does not contain enough information to answer the question, state: "
        f"\"{FALLBACK_MESSAGE}\"\n"
        "4. Be concise, precise, and professional."
    )

    user_prompt = f"Context:\n{context_block}\n\nQuestion: {question}\n\nAnswer:"

    response = _client.chat.completions.create(
        model=settings.GEMINI_CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
    )

    return response.choices[0].message.content.strip()


def answer_question(
    db: Session,
    user: User,
    question: str,
    document_id: Optional[UUID] = None,
) -> QueryResponse:
    """
    Orchestrate full RAG pipeline:
    1. Embed query (Gemini)
    2. Hybrid retrieve user's chunks with additive keyword boost
    3. Check confidence threshold (FEAT-17)
    4. Generate grounded answer (FEAT-16)
    5. Build citations (FEAT-18)
    6. Save to QAHistory
    7. Return QueryResponse
    FEAT-14
    """
    clean_question = question.strip()
    if not clean_question:
        return QueryResponse(
            answer="Please provide a valid question.",
            citations=[],
            is_fallback=True,
        )

    # 1. Embed question (AI call #1)
    query_vector = embed_single(clean_question)

    # 2. Hybrid retrieve chunks
    retrieved = retrieve_relevant_chunks(
        db=db,
        user_id=user.id,
        query_vector=query_vector,
        query_text=clean_question,
        document_id=document_id,
        top_k=TOP_K,
    )

    # 3. Confidence Threshold Check (FEAT-17 - deterministic comparison)
    is_fallback = False
    if not retrieved:
        is_fallback = True
    else:
        top_score = retrieved[0][2]
        if top_score < settings.RAG_CONFIDENCE_THRESHOLD:
            logger.info(
                f"Confidence score {top_score:.3f} below threshold {settings.RAG_CONFIDENCE_THRESHOLD:.3f}. "
                f"Triggering fallback."
            )
            is_fallback = True

    if is_fallback:
        answer = FALLBACK_MESSAGE
        citations: List[Citation] = []
    else:
        # 4. Generate grounded answer (AI call #2)
        answer = generate_grounded_answer(clean_question, retrieved)
        
        # Check if the LLM itself determined the answer is not in context
        if FALLBACK_MESSAGE.lower() in answer.lower() or "couldn't find enough information" in answer.lower():
            is_fallback = True
            citations = []
        else:
            # 5. Build citations (FEAT-18)
            citations = []
            for chunk, doc, score in retrieved:
                excerpt = chunk.text[:200] + ("..." if len(chunk.text) > 200 else "")
                citations.append(
                    Citation(
                        document_id=doc.id,
                        filename=doc.filename,
                        chunk_index=chunk.chunk_index,
                        excerpt=excerpt,
                    )
                )

    # 6. Save to QAHistory
    citations_data = [c.model_dump(mode="json") for c in citations]
    history_record = QAHistory(
        user_id=user.id,
        document_id=document_id,
        question=clean_question,
        answer=answer,
        citations=citations_data,
        is_fallback=is_fallback,
    )
    db.add(history_record)
    db.commit()

    return QueryResponse(
        answer=answer,
        citations=citations,
        is_fallback=is_fallback,
    )
