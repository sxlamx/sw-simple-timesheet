from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime
from app.models.user import Notification
from app.schemas.user import NotificationCreate, NotificationUpdate

class CRUDNotification:
    def create(self, db: Session, obj_in: NotificationCreate) -> Notification:
        db_obj = Notification(**obj_in.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, id: int, site_id: int) -> Optional[Notification]:
        return db.query(Notification).filter(
            Notification.id == id,
            Notification.site_id == site_id
        ).first()

    def get_by_user(
        self, 
        db: Session, 
        user_id: int, 
        site_id: int, 
        skip: int = 0, 
        limit: int = 100,
        unread_only: bool = False
    ) -> List[Notification]:
        query = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.site_id == site_id
        )
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
            
        return query.order_by(desc(Notification.created_at)).offset(skip).limit(limit).all()

    def get_unread_count(self, db: Session, user_id: int, site_id: int) -> int:
        return db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.site_id == site_id,
            Notification.is_read == False
        ).count()

    def mark_as_read(self, db: Session, notification_id: int, user_id: int, site_id: int) -> Optional[Notification]:
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id,
            Notification.site_id == site_id
        ).first()
        
        if notification and not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.add(notification)
            db.commit()
            db.refresh(notification)
        
        return notification

    def mark_all_as_read(self, db: Session, user_id: int, site_id: int) -> int:
        updated_count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.site_id == site_id,
            Notification.is_read == False
        ).update({
            "is_read": True,
            "read_at": datetime.utcnow()
        })
        db.commit()
        return updated_count

    def delete(self, db: Session, notification_id: int, user_id: int, site_id: int) -> bool:
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id,
            Notification.site_id == site_id
        ).first()
        
        if notification:
            db.delete(notification)
            db.commit()
            return True
        return False

    def create_timesheet_approval_notification(
        self, 
        db: Session, 
        user_id: int, 
        site_id: int, 
        timesheet_id: int, 
        status: str
    ) -> Notification:
        """Create notification for timesheet approval/rejection"""
        title = "Timesheet Approved" if status == "approved" else "Timesheet Rejected"
        message = f"Your timesheet submission has been {status}."
        
        notification_in = NotificationCreate(
            site_id=site_id,
            user_id=user_id,
            title=title,
            message=message,
            notification_type="approval",
            related_entity_type="timesheet_submission",
            related_entity_id=timesheet_id
        )
        
        return self.create(db=db, obj_in=notification_in)

    def create_pending_approval_notification(
        self, 
        db: Session, 
        supervisor_id: int, 
        site_id: int, 
        timesheet_id: int,
        submitter_name: str
    ) -> Notification:
        """Create notification for supervisor about pending timesheet approval"""
        notification_in = NotificationCreate(
            site_id=site_id,
            user_id=supervisor_id,
            title="Timesheet Pending Approval",
            message=f"New timesheet from {submitter_name} is awaiting your approval.",
            notification_type="approval",
            related_entity_type="timesheet_submission",
            related_entity_id=timesheet_id
        )
        
        return self.create(db=db, obj_in=notification_in)

    def create_system_notification(
        self, 
        db: Session, 
        user_id: int, 
        site_id: int, 
        title: str, 
        message: str
    ) -> Notification:
        """Create system notification"""
        notification_in = NotificationCreate(
            site_id=site_id,
            user_id=user_id,
            title=title,
            message=message,
            notification_type="system"
        )
        
        return self.create(db=db, obj_in=notification_in)

notification = CRUDNotification()