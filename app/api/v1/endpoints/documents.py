from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentRead, DocumentStatus
from app.services.storage_service import save_uploaded_file, delete_stored_file
from app.services.extraction_service import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES
from app.services.pipeline_service import process_document_async

router = APIRouter()

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a PDF or DOCX file. Validates type and size server-side.
    Binds document to the authenticated user (from JWT, never from request body).
    Triggers async processing pipeline and immediately returns with status='processing'.
    FEAT-06
    """
    # Validate file extension
    import os
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are allowed",
        )

    # Read file and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {MAX_FILE_SIZE_BYTES // (1024*1024)} MB",
        )
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    # Save to disk
    file_path = save_uploaded_file(content, file.filename)

    # Create document record with status = "processing"
    document = Document(
        filename=file.filename,
        file_path=file_path,
        owner_id=current_user.id,
        status="processing",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Kick off async processing (extraction → chunking → embedding → vector store)
    process_document_async(document.id)

    return document


@router.get("", response_model=List[DocumentRead])
def list_my_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return only documents belonging to the authenticated user.
    Never returns another user's documents.
    FEAT-07
    """
    documents = (
        db.query(Document)
        .filter(Document.owner_id == current_user.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )
    return documents


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return a single document's current status. Ownership enforced.
    Used by the frontend to poll status while 'processing'.
    FEAT-08
    """
    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.owner_id == current_user.id,
        )
        .first()
    )
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return document


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a document and all its derived data (chunks, embeddings).
    Only the owning user can delete their document.
    Admins can also delete any document.
    FEAT-09
    """
    query = db.query(Document).filter(Document.id == document_id)

    # Admins can delete any document; regular users only their own
    if current_user.role != "admin":
        query = query.filter(Document.owner_id == current_user.id)

    document = query.first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Delete stored file from disk (chunks cascade via DB foreign key ondelete='CASCADE')
    delete_stored_file(document.file_path)

    db.delete(document)
    db.commit()

    return {"detail": "Document deleted successfully"}
