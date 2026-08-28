from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user
from app.core.database import get_db
from app.models.user import User
from app.models.document import Document
from app.schemas.user import UserRead
from app.services.storage_service import delete_stored_file

router = APIRouter()


@router.get("/users", response_model=List[UserRead], status_code=status.HTTP_200_OK)
def list_all_users(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """
    List all registered users in the system.
    Restricted to admin role only.
    Does NOT expose documents or chunk content of users.
    FEAT-20
    """
    users = db.query(User).order_by(User.created_at.desc()).all()
    return users


@router.patch("/users/{user_id}/suspend", response_model=UserRead, status_code=status.HTTP_200_OK)
def toggle_user_suspension(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """
    Toggle user account suspension status (is_active = True/False).
    Admin cannot suspend their own account.
    FEAT-21
    """
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin cannot suspend their own account",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Toggle active status
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)

    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """
    Permanently delete a user and all their associated data
    (documents, chunks, vectors, and Q&A history cascade-deleted).
    Admin cannot delete their own account.
    FEAT-21
    """
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin cannot delete their own account",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Clean up physical storage files for this user's documents
    user_docs = db.query(Document).filter(Document.owner_id == user.id).all()
    for doc in user_docs:
        delete_stored_file(doc.file_path)

    # Deleting user cascades all DB tables: documents -> chunks, and qa_history
    db.delete(user)
    db.commit()

    return {"detail": f"User {user.email} and all associated data deleted successfully"}
