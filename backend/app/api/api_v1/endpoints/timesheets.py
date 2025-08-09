from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_supervisor
from app.crud.user import timesheet_submission, user
from app.schemas.user import TimesheetSubmission, TimesheetSubmissionCreate, TimesheetSubmissionUpdate
from app.models.user import User as UserModel
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
    """Create a new Google Sheet timesheet for the user"""
    
    # Create Google Sheet
    sheet_url = google_sheets_service.create_timesheet_sheet(
        user_email=current_user.email,
        year=request.year,
        month=request.month
    )
    
    if not sheet_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create Google Sheet"
        )
    
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
    
    # Calculate total hours from Google Sheet
    total_hours = google_sheets_service.calculate_total_hours(timesheet.google_sheet_url)
    
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
    
    # Update Google Sheet status
    google_sheets_service.update_timesheet_status(timesheet.google_sheet_url, "submitted")
    
    # Send notification to supervisor
    try:
        supervisor = user.get(db=db, id=current_user.supervisor_id) if current_user.supervisor_id else None
        if supervisor:
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
        reviewer_id=current_user.id
    )
    
    # Update Google Sheet status
    google_sheets_service.update_timesheet_status(timesheet.google_sheet_url, "approved")
    
    # Send notification to staff member
    try:
        staff_member = user.get(db=db, id=timesheet.user_id)
        if staff_member:
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
        reviewer_id=current_user.id
    )
    
    # Update Google Sheet status
    google_sheets_service.update_timesheet_status(timesheet.google_sheet_url, "rejected")
    
    # Send notification to staff member
    try:
        staff_member = user.get(db=db, id=timesheet.user_id)
        if staff_member:
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
    
    # Get data from Google Sheets
    timesheet_data = google_sheets_service.get_timesheet_data(timesheet.google_sheet_url)
    
    return {
        "timesheet_id": timesheet_id,
        "sheet_url": timesheet.google_sheet_url,
        "status": timesheet.status,
        "data": timesheet_data,
        "total_hours": sum(float(entry.get('total_hours', 0)) for entry in timesheet_data)
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