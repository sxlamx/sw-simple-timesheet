from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_supervisor, get_site_from_user
from app.models.user import User as UserModel
from app.schemas.user import Notification, NotificationCreate, NotificationUpdate
from app.crud.notification import notification as notification_crud
from app.services.notification_service import notification_service

router = APIRouter()

@router.get("/", response_model=List[Notification])
def get_notifications(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = Query(default=50, le=100),
    unread_only: bool = False,
    current_user: UserModel = Depends(get_current_user)
):
    """Get notifications for the current user"""
    site_id = get_site_from_user(current_user)
    notifications = notification_crud.get_by_user(
        db=db, 
        user_id=current_user.id, 
        site_id=site_id, 
        skip=skip, 
        limit=limit,
        unread_only=unread_only
    )
    return notifications

@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get count of unread notifications"""
    site_id = get_site_from_user(current_user)
    count = notification_crud.get_unread_count(
        db=db, 
        user_id=current_user.id, 
        site_id=site_id
    )
    return {"unread_count": count}

@router.put("/{notification_id}/read", response_model=Notification)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Mark a specific notification as read"""
    site_id = get_site_from_user(current_user)
    notification = notification_crud.mark_as_read(
        db=db, 
        notification_id=notification_id, 
        user_id=current_user.id, 
        site_id=site_id
    )
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return notification

@router.put("/mark-all-read")
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Mark all notifications as read for the current user"""
    site_id = get_site_from_user(current_user)
    updated_count = notification_crud.mark_all_as_read(
        db=db, 
        user_id=current_user.id, 
        site_id=site_id
    )
    
    return {"message": f"Marked {updated_count} notifications as read"}

@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Delete a specific notification"""
    site_id = get_site_from_user(current_user)
    success = notification_crud.delete(
        db=db, 
        notification_id=notification_id, 
        user_id=current_user.id, 
        site_id=site_id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification deleted successfully"}

@router.post("/send-reminders")
async def send_reminder_notifications(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_supervisor)
):
    """Send reminder notifications for overdue timesheets (supervisor only)"""
    
    # Run notification service in background
    background_tasks.add_task(notification_service.send_reminder_notifications, db)
    
    return {"message": "Reminder notifications are being sent in the background"}

@router.post("/test-email")
async def test_email_notification(
    to_email: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_supervisor)
):
    """Test email notification system (supervisor only)"""
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background-color: #1976d2; color: white; padding: 20px; text-align: center; }
            .content { padding: 20px; background-color: #f9f9f9; }
            .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📧 Test Email</h1>
            </div>
            <div class="content">
                <p>Hello!</p>
                <p>This is a test email from the Simple Timesheet notification system.</p>
                <p>If you received this email, the notification system is working correctly.</p>
                <p><strong>Sent by:</strong> """ + current_user.full_name + """</p>
            </div>
            <div class="footer">
                <p>Simple Timesheet - Test Notification</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    success = notification_service._send_email(
        to_email=to_email,
        subject="Simple Timesheet - Test Email",
        html_content=html_content
    )
    
    if success:
        return {"message": f"Test email sent successfully to {to_email}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test email. Please check SMTP configuration."
        )