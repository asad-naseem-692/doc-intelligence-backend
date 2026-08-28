import logging
import threading
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.document import Document
from app.models.chunk import Chunk
from app.services.extraction_service import extract_text_from_file
from app.services.chunking_service import chunk_text
from app.services.embedding_service import embed_texts
from app.services.storage_service import delete_stored_file

logger = logging.getLogger(__name__)


def _process_document_sync(document_id: UUID) -> None:
    """
    Full document processing pipeline:
    1. Extract text from file (deterministic, no AI)
    2. Chunk text using LlamaIndex (deterministic, no AI)
    3. Generate embeddings via Gemini (AI - embeddings only)
    4. Store chunks + vectors in PostgreSQL/pgvector
    5. Update document status to "ready" or "failed"
    """
    db: Session = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Document {document_id} not found for processing")
            return

        # Step 1: Text extraction (no AI)
        try:
            text = extract_text_from_file(doc.file_path)
        except ValueError as e:
            doc.status = "failed"
            doc.error_message = f"Text extraction failed: {e}"
            db.commit()
            logger.error(f"Extraction failed for doc {document_id}: {e}")
            return

        # Step 2: Chunking (no AI)
        chunks = chunk_text(text)
        if not chunks:
            doc.status = "failed"
            doc.error_message = "No text chunks produced from document"
            db.commit()
            return

        # Step 3: Embed all chunk texts (Gemini embeddings - AI call)
        try:
            chunk_texts_list = [c.text for c in chunks]
            embeddings = embed_texts(chunk_texts_list)
        except RuntimeError as e:
            doc.status = "failed"
            doc.error_message = f"Embedding generation failed: {e}"
            db.commit()
            logger.error(f"Embedding failed for doc {document_id}: {e}")
            return

        # Step 4: Store chunks + vectors in DB (no AI)
        for chunk_obj, embedding_vector in zip(chunks, embeddings):
            chunk_record = Chunk(
                document_id=doc.id,
                chunk_index=chunk_obj.chunk_index,
                text=chunk_obj.text,
                embedding=embedding_vector,
            )
            db.add(chunk_record)

        # Step 5: Mark document as ready
        doc.status = "ready"
        doc.error_message = None
        db.commit()
        logger.info(
            f"Document {document_id} processed successfully: "
            f"{len(chunks)} chunks stored"
        )

    except Exception as e:
        logger.error(f"Unexpected error processing document {document_id}: {e}")
        try:
            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc and doc.status == "processing":
                doc.status = "failed"
                doc.error_message = f"Unexpected processing error: {e}"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def process_document_async(document_id: UUID) -> None:
    """
    Kick off document processing in a background thread so the upload
    endpoint returns immediately with status="processing".
    """
    thread = threading.Thread(
        target=_process_document_sync,
        args=(document_id,),
        daemon=True,
        name=f"doc-processor-{document_id}",
    )
    thread.start()
