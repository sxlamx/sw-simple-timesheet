from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_supervisor
from app.models.user import User as UserModel
from app.services.notification_service import notification_service

router = APIRouter()

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