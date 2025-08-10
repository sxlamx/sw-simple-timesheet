from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.user import User, TimesheetSubmission, Department, SupervisorDirectReport
from app.schemas.user import UserCreate, UserUpdate, TimesheetSubmissionCreate, TimesheetSubmissionUpdate

class CRUDUser:
    def get(self, db: Session, id: int, site_id: int = None) -> Optional[User]:
        query = db.query(User).filter(User.id == id)
        if site_id:
            query = query.filter(User.site_id == site_id)
        return query.first()
    
    def get_by_email(self, db: Session, email: str, site_id: int = None) -> Optional[User]:
        query = db.query(User).filter(User.email == email)
        if site_id:
            query = query.filter(User.site_id == site_id)
        return query.first()
    
    def get_by_google_id(self, db: Session, google_id: str, site_id: int = None) -> Optional[User]:
        query = db.query(User).filter(User.google_id == google_id)
        if site_id:
            query = query.filter(User.site_id == site_id)
        return query.first()
    
    def get_by_keycloak_id(self, db: Session, keycloak_id: str, site_id: int = None) -> Optional[User]:
        query = db.query(User).filter(User.keycloak_id == keycloak_id)
        if site_id:
            query = query.filter(User.site_id == site_id)
        return query.first()
    
    def get_multi(self, db: Session, site_id: int, skip: int = 0, limit: int = 100) -> List[User]:
        return db.query(User).filter(User.site_id == site_id).offset(skip).limit(limit).all()
    
    def get_staff_by_supervisor(self, db: Session, supervisor_id: int, site_id: int) -> List[User]:
        # Use the supervisor_direct_reports mapping table
        return db.query(User).join(
            SupervisorDirectReport, User.id == SupervisorDirectReport.direct_report_id
        ).filter(
            SupervisorDirectReport.supervisor_id == supervisor_id,
            SupervisorDirectReport.site_id == site_id,
            User.site_id == site_id
        ).all()
    
    def get_direct_reports(self, db: Session, supervisor_id: int, site_id: int) -> List[User]:
        """Get all direct reports for a supervisor using the mapping table"""
        return self.get_staff_by_supervisor(db, supervisor_id, site_id)
    
    def create(self, db: Session, obj_in: UserCreate, site_id: int) -> User:
        db_obj = User(
            site_id=site_id,
            email=obj_in.email,
            full_name=obj_in.full_name,
            google_id=getattr(obj_in, 'google_id', None),
            keycloak_id=getattr(obj_in, 'keycloak_id', None),
            profile_picture=getattr(obj_in, 'profile_picture', None),
            is_active=getattr(obj_in, 'is_active', True),
            role=getattr(obj_in, 'role', 'STAFF'),
            is_supervisor=getattr(obj_in, 'is_supervisor', False),
            department=getattr(obj_in, 'department', None),
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(self, db: Session, db_obj: User, obj_in: UserUpdate) -> User:
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, id: int) -> User:
        obj = db.query(User).get(id)
        db.delete(obj)
        db.commit()
        return obj

class CRUDTimesheetSubmission:
    def get(self, db: Session, id: int, site_id: int) -> Optional[TimesheetSubmission]:
        return db.query(TimesheetSubmission).filter(
            TimesheetSubmission.id == id,
            TimesheetSubmission.site_id == site_id
        ).first()
    
    def get_by_user(self, db: Session, user_id: int, site_id: int, skip: int = 0, limit: int = 100) -> List[TimesheetSubmission]:
        return db.query(TimesheetSubmission).filter(
            TimesheetSubmission.user_id == user_id,
            TimesheetSubmission.site_id == site_id
        ).offset(skip).limit(limit).all()
    
    def get_pending_for_supervisor(self, db: Session, supervisor_id: int, site_id: int) -> List[TimesheetSubmission]:
        # Use the supervisor_direct_reports mapping table
        return db.query(TimesheetSubmission).join(
            User, TimesheetSubmission.user_id == User.id
        ).join(
            SupervisorDirectReport, User.id == SupervisorDirectReport.direct_report_id
        ).filter(
            SupervisorDirectReport.supervisor_id == supervisor_id,
            SupervisorDirectReport.site_id == site_id,
            TimesheetSubmission.status == "pending",
            TimesheetSubmission.site_id == site_id
        ).all()
    
    def get_all_for_supervisor(self, db: Session, supervisor_id: int, site_id: int, status: str = None, skip: int = 0, limit: int = 100) -> List[TimesheetSubmission]:
        """Get all timesheets for supervisor's team with optional status filter"""
        query = db.query(TimesheetSubmission).join(
            User, TimesheetSubmission.user_id == User.id
        ).filter(
            User.supervisor_id == supervisor_id,
            User.site_id == site_id,
            TimesheetSubmission.site_id == site_id
        )
        
        if status:
            query = query.filter(TimesheetSubmission.status == status)
            
        return query.offset(skip).limit(limit).all()
    
    def get_team_statistics(self, db: Session, supervisor_id: int) -> dict:
        """Get aggregated statistics for supervisor's team"""
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        # Get all team timesheets
        team_timesheets = db.query(TimesheetSubmission).join(User, TimesheetSubmission.user_id == User.id).filter(
            User.supervisor_id == supervisor_id
        ).all()
        
        # Calculate statistics
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        total_timesheets = len(team_timesheets)
        pending_count = len([t for t in team_timesheets if t.status == "pending"])
        approved_count = len([t for t in team_timesheets if t.status == "approved"])
        rejected_count = len([t for t in team_timesheets if t.status == "rejected"])
        
        # Current month hours
        current_month_hours = sum([
            t.total_hours or 0 for t in team_timesheets 
            if t.period_start and t.period_start.month == current_month 
            and t.period_start.year == current_year
        ])
        
        # Overdue count (pending for more than 7 days)
        seven_days_ago = datetime.now() - timedelta(days=7)
        overdue_count = len([
            t for t in team_timesheets 
            if t.status == "pending" and t.submitted_at and t.submitted_at < seven_days_ago
        ])
        
        return {
            "total_timesheets": total_timesheets,
            "pending_count": pending_count,
            "approved_count": approved_count,
            "rejected_count": rejected_count,
            "current_month_hours": current_month_hours,
            "overdue_count": overdue_count
        }
    
    def create(self, db: Session, obj_in: TimesheetSubmissionCreate, user_id: int, site_id: int) -> TimesheetSubmission:
        db_obj = TimesheetSubmission(
            site_id=site_id,
            user_id=user_id,
            period_start=obj_in.period_start,
            period_end=obj_in.period_end,
            google_sheet_url=getattr(obj_in, 'google_sheet_url', None),
            total_hours=getattr(obj_in, 'total_hours', None),
            status="draft"  # Default status for new timesheets
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(self, db: Session, db_obj: TimesheetSubmission, obj_in: TimesheetSubmissionUpdate, reviewer_id: int = None, reviewer_name: str = None) -> TimesheetSubmission:
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        if reviewer_id:
            db_obj.reviewed_by = reviewer_id
        if reviewer_name:
            db_obj.reviewed_by_name = reviewer_name
            if obj_in.status in ["approved", "rejected"]:
                from datetime import datetime
                db_obj.reviewed_at = datetime.utcnow()
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

user = CRUDUser()
timesheet_submission = CRUDTimesheetSubmission()