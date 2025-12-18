from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from ..auth.dependencies import require_roles
from ..database import get_db
from ..models.sermon import Sermon
from ..models.series import Series
from ..models.existing_series import ExistingSeries
from ..models.user import User
from ..schemas.enums import UserRole
from ..schemas.sermon import SermonCreate, SermonResponse, SermonUpdate, SermonCountResponse, ExistingSeriesAssociate, ExistingSeriesResponse

router = APIRouter(prefix="/sermons", tags=["sermons"])


@router.get("/list", response_model=List[SermonResponse])
def get_all_sermons(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Get all sermons. Accessible by Admin."""
    sermons = db.query(Sermon).order_by(Sermon.date.desc()).all()
    return sermons


@router.get("/count", response_model=SermonCountResponse)
def get_sermon_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Get the total count of sermons. Accessible by Admin."""
    count = db.query(Sermon).count()
    return SermonCountResponse(total=count)


@router.get("/{sermon_id}", response_model=SermonResponse)
def get_sermon(
    sermon_id: str = Path(..., description="The ID (UUID) of the sermon"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Get a sermon by ID. Accessible by Admin."""
    sermon = db.query(Sermon).filter(Sermon.id == sermon_id).first()
    if not sermon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sermon not found")
    return sermon


@router.post("/create", response_model=SermonResponse, status_code=status.HTTP_201_CREATED)
def create_sermon(
    payload: SermonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Create a new sermon. Admin only."""
    sermon = Sermon(
        date=payload.date,
        time=payload.time,
        speaker=payload.speaker,
        passage=payload.passage,
        title=payload.title,
        description=payload.description,
        created_by_id=current_user.id,
    )
    db.add(sermon)
    db.commit()
    db.refresh(sermon)
    return sermon


@router.put("/update/{sermon_id}", response_model=SermonResponse)
def update_sermon(
    sermon_id: str = Path(..., description="The ID (UUID) of the sermon"),
    payload: SermonUpdate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Update a sermon. Admin only."""
    sermon = db.query(Sermon).filter(Sermon.id == sermon_id).first()
    if not sermon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sermon not found")

    # Update fields if provided
    if payload.date is not None:
        sermon.date = payload.date
    if payload.time is not None:
        sermon.time = payload.time
    if payload.speaker is not None:
        sermon.speaker = payload.speaker
    if payload.passage is not None:
        sermon.passage = payload.passage
    if payload.title is not None:
        sermon.title = payload.title
    if payload.description is not None:
        sermon.description = payload.description

    db.commit()
    db.refresh(sermon)
    return sermon


@router.delete("/delete/{sermon_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sermon(
    sermon_id: str = Path(..., description="The ID (UUID) of the sermon"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Delete a sermon. Admin only."""
    sermon = db.query(Sermon).filter(Sermon.id == sermon_id).first()
    if not sermon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sermon not found")
    db.delete(sermon)
    db.commit()


@router.post("/{sermons_id}/existing-series", response_model=SermonResponse, status_code=status.HTTP_200_OK)
def associate_existing_series(
    sermons_id: str = Path(..., description="The ID (UUID) of the sermon"),
    payload: ExistingSeriesAssociate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Associate an existing series with a sermon. Admin only."""
    from sqlalchemy.exc import IntegrityError
    
    # Verify sermon exists
    sermon = db.query(Sermon).filter(Sermon.id == sermons_id).first()
    if not sermon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sermon not found")
    
    # Verify series exists
    series = db.query(Series).filter(Series.id == payload.series_id).first()
    if not series:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Series not found")
    
    # Check if association already exists in existing_series table
    existing_association = db.query(ExistingSeries).filter(
        ExistingSeries.sermon_id == sermons_id,
        ExistingSeries.series_id == payload.series_id
    ).first()
    
    if existing_association:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Series is already associated with this sermon"
        )
    
    # Create new association in existing_series table
    try:
        existing_series_record = ExistingSeries(
            sermon_id=sermons_id,
            series_id=payload.series_id,
            created_by_id=current_user.id
        )
        db.add(existing_series_record)
        db.commit()
        db.refresh(existing_series_record)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Series is already associated with this sermon"
        )
    
    # Refresh sermon to get latest data
    db.refresh(sermon)
    return sermon


@router.get("/{sermons_id}/existing-series", response_model=ExistingSeriesResponse)
def get_unused_series(
    sermons_id: str = Path(..., description="The ID (UUID) of the sermon"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Get list of unused series IDs for a sermon. Accessible by Admin."""
    # Verify sermon exists
    sermon = db.query(Sermon).filter(Sermon.id == sermons_id).first()
    if not sermon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sermon not found")
    
    # Get all series from the database
    all_series = db.query(Series).all()
    
    # Get series IDs that are already associated with the sermon in existing_series table
    associated_series_records = db.query(ExistingSeries).filter(
        ExistingSeries.sermon_id == sermons_id
    ).all()
    associated_series_ids = {record.series_id for record in associated_series_records}
    
    # Get unused series IDs (series not associated with the sermon)
    unused_series_ids = [series.id for series in all_series if series.id not in associated_series_ids]
    
    return ExistingSeriesResponse(unused_series_ids=unused_series_ids)

