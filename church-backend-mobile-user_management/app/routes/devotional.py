from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from ..auth.dependencies import require_roles
from ..database import get_db
from ..models.devotional import Devotional
from ..models.user import User
from ..schemas.enums import UserRole
from ..schemas.devotional import (
    DevotionalCreate,
    DevotionalResponse,
    DevotionalUpdate,
    DevotionalCountResponse,
)

router = APIRouter(prefix="/devotional", tags=["devotional"])


@router.get("/list", response_model=List[DevotionalResponse])
def get_all_devotionals(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Get all devotionals. Accessible by Admin."""
    devotionals = db.query(Devotional).order_by(Devotional.date.desc()).all()
    return devotionals


@router.get("/count", response_model=DevotionalCountResponse)
def get_devotional_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Get the total count of devotionals. Accessible by Admin."""
    count = db.query(Devotional).count()
    return DevotionalCountResponse(total=count)


@router.get("/{devotional_id}", response_model=DevotionalResponse)
def get_devotional(
    devotional_id: str = Path(..., description="The ID (UUID) of the devotional"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Get a devotional by ID. Accessible by Admin."""
    devotional = db.query(Devotional).filter(Devotional.id == devotional_id).first()
    if not devotional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Devotional not found"
        )
    return devotional


@router.post("/create", response_model=DevotionalResponse, status_code=status.HTTP_201_CREATED)
def create_devotional(
    payload: DevotionalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Create a new devotional. Admin only."""
    devotional = Devotional(
        title=payload.title,
        date=payload.date,
        passage=payload.passage,
        leader=payload.leader,
        sermon_id=payload.sermon_id,
        created_by_id=current_user.id,
    )
    db.add(devotional)
    db.commit()
    db.refresh(devotional)
    return devotional


@router.put("/update/{devotional_id}", response_model=DevotionalResponse)
def update_devotional(
    devotional_id: str = Path(..., description="The ID (UUID) of the devotional"),
    payload: DevotionalUpdate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Update a devotional. Admin only."""
    devotional = db.query(Devotional).filter(Devotional.id == devotional_id).first()
    if not devotional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Devotional not found"
        )

    # Update fields if provided
    if payload.title is not None:
        devotional.title = payload.title
    if payload.date is not None:
        devotional.date = payload.date
    if payload.passage is not None:
        devotional.passage = payload.passage
    if payload.leader is not None:
        devotional.leader = payload.leader
    if payload.sermon_id is not None:
        devotional.sermon_id = payload.sermon_id

    db.commit()
    db.refresh(devotional)
    return devotional


@router.delete("/delete/{devotional_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_devotional(
    devotional_id: str = Path(..., description="The ID (UUID) of the devotional"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Delete a devotional. Admin only."""
    devotional = db.query(Devotional).filter(Devotional.id == devotional_id).first()
    if not devotional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Devotional not found"
        )
    db.delete(devotional)
    db.commit()

