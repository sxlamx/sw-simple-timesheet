from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from datetime import datetime, timedelta, date
from calendar import monthrange

from app.api.deps import get_db, get_current_user, get_site_from_user
from app.crud.user import timesheet_submission, user as user_crud
from app.crud.project import project as project_crud
from app.crud.notification import notification as notification_crud
from app.models.user import User as UserModel, TimesheetSubmission, Project, Notification
from app.schemas.user import User

router = APIRouter()

@router.get("/staff/overview")
def get_staff_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get comprehensive dashboard overview for staff members"""
    site_id = get_site_from_user(current_user)
    
    # Current month stats
    current_date = datetime.now()
    month_start = date(current_date.year, current_date.month, 1)
    _, last_day = monthrange(current_date.year, current_date.month)
    month_end = date(current_date.year, current_date.month, last_day)
    
    # Get current month timesheets
    current_month_timesheets = db.query(TimesheetSubmission).filter(
        TimesheetSubmission.user_id == current_user.id,
        TimesheetSubmission.site_id == site_id,
        TimesheetSubmission.period_start >= month_start,
        TimesheetSubmission.period_start <= month_end
    ).all()
    
    # Calculate current month metrics
    current_month_hours = sum(ts.total_hours or 0 for ts in current_month_timesheets)
    submitted_timesheets = len([ts for ts in current_month_timesheets if ts.status != 'draft'])
    approved_timesheets = len([ts for ts in current_month_timesheets if ts.status == 'approved'])
    pending_timesheets = len([ts for ts in current_month_timesheets if ts.status == 'pending'])
    draft_timesheets = len([ts for ts in current_month_timesheets if ts.status == 'draft'])
    
    # Get unread notifications count
    unread_notifications = notification_crud.get_unread_count(
        db=db, user_id=current_user.id, site_id=site_id
    )
    
    # Get user's active projects
    user_projects = project_crud.get_user_projects(
        db=db, user_id=current_user.id, site_id=site_id
    )
    
    # Calculate completion rate
    completion_rate = (approved_timesheets / submitted_timesheets * 100) if submitted_timesheets > 0 else 0
    
    # Upcoming deadlines (next 7 days - mock for now, could be enhanced)
    upcoming_deadlines = []
    for project in user_projects:
        if project.end_date and project.end_date > current_date.date():
            days_remaining = (project.end_date - current_date.date()).days
            if days_remaining <= 7:
                upcoming_deadlines.append({
                    "type": "project_deadline",
                    "title": f"Project: {project.name}",
                    "description": f"Project deadline in {days_remaining} day(s)",
                    "date": project.end_date,
                    "priority": "high" if days_remaining <= 3 else "medium"
                })
    
    # Add timesheet submission reminders
    if draft_timesheets > 0:
        upcoming_deadlines.append({
            "type": "timesheet_reminder", 
            "title": "Pending Timesheet Submissions",
            "description": f"{draft_timesheets} draft timesheet(s) need to be submitted",
            "date": current_date.date(),
            "priority": "high"
        })
    
    return {
        "current_month": {
            "month": current_date.strftime('%B %Y'),
            "total_hours": current_month_hours,
            "submitted_timesheets": submitted_timesheets,
            "approved_timesheets": approved_timesheets,
            "pending_timesheets": pending_timesheets,
            "draft_timesheets": draft_timesheets,
            "completion_rate": round(completion_rate, 1)
        },
        "notifications": {
            "unread_count": unread_notifications
        },
        "projects": {
            "active_count": len(user_projects),
            "projects": [{"id": p.id, "name": p.name, "description": p.description} for p in user_projects[:5]]
        },
        "upcoming_deadlines": sorted(upcoming_deadlines, key=lambda x: x['date'])[:10],
        "quick_stats": {
            "average_hours_per_week": round(current_month_hours / 4, 1) if current_month_hours > 0 else 0,
            "productivity_trend": "stable",  # Could be enhanced with historical data
            "goal_progress": 85  # Mock goal progress - could be enhanced
        }
    }

@router.get("/staff/performance-metrics")  
def get_staff_performance_metrics(
    months: int = Query(default=6, le=12, ge=1),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get detailed performance metrics for staff member"""
    site_id = get_site_from_user(current_user)
    
    # Get historical data for the specified months
    current_date = datetime.now()
    monthly_data = []
    
    for i in range(months):
        target_date = current_date - timedelta(days=30 * i)
        month_start = date(target_date.year, target_date.month, 1)
        _, last_day = monthrange(target_date.year, target_date.month)
        month_end = date(target_date.year, target_date.month, last_day)
        
        # Get timesheets for this month
        month_timesheets = db.query(TimesheetSubmission).filter(
            TimesheetSubmission.user_id == current_user.id,
            TimesheetSubmission.site_id == site_id,
            TimesheetSubmission.period_start >= month_start,
            TimesheetSubmission.period_start <= month_end
        ).all()
        
        total_hours = sum(ts.total_hours or 0 for ts in month_timesheets)
        submitted_count = len([ts for ts in month_timesheets if ts.status != 'draft'])
        approved_count = len([ts for ts in month_timesheets if ts.status == 'approved'])
        on_time_submissions = len([
            ts for ts in month_timesheets 
            if ts.status != 'draft' and ts.submitted_at and 
               ts.submitted_at.day <= 5  # Assume deadline is 5th of month
        ])
        
        monthly_data.append({
            "month": target_date.strftime('%B %Y'),
            "month_code": target_date.strftime('%Y-%m'),
            "total_hours": total_hours,
            "submitted_timesheets": submitted_count,
            "approved_timesheets": approved_count,
            "approval_rate": round((approved_count / submitted_count * 100) if submitted_count > 0 else 0, 1),
            "on_time_submissions": on_time_submissions,
            "punctuality_rate": round((on_time_submissions / submitted_count * 100) if submitted_count > 0 else 0, 1),
            "average_hours_per_timesheet": round(total_hours / submitted_count, 1) if submitted_count > 0 else 0
        })
    
    # Calculate overall metrics
    total_hours_all = sum(m["total_hours"] for m in monthly_data)
    total_submitted = sum(m["submitted_timesheets"] for m in monthly_data) 
    total_approved = sum(m["approved_timesheets"] for m in monthly_data)
    total_on_time = sum(m["on_time_submissions"] for m in monthly_data)
    
    return {
        "period": f"Last {months} months",
        "monthly_breakdown": list(reversed(monthly_data)),
        "overall_metrics": {
            "total_hours": total_hours_all,
            "total_submissions": total_submitted,
            "overall_approval_rate": round((total_approved / total_submitted * 100) if total_submitted > 0 else 0, 1),
            "overall_punctuality_rate": round((total_on_time / total_submitted * 100) if total_submitted > 0 else 0, 1),
            "average_monthly_hours": round(total_hours_all / months, 1),
            "consistency_score": 90  # Mock score - could calculate actual variance
        },
        "achievements": [
            {
                "title": "Consistent Performer",
                "description": "Maintained regular timesheet submissions",
                "earned": total_submitted >= months * 4
            },
            {
                "title": "High Approval Rate", 
                "description": "90%+ approval rate maintained",
                "earned": (total_approved / total_submitted * 100) >= 90 if total_submitted > 0 else False
            },
            {
                "title": "Punctuality Expert",
                "description": "Timely submissions",
                "earned": (total_on_time / total_submitted * 100) >= 80 if total_submitted > 0 else False
            }
        ]
    }

@router.get("/staff/goals")
def get_staff_goals(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get staff member goals and progress tracking"""
    site_id = get_site_from_user(current_user)
    
    # Mock goals system - in a real implementation, these would be stored in database
    current_date = datetime.now()
    current_month_start = date(current_date.year, current_date.month, 1)
    
    # Get current month data for progress calculation
    current_month_timesheets = db.query(TimesheetSubmission).filter(
        TimesheetSubmission.user_id == current_user.id,
        TimesheetSubmission.site_id == site_id,
        TimesheetSubmission.period_start >= current_month_start
    ).all()
    
    current_hours = sum(ts.total_hours or 0 for ts in current_month_timesheets)
    submitted_count = len([ts for ts in current_month_timesheets if ts.status != 'draft'])
    approved_count = len([ts for ts in current_month_timesheets if ts.status == 'approved'])
    
    goals = [
        {
            "id": "monthly_hours",
            "title": "Monthly Hours Target",
            "description": "Complete 160 hours this month",
            "type": "hours",
            "target": 160,
            "current": current_hours,
            "progress": min(round((current_hours / 160) * 100, 1), 100),
            "status": "on_track" if current_hours >= 120 else "behind",
            "deadline": date(current_date.year, current_date.month, 
                           monthrange(current_date.year, current_date.month)[1]),
            "category": "productivity"
        },
        {
            "id": "submission_consistency",
            "title": "Timely Submissions",
            "description": "Submit all timesheets on time this month",
            "type": "percentage",
            "target": 100,
            "current": (submitted_count / 4) * 100 if submitted_count <= 4 else 100,  # Assuming weekly submissions
            "progress": min((submitted_count / 4) * 100, 100) if submitted_count <= 4 else 100,
            "status": "completed" if submitted_count >= 4 else "in_progress",
            "deadline": current_month_start + timedelta(days=32),
            "category": "compliance"
        },
        {
            "id": "approval_rate",
            "title": "High Approval Rate",
            "description": "Maintain 95%+ approval rate",
            "type": "percentage", 
            "target": 95,
            "current": round((approved_count / submitted_count) * 100, 1) if submitted_count > 0 else 0,
            "progress": min(round((approved_count / submitted_count) * 100, 1), 100) if submitted_count > 0 else 0,
            "status": "completed" if (approved_count / submitted_count) * 100 >= 95 and submitted_count > 0 else "in_progress",
            "deadline": date(current_date.year, 12, 31),  # Year-end goal
            "category": "quality"
        }
    ]
    
    # Calculate overall progress
    total_progress = sum(goal["progress"] for goal in goals)
    overall_progress = round(total_progress / len(goals), 1)
    
    return {
        "period": current_date.strftime('%B %Y'),
        "overall_progress": overall_progress,
        "goals": goals,
        "categories": {
            "productivity": [g for g in goals if g["category"] == "productivity"],
            "compliance": [g for g in goals if g["category"] == "compliance"], 
            "quality": [g for g in goals if g["category"] == "quality"]
        },
        "recommendations": [
            "Continue maintaining consistent timesheet submissions",
            "Focus on detailed task descriptions for better approval rates",
            "Consider project time allocation for better productivity metrics"
        ]
    }

@router.get("/supervisor/team-overview")
def get_supervisor_team_overview(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Enhanced supervisor dashboard with comprehensive team monitoring"""
    from app.crud.user import supervisor_direct_report
    
    site_id = get_site_from_user(current_user)
    
    # Get team members
    team_members = supervisor_direct_report.get_direct_reports(
        db=db, supervisor_id=current_user.id, site_id=site_id
    )
    
    if not team_members:
        return {"message": "No team members found", "team_size": 0}
    
    # Current month analysis
    current_date = datetime.now()
    month_start = date(current_date.year, current_date.month, 1)
    
    team_stats = []
    total_team_hours = 0
    total_pending_approvals = 0
    
    for member in team_members:
        # Get member's current month timesheets
        member_timesheets = db.query(TimesheetSubmission).filter(
            TimesheetSubmission.user_id == member.id,
            TimesheetSubmission.site_id == site_id,
            TimesheetSubmission.period_start >= month_start
        ).all()
        
        member_hours = sum(ts.total_hours or 0 for ts in member_timesheets)
        pending_count = len([ts for ts in member_timesheets if ts.status == 'pending'])
        approved_count = len([ts for ts in member_timesheets if ts.status == 'approved'])
        total_submissions = len([ts for ts in member_timesheets if ts.status != 'draft'])
        
        total_team_hours += member_hours
        total_pending_approvals += pending_count
        
        # Performance indicators
        performance_score = 0
        if total_submissions > 0:
            approval_rate = (approved_count / total_submissions) * 100
            if approval_rate >= 95: performance_score += 30
            elif approval_rate >= 85: performance_score += 20
            else: performance_score += 10
            
        if member_hours >= 140: performance_score += 40  # Good hours
        elif member_hours >= 120: performance_score += 30
        else: performance_score += 20
        
        if pending_count == 0: performance_score += 30  # No pending items
        elif pending_count <= 1: performance_score += 20
        else: performance_score += 10
        
        team_stats.append({
            "user_id": member.id,
            "name": member.full_name,
            "email": member.email,
            "current_month_hours": member_hours,
            "pending_approvals": pending_count,
            "approved_timesheets": approved_count,
            "total_submissions": total_submissions,
            "approval_rate": round((approved_count / total_submissions) * 100, 1) if total_submissions > 0 else 0,
            "performance_score": performance_score,
            "status": "excellent" if performance_score >= 90 else "good" if performance_score >= 70 else "needs_attention"
        })
    
    # Sort by performance score
    team_stats.sort(key=lambda x: x['performance_score'], reverse=True)
    
    # Team-wide metrics
    avg_team_hours = round(total_team_hours / len(team_members), 1)
    high_performers = len([m for m in team_stats if m['status'] == 'excellent'])
    needs_attention = len([m for m in team_stats if m['status'] == 'needs_attention'])
    
    return {
        "overview": {
            "team_size": len(team_members),
            "total_hours_this_month": total_team_hours,
            "average_hours_per_member": avg_team_hours,
            "pending_approvals": total_pending_approvals,
            "high_performers": high_performers,
            "needs_attention": needs_attention
        },
        "team_members": team_stats,
        "alerts": [
            {
                "type": "warning",
                "message": f"{needs_attention} team member(s) need attention",
                "priority": "high"
            } if needs_attention > 0 else None,
            {
                "type": "info", 
                "message": f"{total_pending_approvals} timesheet(s) pending your approval",
                "priority": "medium"
            } if total_pending_approvals > 0 else None,
            {
                "type": "success",
                "message": f"{high_performers} team member(s) performing excellently",
                "priority": "low"
            } if high_performers > 0 else None
        ],
        "recommendations": [
            f"Review pending approvals for {total_pending_approvals} timesheet(s)" if total_pending_approvals > 0 else None,
            f"Check in with {needs_attention} team member(s) who may need support" if needs_attention > 0 else None,
            "Team performance is strong - consider recognizing top performers" if high_performers >= len(team_members) * 0.5 else None
        ]
    }