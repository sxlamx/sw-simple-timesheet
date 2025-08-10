from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import csv
import io
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_supervisor
from app.crud.user import timesheet_submission, user
from app.crud.notification import notification as notification_crud
from app.schemas.user import TimesheetSubmission, TimesheetSubmissionCreate, TimesheetSubmissionUpdate, TimesheetEntry as TimesheetEntrySchema, TimesheetEntryCreate, TimesheetEntryUpdate
from app.models.user import TimesheetEntry
from app.models.user import User as UserModel
from app.api.deps import get_site_from_user
from app.services.google_sheets import google_sheets_service
from app.services.excel_export import excel_export_service
from app.services.notification_service import notification_service

router = APIRouter()

class CreateTimesheetRequest(BaseModel):
    year: int
    month: int

class TimesheetResponse(BaseModel):
    id: int
    google_sheet_url: str
    period_start: datetime
    period_end: datetime
    status: str
    total_hours: float = 0.0

@router.post("/create", response_model=TimesheetResponse)
async def create_timesheet(
    request: CreateTimesheetRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Create a new timesheet for the user (database storage only)"""
    
    # Google Sheets integration disabled - use database-only storage
    print(f"Creating database-only timesheet for {current_user.email}")
    sheet_url = "database_only_storage"  # Placeholder URL since we're using database only
    
    # Calculate period dates
    from datetime import datetime, date
    import calendar
    
    period_start = date(request.year, request.month, 1)
    last_day = calendar.monthrange(request.year, request.month)[1]
    period_end = date(request.year, request.month, last_day)
    
    # Create database record
    timesheet_create = TimesheetSubmissionCreate(
        period_start=datetime.combine(period_start, datetime.min.time()),
        period_end=datetime.combine(period_end, datetime.max.time()),
        google_sheet_url=sheet_url
    )
    
    timesheet = timesheet_submission.create(
        db=db, 
        obj_in=timesheet_create, 
        user_id=current_user.id
    )
    
    return TimesheetResponse(
        id=timesheet.id,
        google_sheet_url=timesheet.google_sheet_url,
        period_start=timesheet.period_start,
        period_end=timesheet.period_end,
        status=timesheet.status
    )

@router.get("/", response_model=List[TimesheetSubmission])
async def get_user_timesheets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get user's timesheets"""
    timesheets = timesheet_submission.get_by_user(
        db=db, 
        user_id=current_user.id, 
        skip=skip, 
        limit=limit
    )
    return timesheets

@router.get("/{timesheet_id}", response_model=TimesheetSubmission)
async def get_timesheet(
    timesheet_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get specific timesheet"""
    timesheet = timesheet_submission.get(db=db, id=timesheet_id)
    
    if not timesheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timesheet not found"
        )
    
    # Check permissions
    if timesheet.user_id != current_user.id and not current_user.is_supervisor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return timesheet

@router.post("/{timesheet_id}/submit")
async def submit_timesheet(
    timesheet_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Submit timesheet for approval"""
    timesheet = timesheet_submission.get(db=db, id=timesheet_id)
    
    if not timesheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timesheet not found"
        )
    
    if timesheet.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only submit your own timesheets"
        )
    
    if timesheet.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Timesheet is not in draft status"
        )
    
    # Calculate total hours from database entries
    from app.models.user import TimesheetEntry
    entries = db.query(TimesheetEntry).filter(TimesheetEntry.submission_id == timesheet.id).all()
    total_hours = sum(entry.total_hours or 0 for entry in entries)
    
    # Update status to submitted
    update_data = TimesheetSubmissionUpdate(
        status="pending",
        total_hours=int(total_hours)
    )
    
    updated_timesheet = timesheet_submission.update(
        db=db, 
        db_obj=timesheet, 
        obj_in=update_data
    )
    
    # Google Sheets integration disabled - database storage only
    
    # Create notification for supervisor
    try:
        supervisor = user.get(db=db, id=current_user.supervisor_id) if current_user.supervisor_id else None
        if supervisor:
            site_id = get_site_from_user(current_user)
            notification_crud.create_pending_approval_notification(
                db=db,
                supervisor_id=supervisor.id,
                site_id=site_id,
                timesheet_id=timesheet_id,
                submitter_name=current_user.full_name
            )
            
            # Also send email notification if service is available
            notification_service.send_timesheet_submitted_notification(
                timesheet=updated_timesheet,
                staff_user=current_user,
                supervisor=supervisor
            )
    except Exception as e:
        # Log error but don't fail the submission
        print(f"Failed to send notification: {e}")
    
    return {"message": "Timesheet submitted successfully", "timesheet": updated_timesheet}

@router.post("/{timesheet_id}/approve")
async def approve_timesheet(
    timesheet_id: int,
    review_notes: str = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_supervisor)
):
    """Approve a timesheet (supervisor only)"""
    timesheet = timesheet_submission.get(db=db, id=timesheet_id)
    
    if not timesheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timesheet not found"
        )
    
    if timesheet.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Timesheet is not pending approval"
        )
    
    # Update status to approved
    update_data = TimesheetSubmissionUpdate(
        status="approved",
        review_notes=review_notes
    )
    
    updated_timesheet = timesheet_submission.update(
        db=db, 
        db_obj=timesheet, 
        obj_in=update_data,
        reviewer_id=current_user.id,
        reviewer_name=current_user.full_name
    )
    
    # Google Sheets integration disabled - database storage only
    
    # Create notification for staff member
    try:
        staff_member = user.get(db=db, id=timesheet.user_id)
        if staff_member:
            site_id = get_site_from_user(current_user)
            notification_crud.create_timesheet_approval_notification(
                db=db,
                user_id=staff_member.id,
                site_id=site_id,
                timesheet_id=timesheet_id,
                status="approved"
            )
            
            # Also send email notification if service is available
            notification_service.send_timesheet_approved_notification(
                timesheet=updated_timesheet,
                staff_user=staff_member,
                supervisor=current_user
            )
    except Exception as e:
        print(f"Failed to send approval notification: {e}")
    
    return {"message": "Timesheet approved successfully", "timesheet": updated_timesheet}

@router.post("/{timesheet_id}/reject")
async def reject_timesheet(
    timesheet_id: int,
    review_notes: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_supervisor)
):
    """Reject a timesheet (supervisor only)"""
    timesheet = timesheet_submission.get(db=db, id=timesheet_id)
    
    if not timesheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timesheet not found"
        )
    
    if timesheet.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Timesheet is not pending approval"
        )
    
    # Update status to rejected
    update_data = TimesheetSubmissionUpdate(
        status="rejected",
        review_notes=review_notes
    )
    
    updated_timesheet = timesheet_submission.update(
        db=db, 
        db_obj=timesheet, 
        obj_in=update_data,
        reviewer_id=current_user.id,
        reviewer_name=current_user.full_name
    )
    
    # Google Sheets integration disabled - database storage only
    
    # Create notification for staff member
    try:
        staff_member = user.get(db=db, id=timesheet.user_id)
        if staff_member:
            site_id = get_site_from_user(current_user)
            notification_crud.create_timesheet_approval_notification(
                db=db,
                user_id=staff_member.id,
                site_id=site_id,
                timesheet_id=timesheet_id,
                status="rejected"
            )
            
            # Also send email notification if service is available
            notification_service.send_timesheet_rejected_notification(
                timesheet=updated_timesheet,
                staff_user=staff_member,
                supervisor=current_user
            )
    except Exception as e:
        print(f"Failed to send rejection notification: {e}")
    
    return {"message": "Timesheet rejected", "timesheet": updated_timesheet}

@router.get("/pending/review", response_model=List[TimesheetSubmission])
async def get_pending_timesheets(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_supervisor)
):
    """Get all pending timesheets for review (supervisor only)"""
    pending_timesheets = timesheet_submission.get_pending_for_supervisor(
        db=db, 
        supervisor_id=current_user.id
    )
    return pending_timesheets

@router.get("/data/{timesheet_id}")
async def get_timesheet_data(
    timesheet_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get actual timesheet data from Google Sheets"""
    timesheet = timesheet_submission.get(db=db, id=timesheet_id)
    
    if not timesheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timesheet not found"
        )
    
    # Check permissions
    if timesheet.user_id != current_user.id and not current_user.is_supervisor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get data from database entries
    from app.models.user import TimesheetEntry
    entries = db.query(TimesheetEntry).filter(TimesheetEntry.submission_id == timesheet.id).all()
    
    timesheet_data = []
    for entry in entries:
        timesheet_data.append({
            "id": entry.id,
            "date": entry.date.strftime('%Y-%m-%d') if entry.date else '',
            "start_time": entry.start_time.strftime('%H:%M:%S') if entry.start_time else '',
            "end_time": entry.end_time.strftime('%H:%M:%S') if entry.end_time else '',
            "break_duration": entry.break_duration or 0,
            "total_hours": entry.total_hours or 0,
            "project": entry.project or '',
            "task_description": entry.task_description or ''
        })
    
    return {
        "timesheet_id": timesheet_id,
        "status": timesheet.status,
        "data": timesheet_data,
        "total_hours": sum(entry.total_hours or 0 for entry in entries)
    }

@router.get("/{timesheet_id}/export")
async def export_timesheet_to_excel(
    timesheet_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Export individual timesheet to Excel"""
    timesheet = timesheet_submission.get(db=db, id=timesheet_id)
    
    if not timesheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timesheet not found"
        )
    
    # Check permissions
    if timesheet.user_id != current_user.id and not current_user.is_supervisor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get user info
    timesheet_user = user.get(db=db, id=timesheet.user_id)
    if not timesheet_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prepare timesheet data
    timesheet_data = {
        "period_start": timesheet.period_start.strftime('%Y-%m-%d') if timesheet.period_start else '',
        "period_end": timesheet.period_end.strftime('%Y-%m-%d') if timesheet.period_end else '',
        "status": timesheet.status,
        "total_hours": timesheet.total_hours or 0,
        "google_sheet_url": timesheet.google_sheet_url,
        "submitted_at": timesheet.submitted_at.strftime('%Y-%m-%d') if timesheet.submitted_at else '',
        "reviewed_at": timesheet.reviewed_at.strftime('%Y-%m-%d') if timesheet.reviewed_at else ''
    }
    
    user_info = {
        "full_name": timesheet_user.full_name,
        "email": timesheet_user.email
    }
    
    # Generate Excel file
    excel_data = excel_export_service.export_individual_timesheet(timesheet_data, user_info)
    
    # Create filename
    period_str = timesheet.period_start.strftime('%Y-%m') if timesheet.period_start else 'unknown'
    filename = f"timesheet_{timesheet_user.email}_{period_str}.xlsx"
    
    return Response(
        content=excel_data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/team/all")
async def get_all_team_timesheets(
    status: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_supervisor)
):
    """Get all team timesheets with optional status filter (supervisor only)"""
    timesheets = timesheet_submission.get_all_for_supervisor(
        db=db, 
        supervisor_id=current_user.id,
        status=status,
        skip=skip,
        limit=limit
    )
    
    # Add staff member information to each timesheet
    staff_users = user.get_staff_by_supervisor(db=db, supervisor_id=current_user.id)
    staff_dict = {staff.id: staff for staff in staff_users}
    
    enriched_timesheets = []
    for timesheet in timesheets:
        staff_member = staff_dict.get(timesheet.user_id)
        timesheet_data = {
            "id": timesheet.id,
            "user_id": timesheet.user_id,
            "staff_name": staff_member.full_name if staff_member else "Unknown",
            "staff_email": staff_member.email if staff_member else "Unknown",
            "period_start": timesheet.period_start,
            "period_end": timesheet.period_end,
            "status": timesheet.status,
            "total_hours": timesheet.total_hours or 0,
            "submitted_at": timesheet.submitted_at,
            "reviewed_at": timesheet.reviewed_at,
            "review_notes": timesheet.review_notes,
            "google_sheet_url": timesheet.google_sheet_url
        }
        enriched_timesheets.append(timesheet_data)
    
    return enriched_timesheets

@router.get("/team/statistics")
async def get_team_statistics(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_supervisor)
):
    """Get team timesheet statistics (supervisor only)"""
    stats = timesheet_submission.get_team_statistics(db=db, supervisor_id=current_user.id)
    
    # Add team member count
    team_members = user.get_staff_by_supervisor(db=db, supervisor_id=current_user.id)
    stats["team_member_count"] = len(team_members)
    
    return stats

@router.get("/analytics/monthly")
async def get_monthly_analytics(
    months: int = 6,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get monthly timesheet analytics for current user"""
    from datetime import datetime, timedelta
    from dateutil.relativedelta import relativedelta
    
    # Get user timesheets from last N months
    user_timesheets = timesheet_submission.get_by_user(db=db, user_id=current_user.id, limit=1000)
    
    # Calculate monthly data
    monthly_data = []
    current_date = datetime.now()
    
    for i in range(months):
        month_date = current_date - relativedelta(months=i)
        month_str = month_date.strftime('%Y-%m')
        month_name = month_date.strftime('%b %Y')
        
        # Find timesheets for this month
        month_timesheets = [
            ts for ts in user_timesheets 
            if ts.period_start and ts.period_start.strftime('%Y-%m') == month_str
        ]
        
        total_hours = sum(ts.total_hours or 0 for ts in month_timesheets)
        submitted_count = len([ts for ts in month_timesheets if ts.status != 'draft'])
        approved_count = len([ts for ts in month_timesheets if ts.status == 'approved'])
        
        monthly_data.append({
            "month": month_name,
            "total_hours": total_hours,
            "submitted_count": submitted_count,
            "approved_count": approved_count,
            "timesheets": len(month_timesheets)
        })
    
    return list(reversed(monthly_data))

@router.get("/analytics/team-monthly")
async def get_team_monthly_analytics(
    months: int = 6,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_supervisor)
):
    """Get team monthly analytics (supervisor only)"""
    from datetime import datetime, timedelta
    from dateutil.relativedelta import relativedelta
    
    # Get all team timesheets
    team_timesheets = timesheet_submission.get_all_for_supervisor(db=db, supervisor_id=current_user.id, limit=1000)
    team_members = user.get_staff_by_supervisor(db=db, supervisor_id=current_user.id)
    
    # Calculate monthly data
    monthly_data = []
    current_date = datetime.now()
    
    for i in range(months):
        month_date = current_date - relativedelta(months=i)
        month_str = month_date.strftime('%Y-%m')
        month_name = month_date.strftime('%b %Y')
        
        # Find timesheets for this month
        month_timesheets = [
            ts for ts in team_timesheets 
            if ts.period_start and ts.period_start.strftime('%Y-%m') == month_str
        ]
        
        total_hours = sum(ts.total_hours or 0 for ts in month_timesheets)
        submitted_count = len([ts for ts in month_timesheets if ts.status != 'draft'])
        approved_count = len([ts for ts in month_timesheets if ts.status == 'approved'])
        pending_count = len([ts for ts in month_timesheets if ts.status == 'pending'])
        
        monthly_data.append({
            "month": month_name,
            "total_hours": total_hours,
            "submitted_count": submitted_count,
            "approved_count": approved_count,
            "pending_count": pending_count,
            "timesheets": len(month_timesheets),
            "active_staff": len(set(ts.user_id for ts in month_timesheets))
        })
    
    return list(reversed(monthly_data))

@router.get("/analytics/staff-breakdown")
async def get_staff_breakdown_analytics(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_supervisor)
):
    """Get staff performance breakdown (supervisor only)"""
    team_members = user.get_staff_by_supervisor(db=db, supervisor_id=current_user.id)
    
    staff_data = []
    for staff_member in team_members:
        staff_timesheets = timesheet_submission.get_by_user(db=db, user_id=staff_member.id, limit=1000)
        
        total_hours = sum(ts.total_hours or 0 for ts in staff_timesheets)
        total_timesheets = len(staff_timesheets)
        approved_count = len([ts for ts in staff_timesheets if ts.status == 'approved'])
        pending_count = len([ts for ts in staff_timesheets if ts.status == 'pending'])
        rejected_count = len([ts for ts in staff_timesheets if ts.status == 'rejected'])
        
        # Calculate current month hours
        current_month = datetime.now().month
        current_year = datetime.now().year
        current_month_hours = sum([
            ts.total_hours or 0 for ts in staff_timesheets 
            if ts.period_start and ts.period_start.month == current_month 
            and ts.period_start.year == current_year
        ])
        
        staff_data.append({
            "staff_name": staff_member.full_name,
            "staff_email": staff_member.email,
            "total_hours": total_hours,
            "current_month_hours": current_month_hours,
            "total_timesheets": total_timesheets,
            "approved_count": approved_count,
            "pending_count": pending_count,
            "rejected_count": rejected_count,
            "approval_rate": (approved_count / total_timesheets * 100) if total_timesheets > 0 else 0
        })
    
    return sorted(staff_data, key=lambda x: x['total_hours'], reverse=True)

@router.get("/export/team")
async def export_team_timesheets_to_excel(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_supervisor)
):
    """Export all team timesheets to Excel (supervisor only)"""
    
    # Get all timesheets for supervisor's team
    team_timesheets = timesheet_submission.get_all_for_supervisor(db=db, supervisor_id=current_user.id)
    
    # Also get staff information
    staff_users = user.get_staff_by_supervisor(db=db, supervisor_id=current_user.id)
    staff_dict = {staff.id: staff for staff in staff_users}
    
    all_timesheets = []
    for ts in team_timesheets:
        staff_member = staff_dict.get(ts.user_id)
        all_timesheets.append({
            "id": ts.id,
            "staff_name": staff_member.full_name if staff_member else "Unknown",
            "staff_email": staff_member.email if staff_member else "Unknown",
            "period": ts.period_start.strftime('%Y-%m') if ts.period_start else 'Unknown',
            "status": ts.status,
            "total_hours": ts.total_hours or 0,
            "submitted_at": ts.submitted_at.strftime('%Y-%m-%d') if ts.submitted_at else '',
            "reviewed_at": ts.reviewed_at.strftime('%Y-%m-%d') if ts.reviewed_at else '',
            "google_sheet_url": ts.google_sheet_url
        })
    
    supervisor_info = {
        "full_name": current_user.full_name,
        "email": current_user.email
    }
    
    # Generate Excel file
    excel_data = excel_export_service.export_team_timesheets(all_timesheets, supervisor_info)
    
    # Create filename
    current_date = datetime.now().strftime('%Y-%m-%d')
    filename = f"team_timesheets_{current_user.email}_{current_date}.xlsx"
    
    return Response(
        content=excel_data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

class BulkTimesheetEntryCreate(BaseModel):
    date: str  # YYYY-MM-DD format
    start_time: str = None  # HH:MM format 
    end_time: str = None  # HH:MM format
    break_duration: int = 0  # minutes
    total_hours: float
    project_id: int = None
    project: str = None  # fallback
    task_description: str = None
    entry_type: str = "normal"

@router.post("/{timesheet_id}/bulk-entries")
async def create_bulk_timesheet_entries(
    timesheet_id: int,
    entries: List[BulkTimesheetEntryCreate],
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Create multiple timesheet entries at once"""
    from app.crud.user import timesheet_entry
    from app.schemas.user import TimesheetEntryCreate
    
    # Verify timesheet exists and belongs to user
    timesheet = timesheet_submission.get(db=db, id=timesheet_id)
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    if timesheet.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only add entries to your own timesheet")
    
    if timesheet.status != "draft":
        raise HTTPException(status_code=400, detail="Can only add entries to draft timesheets")
    
    # Convert and create entries
    created_entries = []
    for entry_data in entries:
        try:
            # Parse date and times
            from datetime import datetime, time
            entry_date = datetime.strptime(entry_data.date, '%Y-%m-%d')
            
            start_datetime = None
            end_datetime = None
            
            if entry_data.start_time:
                start_time = datetime.strptime(entry_data.start_time, '%H:%M').time()
                start_datetime = datetime.combine(entry_date.date(), start_time)
            
            if entry_data.end_time:
                end_time = datetime.strptime(entry_data.end_time, '%H:%M').time()
                end_datetime = datetime.combine(entry_date.date(), end_time)
            
            entry_create = TimesheetEntryCreate(
                submission_id=timesheet_id,
                date=entry_date,
                start_time=start_datetime,
                end_time=end_datetime,
                break_duration=entry_data.break_duration,
                total_hours=entry_data.total_hours,
                project_id=entry_data.project_id,
                project=entry_data.project,
                task_description=entry_data.task_description,
                entry_type=entry_data.entry_type
            )
            
            created_entry = timesheet_entry.create(db=db, obj_in=entry_create)
            created_entries.append(created_entry)
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid date/time format: {e}")
    
    return {
        "message": f"Created {len(created_entries)} timesheet entries",
        "entries": created_entries
    }

@router.post("/{timesheet_id}/upload-csv")
async def upload_timesheet_csv(
    timesheet_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Upload CSV file with timesheet entries"""
    
    # Verify timesheet exists and belongs to user
    timesheet = timesheet_submission.get(db=db, id=timesheet_id)
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    if timesheet.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only upload to your own timesheet")
    
    if timesheet.status != "draft":
        raise HTTPException(status_code=400, detail="Can only upload to draft timesheets")
    
    # Validate file type
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        # Read CSV content
        contents = await file.read()
        csv_string = contents.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_string))
        
        # Expected columns: date, start_time, end_time, break_duration, total_hours, project, task_description, entry_type
        required_columns = ['date', 'total_hours']
        
        # Parse CSV entries
        entries = []
        for row_num, row in enumerate(csv_reader, 1):
            # Validate required columns
            missing_columns = [col for col in required_columns if col not in row or not row[col].strip()]
            if missing_columns:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Row {row_num}: Missing required columns: {missing_columns}"
                )
            
            entry = BulkTimesheetEntryCreate(
                date=row['date'].strip(),
                start_time=row.get('start_time', '').strip() or None,
                end_time=row.get('end_time', '').strip() or None,
                break_duration=int(row.get('break_duration', 0) or 0),
                total_hours=float(row['total_hours'].strip()),
                project=row.get('project', '').strip() or None,
                task_description=row.get('task_description', '').strip() or None,
                entry_type=row.get('entry_type', 'normal').strip() or 'normal'
            )
            entries.append(entry)
        
        if not entries:
            raise HTTPException(status_code=400, detail="CSV file is empty or has no valid entries")
        
        # Create entries using bulk endpoint
        return await create_bulk_timesheet_entries(timesheet_id, entries, db, current_user)
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding error. Please ensure the file is UTF-8 encoded.")
    except csv.Error as e:
        raise HTTPException(status_code=400, detail=f"CSV parsing error: {e}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Data validation error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {e}")

@router.get("/csv-template")
async def get_csv_template():
    """Download a CSV template for bulk entry"""
    csv_template = """date,start_time,end_time,break_duration,total_hours,project,task_description,entry_type
2024-01-01,09:00,17:00,60,8.0,Project Alpha,Development work,normal
2024-01-02,09:00,19:00,60,10.0,Project Beta,Overtime work,overtime
2024-01-03,10:00,15:00,30,5.0,Project Gamma,Holiday coverage,holiday"""
    
    return Response(
        content=csv_template,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=timesheet_template.csv"}
    )