from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.crud.user import timesheet_submission
from app.schemas.user import TimesheetEntry as TimesheetEntrySchema, TimesheetEntryCreate, TimesheetEntryUpdate
from app.models.user import TimesheetEntry, User as UserModel

router = APIRouter()

# Timesheet Entry endpoints for inline grid editing
@router.get("/submission/{submission_id}", response_model=List[TimesheetEntrySchema])
async def get_entries_by_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get all entries for a specific timesheet submission (alternative endpoint)"""
    # Verify timesheet exists and user has access
    timesheet = timesheet_submission.get(db=db, id=submission_id)
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    if timesheet.user_id != current_user.id and not current_user.is_supervisor:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get entries for this timesheet
    entries = db.query(TimesheetEntry).filter(TimesheetEntry.submission_id == submission_id).order_by(TimesheetEntry.date).all()
    return entries

@router.get("/{timesheet_id}/entries", response_model=List[TimesheetEntrySchema])
async def get_timesheet_entries(
    timesheet_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get all entries for a specific timesheet"""
    # Verify timesheet exists and user has access
    timesheet = timesheet_submission.get(db=db, id=timesheet_id)
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    if timesheet.user_id != current_user.id and not current_user.is_supervisor:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get entries for this timesheet
    entries = db.query(TimesheetEntry).filter(TimesheetEntry.submission_id == timesheet_id).order_by(TimesheetEntry.date).all()
    return entries

@router.post("/{timesheet_id}/entries", response_model=TimesheetEntrySchema)
async def create_timesheet_entry(
    timesheet_id: int,
    entry: TimesheetEntryCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Create a new timesheet entry"""
    # Verify timesheet exists and user has access
    timesheet = timesheet_submission.get(db=db, id=timesheet_id)
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    if timesheet.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only edit your own timesheets")
    
    # Create new entry
    db_entry = TimesheetEntry(
        submission_id=timesheet_id,
        date=entry.date,
        start_time=entry.start_time,
        end_time=entry.end_time,
        break_duration=entry.break_duration,
        total_hours=entry.total_hours,
        project=entry.project,
        task_description=entry.task_description
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    
    return db_entry

@router.put("/{timesheet_id}/entries/{entry_id}", response_model=TimesheetEntrySchema)
async def update_timesheet_entry(
    timesheet_id: int,
    entry_id: int,
    entry_update: TimesheetEntryUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Update a timesheet entry"""
    # Verify timesheet exists and user has access
    timesheet = timesheet_submission.get(db=db, id=timesheet_id)
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    if timesheet.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only edit your own timesheets")
    
    # Get the entry
    db_entry = db.query(TimesheetEntry).filter(
        TimesheetEntry.id == entry_id,
        TimesheetEntry.submission_id == timesheet_id
    ).first()
    
    if not db_entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    # Update fields
    for field, value in entry_update.dict(exclude_unset=True).items():
        setattr(db_entry, field, value)
    
    db.commit()
    db.refresh(db_entry)
    
    return db_entry

@router.delete("/{timesheet_id}/entries/{entry_id}")
async def delete_timesheet_entry(
    timesheet_id: int,
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Delete a timesheet entry"""
    # Verify timesheet exists and user has access
    timesheet = timesheet_submission.get(db=db, id=timesheet_id)
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    if timesheet.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only edit your own timesheets")
    
    # Get and delete the entry
    db_entry = db.query(TimesheetEntry).filter(
        TimesheetEntry.id == entry_id,
        TimesheetEntry.submission_id == timesheet_id
    ).first()
    
    if not db_entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    db.delete(db_entry)
    db.commit()
    
    return {"message": "Entry deleted successfully"}

# Alternative endpoints to match frontend API expectations
@router.post("/", response_model=TimesheetEntrySchema)
async def create_entry(
    entry: TimesheetEntryCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Create a new timesheet entry (alternative endpoint)"""
    # Verify timesheet exists and user has access
    timesheet = timesheet_submission.get(db=db, id=entry.submission_id)
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    if timesheet.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only edit your own timesheets")
    
    # Create new entry
    db_entry = TimesheetEntry(
        submission_id=entry.submission_id,
        date=entry.date,
        start_time=entry.start_time,
        end_time=entry.end_time,
        break_duration=entry.break_duration,
        total_hours=entry.total_hours,
        project=entry.project,
        task_description=entry.task_description
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    
    return db_entry

@router.put("/{entry_id}", response_model=TimesheetEntrySchema)
async def update_entry(
    entry_id: int,
    entry_update: TimesheetEntryUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Update a timesheet entry (alternative endpoint)"""
    # Get the entry
    db_entry = db.query(TimesheetEntry).filter(TimesheetEntry.id == entry_id).first()
    if not db_entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    # Verify user has access to the timesheet
    timesheet = timesheet_submission.get(db=db, id=db_entry.submission_id)
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    if timesheet.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only edit your own timesheets")
    
    # Update fields
    for field, value in entry_update.dict(exclude_unset=True).items():
        setattr(db_entry, field, value)
    
    db.commit()
    db.refresh(db_entry)
    
    return db_entry

@router.delete("/{entry_id}")
async def delete_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Delete a timesheet entry (alternative endpoint)"""
    # Get the entry
    db_entry = db.query(TimesheetEntry).filter(TimesheetEntry.id == entry_id).first()
    if not db_entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    # Verify user has access to the timesheet
    timesheet = timesheet_submission.get(db=db, id=db_entry.submission_id)
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    if timesheet.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only edit your own timesheets")
    
    db.delete(db_entry)
    db.commit()
    
    return {"message": "Entry deleted successfully"}