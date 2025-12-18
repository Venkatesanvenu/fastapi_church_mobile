from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_user, require_roles
from ..database import get_db
from ..models.series import Series
from ..models.sermon import Sermon
from ..models.user import User
from ..schemas.enums import UserRole
from ..schemas.series import SeriesCreate, SeriesResponse, SeriesUpdate, SeriesCountResponse, SeriesCreateResponse, SeriesInsertSermons, SeriesDeleteSermons, SeriesDetailResponse, SeriesSermonsResponse
from ..schemas.sermon import SermonResponse

router = APIRouter(prefix="/series", tags=["series"])


@router.get("/list", response_model=List[SeriesResponse])
def get_all_series(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all series. Accessible by all authenticated users."""
    from sqlalchemy.orm import joinedload
    series = db.query(Series).options(joinedload(Series.sermons)).order_by(Series.from_date.desc()).all()
    return series


@router.get("/count", response_model=SeriesCountResponse)
def get_series_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the total count of series. Accessible by all authenticated users."""
    count = db.query(Series).count()
    return SeriesCountResponse(total=count)


@router.get("/{series_id}/sermons", response_model=SeriesSermonsResponse)
def get_series_sermons(
    series_id: str = Path(..., description="The ID (UUID) of the series"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get access and available sermons for a series. Accessible by all authenticated users."""
    from sqlalchemy.orm import joinedload
    
    # Get the series with its sermons
    series = db.query(Series).options(joinedload(Series.sermons)).filter(Series.id == series_id).first()
    if not series:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Series not found")
    
    # Get all sermons from the database
    all_sermons = db.query(Sermon).all()
    
    # Get sermon IDs that are in the series
    series_sermon_ids = {sermon.id for sermon in series.sermons}
    
    # Separate sermons into access_sermons (in series) and available_sermons (not in series)
    access_sermons = [sermon for sermon in all_sermons if sermon.id in series_sermon_ids]
    available_sermons = [sermon for sermon in all_sermons if sermon.id not in series_sermon_ids]
    
    # Convert to response format
    access_sermons_data = [SermonResponse.model_validate(sermon) for sermon in access_sermons]
    available_sermons_data = [SermonResponse.model_validate(sermon) for sermon in available_sermons]
    
    return SeriesSermonsResponse(
        access_sermons=access_sermons_data,
        available_sermons=available_sermons_data
    )


@router.get("/{series_id}", response_model=SeriesDetailResponse)
def get_series(
    series_id: str = Path(..., description="The ID (UUID) of the series"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a series by ID with access and available sermons. Accessible by all authenticated users."""
    from sqlalchemy.orm import joinedload
    
    # Get the series with its sermons
    series = db.query(Series).options(joinedload(Series.sermons)).filter(Series.id == series_id).first()
    if not series:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Series not found")
    
    # Get all sermons from the database
    all_sermons = db.query(Sermon).all()
    
    # Get sermon IDs that are in the series
    series_sermon_ids = {sermon.id for sermon in series.sermons}
    
    # Separate sermons into access_sermons (in series) and available_sermons (not in series)
    access_sermons = [sermon for sermon in all_sermons if sermon.id in series_sermon_ids]
    available_sermons = [sermon for sermon in all_sermons if sermon.id not in series_sermon_ids]
    
    # Convert to response format
    access_sermons_data = [SermonResponse.model_validate(sermon) for sermon in access_sermons]
    available_sermons_data = [SermonResponse.model_validate(sermon) for sermon in available_sermons]
    
    return SeriesDetailResponse(
        id=series.id,
        title=series.title,
        from_date=series.from_date,
        to_date=series.to_date,
        passage=series.passage,
        description=series.description,
        created_by_id=series.created_by_id,
        created_at=series.created_at,
        updated_at=series.updated_at,
        access_sermons=access_sermons_data,
        available_sermons=available_sermons_data
    )


@router.post("/create", response_model=SeriesCreateResponse, status_code=status.HTTP_201_CREATED)
def create_series(
    payload: SeriesCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Create a new series. Admin only."""
    # Validate date range
    if payload.from_date > payload.to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="from_date must be before or equal to to_date"
        )
    
    # Validate sermons_id if provided
    sermons_list = []
    if payload.sermons_id is not None and len(payload.sermons_id) > 0:
        # Validate all sermon IDs exist
        for sermon_id in payload.sermons_id:
            sermon = db.query(Sermon).filter(Sermon.id == sermon_id).first()
            if not sermon:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Sermon with id {sermon_id} not found"
                )
            sermons_list.append(sermon)
    
    # Ensure created_by_id is always set (admin user ID)
    admin_user_id = current_user.id
    if not admin_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in authentication token"
        )
    
    series = Series(
        title=payload.title,
        from_date=payload.from_date,
        to_date=payload.to_date,
        passage=payload.passage,
        description=payload.description,
        created_by_id=admin_user_id,  # Always set to admin user ID
    )
    
    # Add sermons to the series (many-to-many relationship)
    if sermons_list:
        series.sermons = sermons_list
    
    db.add(series)
    db.commit()
    db.refresh(series)
    
    # Reload series with sermons to ensure we have the latest data
    db.refresh(series)
    # Eagerly load sermons
    sermons_data = [SermonResponse.model_validate(sermon) for sermon in series.sermons]
    
    # Return response with full sermon details
    return SeriesCreateResponse(
        id=series.id,
        title=series.title,
        from_date=series.from_date,
        to_date=series.to_date,
        passage=series.passage,
        description=series.description,
        created_by_id=series.created_by_id,
        created_at=series.created_at,
        updated_at=series.updated_at,
        sermons=sermons_data
    )


@router.put("/update/{series_id}", response_model=SeriesResponse)
def update_series(
    series_id: str = Path(..., description="The ID (UUID) of the series"),
    payload: SeriesUpdate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Update a series. Admin only."""
    series = db.query(Series).filter(Series.id == series_id).first()
    if not series:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Series not found")

    # Update fields if provided
    if payload.title is not None:
        series.title = payload.title
    if payload.from_date is not None:
        series.from_date = payload.from_date
    if payload.to_date is not None:
        series.to_date = payload.to_date
    if payload.passage is not None:
        series.passage = payload.passage
    if payload.description is not None:
        series.description = payload.description

    # Validate date range if dates were updated
    if series.from_date > series.to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="from_date must be before or equal to to_date"
        )

    db.commit()
    db.refresh(series)
    return series


@router.post("/insert/{series_id}/", response_model=SeriesResponse, status_code=status.HTTP_200_OK)
def insert_sermons_to_series(
    series_id: str = Path(..., description="The ID (UUID) of the series"),
    payload: SeriesInsertSermons = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Insert sermons into an existing series. Admin only."""
    from sqlalchemy.orm import joinedload
    
    # Get the series
    series = db.query(Series).options(joinedload(Series.sermons)).filter(Series.id == series_id).first()
    if not series:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Series not found")
    
    # Get existing sermon IDs to avoid duplicates
    existing_sermon_ids = {sermon.id for sermon in series.sermons}
    
    # Validate all sermon IDs exist and collect new sermons
    new_sermons = []
    for sermon_id in payload.sermons_id:
        # Skip if already in the series
        if sermon_id in existing_sermon_ids:
            continue
        
        sermon = db.query(Sermon).filter(Sermon.id == sermon_id).first()
        if not sermon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sermon with id {sermon_id} not found"
            )
        new_sermons.append(sermon)
    
    # Add new sermons to the series (append to existing ones)
    if new_sermons:
        series.sermons.extend(new_sermons)
        db.commit()
        db.refresh(series)
        # Reload with sermons
        db.refresh(series)
    
    return series


@router.delete("/{series_id}/sermons", response_model=SeriesResponse, status_code=status.HTTP_200_OK)
def delete_sermons_from_series(
    series_id: str = Path(..., description="The ID (UUID) of the series"),
    payload: SeriesDeleteSermons = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Delete sermons from an existing series. Admin only."""
    from sqlalchemy.orm import joinedload
    
    # Get the series with sermons
    series = db.query(Series).options(joinedload(Series.sermons)).filter(Series.id == series_id).first()
    if not series:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Series not found")
    
    # Get existing sermon IDs
    existing_sermon_ids = {sermon.id for sermon in series.sermons}
    
    # Validate all sermon IDs exist in the series and collect sermons to remove
    sermons_to_remove = []
    for sermon_id in payload.sermons_id:
        if sermon_id not in existing_sermon_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sermon with id {sermon_id} is not in this series"
            )
        # Find the sermon object to remove
        sermon = next((s for s in series.sermons if s.id == sermon_id), None)
        if sermon:
            sermons_to_remove.append(sermon)
    
    # Remove sermons from the series
    if sermons_to_remove:
        for sermon in sermons_to_remove:
            series.sermons.remove(sermon)
        db.commit()
        db.refresh(series)
        # Reload with sermons
        db.refresh(series)
    
    return series


@router.delete("/delete/{series_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_series(
    series_id: str = Path(..., description="The ID (UUID) of the series"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Delete a series. Admin only."""
    series = db.query(Series).filter(Series.id == series_id).first()
    if not series:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Series not found")
    db.delete(series)
    db.commit()

