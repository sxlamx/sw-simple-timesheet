import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Optional
import logging
from jinja2 import Template
from app.core.config import settings
from app.models.user import User, TimesheetSubmission
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.smtp_server = getattr(settings, 'SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_username = getattr(settings, 'SMTP_USERNAME', '')
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', '')
        self.from_email = getattr(settings, 'FROM_EMAIL', 'noreply@simpletimesheet.com')
        
    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None):
        """Send email using SMTP"""
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP credentials not configured. Email not sent.")
                return False
                
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
                
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_timesheet_submitted_notification(self, timesheet: TimesheetSubmission, staff_user: User, supervisor: User):
        """Notify supervisor when a timesheet is submitted"""
        subject = f"Timesheet Submitted for Review - {staff_user.full_name}"
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #1976d2; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background-color: #f9f9f9; }
                .button { background-color: #1976d2; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; margin: 10px 0; }
                .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Timesheet Submitted for Review</h1>
                </div>
                <div class="content">
                    <p>Hello {{ supervisor_name }},</p>
                    <p>{{ staff_name }} has submitted a timesheet for your review:</p>
                    
                    <ul>
                        <li><strong>Staff Member:</strong> {{ staff_name }}</li>
                        <li><strong>Period:</strong> {{ period }}</li>
                        <li><strong>Total Hours:</strong> {{ total_hours }}</li>
                        <li><strong>Submitted:</strong> {{ submitted_date }}</li>
                    </ul>
                    
                    <p>Please review and approve or reject this timesheet at your earliest convenience.</p>
                    
                    <a href="{{ app_url }}" class="button">Review Timesheet</a>
                </div>
                <div class="footer">
                    <p>Simple Timesheet - Automated Notification</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        period_str = timesheet.period_start.strftime('%B %Y') if timesheet.period_start else 'Unknown'
        submitted_date = timesheet.submitted_at.strftime('%Y-%m-%d %H:%M') if timesheet.submitted_at else 'Unknown'
        
        template = Template(html_template)
        html_content = template.render(
            supervisor_name=supervisor.full_name,
            staff_name=staff_user.full_name,
            period=period_str,
            total_hours=timesheet.total_hours or 0,
            submitted_date=submitted_date,
            app_url=getattr(settings, 'FRONTEND_URL', 'http://localhost:5185')
        )
        
        return self._send_email(supervisor.email, subject, html_content)
    
    def send_timesheet_approved_notification(self, timesheet: TimesheetSubmission, staff_user: User, supervisor: User):
        """Notify staff when timesheet is approved"""
        subject = f"Timesheet Approved - {timesheet.period_start.strftime('%B %Y') if timesheet.period_start else 'Unknown'}"
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #4caf50; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background-color: #f9f9f9; }
                .success { background-color: #dff0d8; border: 1px solid #d6e9c6; color: #3c763d; padding: 15px; border-radius: 4px; margin: 15px 0; }
                .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Timesheet Approved</h1>
                </div>
                <div class="content">
                    <p>Hello {{ staff_name }},</p>
                    
                    <div class="success">
                        <strong>Great news!</strong> Your timesheet has been approved by {{ supervisor_name }}.
                    </div>
                    
                    <ul>
                        <li><strong>Period:</strong> {{ period }}</li>
                        <li><strong>Total Hours:</strong> {{ total_hours }}</li>
                        <li><strong>Approved by:</strong> {{ supervisor_name }}</li>
                        <li><strong>Approved on:</strong> {{ approved_date }}</li>
                    </ul>
                    
                    {% if review_notes %}
                    <p><strong>Review Notes:</strong></p>
                    <p style="background-color: #e8f4fd; padding: 10px; border-radius: 4px;">{{ review_notes }}</p>
                    {% endif %}
                </div>
                <div class="footer">
                    <p>Simple Timesheet - Automated Notification</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        period_str = timesheet.period_start.strftime('%B %Y') if timesheet.period_start else 'Unknown'
        approved_date = timesheet.reviewed_at.strftime('%Y-%m-%d %H:%M') if timesheet.reviewed_at else 'Unknown'
        
        template = Template(html_template)
        html_content = template.render(
            staff_name=staff_user.full_name,
            supervisor_name=supervisor.full_name,
            period=period_str,
            total_hours=timesheet.total_hours or 0,
            approved_date=approved_date,
            review_notes=timesheet.review_notes
        )
        
        return self._send_email(staff_user.email, subject, html_content)
    
    def send_timesheet_rejected_notification(self, timesheet: TimesheetSubmission, staff_user: User, supervisor: User):
        """Notify staff when timesheet is rejected"""
        subject = f"Timesheet Requires Revision - {timesheet.period_start.strftime('%B %Y') if timesheet.period_start else 'Unknown'}"
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #f44336; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background-color: #f9f9f9; }
                .warning { background-color: #fcf8e3; border: 1px solid #faebcc; color: #8a6d3b; padding: 15px; border-radius: 4px; margin: 15px 0; }
                .button { background-color: #1976d2; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; margin: 10px 0; }
                .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📝 Timesheet Requires Revision</h1>
                </div>
                <div class="content">
                    <p>Hello {{ staff_name }},</p>
                    
                    <div class="warning">
                        Your timesheet has been reviewed and requires some changes before approval.
                    </div>
                    
                    <ul>
                        <li><strong>Period:</strong> {{ period }}</li>
                        <li><strong>Total Hours:</strong> {{ total_hours }}</li>
                        <li><strong>Reviewed by:</strong> {{ supervisor_name }}</li>
                        <li><strong>Reviewed on:</strong> {{ reviewed_date }}</li>
                    </ul>
                    
                    {% if review_notes %}
                    <p><strong>Review Notes:</strong></p>
                    <p style="background-color: #fff2cc; padding: 10px; border-radius: 4px; border-left: 4px solid #ff9800;">{{ review_notes }}</p>
                    {% endif %}
                    
                    <p>Please make the necessary changes and resubmit your timesheet.</p>
                    
                    <a href="{{ app_url }}" class="button">Edit Timesheet</a>
                </div>
                <div class="footer">
                    <p>Simple Timesheet - Automated Notification</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        period_str = timesheet.period_start.strftime('%B %Y') if timesheet.period_start else 'Unknown'
        reviewed_date = timesheet.reviewed_at.strftime('%Y-%m-%d %H:%M') if timesheet.reviewed_at else 'Unknown'
        
        template = Template(html_template)
        html_content = template.render(
            staff_name=staff_user.full_name,
            supervisor_name=supervisor.full_name,
            period=period_str,
            total_hours=timesheet.total_hours or 0,
            reviewed_date=reviewed_date,
            review_notes=timesheet.review_notes,
            app_url=getattr(settings, 'FRONTEND_URL', 'http://localhost:5185')
        )
        
        return self._send_email(staff_user.email, subject, html_content)
    
    def send_reminder_notifications(self, db: Session):
        """Send reminder notifications for overdue timesheets"""
        from app.crud.user import user, timesheet_submission
        from datetime import datetime, timedelta
        
        # Get all pending timesheets older than 3 days
        three_days_ago = datetime.now() - timedelta(days=3)
        
        # This would need a more sophisticated query in a real implementation
        # For now, we'll get all pending and filter
        all_supervisors = user.get_multi(db, limit=1000)
        supervisors = [u for u in all_supervisors if u.is_supervisor]
        
        reminder_count = 0
        
        for supervisor in supervisors:
            pending_timesheets = timesheet_submission.get_pending_for_supervisor(db, supervisor.id)
            overdue_timesheets = [
                ts for ts in pending_timesheets 
                if ts.submitted_at and ts.submitted_at < three_days_ago
            ]
            
            if overdue_timesheets:
                self._send_reminder_to_supervisor(supervisor, overdue_timesheets, db)
                reminder_count += 1
        
        logger.info(f"Sent {reminder_count} reminder notifications")
        return reminder_count
    
    def _send_reminder_to_supervisor(self, supervisor: User, overdue_timesheets: List[TimesheetSubmission], db: Session):
        """Send reminder email to supervisor about overdue reviews"""
        from app.crud.user import user
        
        subject = f"Reminder: {len(overdue_timesheets)} Timesheets Pending Review"
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #ff9800; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background-color: #f9f9f9; }
                .timesheet-item { background-color: white; border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 4px; }
                .button { background-color: #1976d2; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; margin: 10px 0; }
                .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⏰ Timesheet Review Reminder</h1>
                </div>
                <div class="content">
                    <p>Hello {{ supervisor_name }},</p>
                    
                    <p>You have {{ count }} timesheet(s) that have been waiting for review for more than 3 days:</p>
                    
                    {% for timesheet in timesheets %}
                    <div class="timesheet-item">
                        <strong>{{ timesheet.staff_name }}</strong><br>
                        Period: {{ timesheet.period }}<br>
                        Hours: {{ timesheet.total_hours }}<br>
                        Submitted: {{ timesheet.days_ago }} days ago
                    </div>
                    {% endfor %}
                    
                    <p>Please review these timesheets at your earliest convenience to keep the approval process on track.</p>
                    
                    <a href="{{ app_url }}" class="button">Review Timesheets</a>
                </div>
                <div class="footer">
                    <p>Simple Timesheet - Automated Reminder</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Prepare timesheet data for template
        timesheet_data = []
        for ts in overdue_timesheets:
            staff_member = user.get(db, ts.user_id)
            days_ago = (datetime.now() - ts.submitted_at).days if ts.submitted_at else 0
            timesheet_data.append({
                'staff_name': staff_member.full_name if staff_member else 'Unknown',
                'period': ts.period_start.strftime('%B %Y') if ts.period_start else 'Unknown',
                'total_hours': ts.total_hours or 0,
                'days_ago': days_ago
            })
        
        template = Template(html_template)
        html_content = template.render(
            supervisor_name=supervisor.full_name,
            count=len(overdue_timesheets),
            timesheets=timesheet_data,
            app_url=getattr(settings, 'FRONTEND_URL', 'http://localhost:5185')
        )
        
        return self._send_email(supervisor.email, subject, html_content)

# Global instance
notification_service = NotificationService()