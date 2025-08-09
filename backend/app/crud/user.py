from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.user import User, TimesheetSubmission, Department
from app.schemas.user import UserCreate, UserUpdate, TimesheetSubmissionCreate, TimesheetSubmissionUpdate

class CRUDUser:
    def get(self, db: Session, id: int) -> Optional[User]:
        return db.query(User).filter(User.id == id).first()
    
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()
    
    def get_by_google_id(self, db: Session, google_id: str) -> Optional[User]:
        return db.query(User).filter(User.google_id == google_id).first()
    
    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        return db.query(User).offset(skip).limit(limit).all()
    
    def get_staff_by_supervisor(self, db: Session, supervisor_id: int) -> List[User]:
        return db.query(User).filter(User.supervisor_id == supervisor_id).all()
    
    def create(self, db: Session, obj_in: UserCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            full_name=obj_in.full_name,
            google_id=obj_in.google_id,
            profile_picture=obj_in.profile_picture,
            is_active=obj_in.is_active,
            is_supervisor=obj_in.is_supervisor,
            department=obj_in.department,
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
    def get(self, db: Session, id: int) -> Optional[TimesheetSubmission]:
        return db.query(TimesheetSubmission).filter(TimesheetSubmission.id == id).first()
    
    def get_by_user(self, db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[TimesheetSubmission]:
        return db.query(TimesheetSubmission).filter(TimesheetSubmission.user_id == user_id).offset(skip).limit(limit).all()
    
    def get_pending_for_supervisor(self, db: Session, supervisor_id: int) -> List[TimesheetSubmission]:
        return db.query(TimesheetSubmission).join(User).filter(
            User.supervisor_id == supervisor_id,
            TimesheetSubmission.status == "pending"
        ).all()
    
    def get_all_for_supervisor(self, db: Session, supervisor_id: int, status: str = None, skip: int = 0, limit: int = 100) -> List[TimesheetSubmission]:
        """Get all timesheets for supervisor's team with optional status filter"""
        query = db.query(TimesheetSubmission).join(User).filter(User.supervisor_id == supervisor_id)
        
        if status:
            query = query.filter(TimesheetSubmission.status == status)
            
        return query.offset(skip).limit(limit).all()
    
    def get_team_statistics(self, db: Session, supervisor_id: int) -> dict:
        """Get aggregated statistics for supervisor's team"""
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        # Get all team timesheets
        team_timesheets = db.query(TimesheetSubmission).join(User).filter(
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
    
    def create(self, db: Session, obj_in: TimesheetSubmissionCreate, user_id: int) -> TimesheetSubmission:
        db_obj = TimesheetSubmission(
            user_id=user_id,
            period_start=obj_in.period_start,
            period_end=obj_in.period_end,
            google_sheet_url=obj_in.google_sheet_url,
            total_hours=obj_in.total_hours,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(self, db: Session, db_obj: TimesheetSubmission, obj_in: TimesheetSubmissionUpdate, reviewer_id: int = None) -> TimesheetSubmission:
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        if reviewer_id:
            db_obj.reviewed_by = reviewer_id
            if obj_in.status in ["approved", "rejected"]:
                from datetime import datetime
                db_obj.reviewed_at = datetime.utcnow()
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

user = CRUDUser()
timesheet_submission = CRUDTimesheetSubmission()