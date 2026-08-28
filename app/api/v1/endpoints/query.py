from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.query import QueryRequest, QueryResponse
from app.services.rag_service import answer_question

router = APIRouter()


@router.post("", response_model=QueryResponse, status_code=status.HTTP_200_OK)
def query_documents(
    request: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Accept a user's question, execute hybrid retrieval over their ready documents,
    apply confidence threshold check, generate grounded answer using Gemini chat model,
    and return answer with citations.
    FEAT-14
    """
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty",
        )

    response = answer_question(
        db=db,
        user=current_user,
        question=request.question,
        document_id=request.document_id,
    )
    return response
