#!/usr/bin/env python3
"""
Create comprehensive demo data for the timesheet application
including projects, rate configurations, notifications, and sample entries
"""

import sys
import os
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session

# Add the backend directory to Python path
sys.path.append('/Volumes/X9Pro/github/sw-simple-timesheet/backend')

from app.core.database import get_db
from app.models.user import (
    Site, User, Project, ProjectMember, SiteRateConfig, 
    TimesheetSubmission, TimesheetEntry, Notification
)
from app.schemas.project import ProjectCreate, ProjectMemberCreate
from app.schemas.user import SiteRateConfigCreate, NotificationCreate
from app.crud.project import project as project_crud, project_member as project_member_crud
from app.crud.notification import notification as notification_crud

def create_demo_data():
    """Create comprehensive demo data"""
    
    # Get database session
    db = next(get_db())
    
    print("🎯 Creating demo data for timesheet application...")
    
    try:
        # Get the demo site
        demo_site = db.query(Site).filter(Site.name == "Demo Site").first()
        if not demo_site:
            print("❌ Demo site not found. Please run create_demo_site.py first.")
            return
        
        print(f"✅ Using demo site: {demo_site.name} (ID: {demo_site.id})")
        
        # Get users
        admin_user = db.query(User).filter(
            User.email == "admin@demo.com",
            User.site_id == demo_site.id
        ).first()
        
        supervisor_user = db.query(User).filter(
            User.email == "supervisor@demo.com", 
            User.site_id == demo_site.id
        ).first()
        
        from app.models.user import UserRole
        staff_users = db.query(User).filter(
            User.site_id == demo_site.id,
            User.role == UserRole.STAFF
        ).all()
        
        if not admin_user or not supervisor_user or not staff_users:
            print("❌ Required users not found. Please ensure demo users exist.")
            return
            
        print(f"✅ Found {len(staff_users)} staff users, 1 supervisor, 1 admin")
        
        # 1. Create Site Rate Configurations
        print("\n📊 Creating site rate configurations...")
        
        rate_configs = [
            {"entry_type": "normal", "hourly_rate": 25.0},
            {"entry_type": "overtime", "hourly_rate": 37.5},  # 1.5x normal rate
            {"entry_type": "holiday", "hourly_rate": 50.0}    # 2x normal rate
        ]
        
        for config in rate_configs:
            existing = db.query(SiteRateConfig).filter(
                SiteRateConfig.site_id == demo_site.id,
                SiteRateConfig.entry_type == config["entry_type"]
            ).first()
            
            if not existing:
                rate_config = SiteRateConfig(
                    site_id=demo_site.id,
                    entry_type=config["entry_type"],
                    hourly_rate=config["hourly_rate"],
                    is_active=True
                )
                db.add(rate_config)
                print(f"   ✅ Created {config['entry_type']} rate: ${config['hourly_rate']}/hour")
        
        # 2. Create Demo Projects
        print("\n🏗️ Creating demo projects...")
        
        demo_projects = [
            {
                "name": "Website Redesign",
                "description": "Complete overhaul of company website with modern design and improved UX",
                "objectives": "Increase conversion rate by 25% and improve user engagement metrics",
                "start_date": date.today() - timedelta(days=60),
                "end_date": date.today() + timedelta(days=30),
                "project_manager_id": supervisor_user.id
            },
            {
                "name": "Mobile App Development", 
                "description": "Native iOS and Android app for customer portal",
                "objectives": "Launch mobile app with core features and 4+ star rating",
                "start_date": date.today() - timedelta(days=45),
                "end_date": date.today() + timedelta(days=90),
                "project_manager_id": supervisor_user.id
            },
            {
                "name": "Database Migration",
                "description": "Migrate legacy database to PostgreSQL with improved performance",
                "objectives": "Complete migration with zero downtime and 50% performance improvement",
                "start_date": date.today() - timedelta(days=30),
                "end_date": date.today() + timedelta(days=45),
                "project_manager_id": admin_user.id
            },
            {
                "name": "Customer Support Portal",
                "description": "Self-service portal for customer support and documentation",
                "objectives": "Reduce support tickets by 40% and improve customer satisfaction",
                "start_date": date.today() - timedelta(days=15),
                "end_date": date.today() + timedelta(days=120),
                "project_manager_id": supervisor_user.id
            },
            {
                "name": "Security Audit & Compliance",
                "description": "Comprehensive security review and SOC2 compliance preparation", 
                "objectives": "Pass SOC2 audit and implement security best practices",
                "start_date": date.today() - timedelta(days=10),
                "end_date": date.today() + timedelta(days=60),
                "project_manager_id": admin_user.id
            }
        ]
        
        created_projects = []
        for project_data in demo_projects:
            existing_project = db.query(Project).filter(
                Project.name == project_data["name"],
                Project.site_id == demo_site.id
            ).first()
            
            if not existing_project:
                project = Project(
                    site_id=demo_site.id,
                    **project_data
                )
                db.add(project)
                db.flush()  # Get the ID
                created_projects.append(project)
                print(f"   ✅ Created project: {project.name}")
            else:
                created_projects.append(existing_project)
                print(f"   ✅ Using existing project: {existing_project.name}")
        
        # 3. Assign Users to Projects
        print("\n👥 Assigning users to projects...")
        
        for i, project in enumerate(created_projects):
            # Assign different staff members to different projects
            assigned_staff = staff_users[i % len(staff_users):(i % len(staff_users)) + 2]  # 1-2 staff per project
            
            for staff in assigned_staff:
                existing_membership = db.query(ProjectMember).filter(
                    ProjectMember.project_id == project.id,
                    ProjectMember.user_id == staff.id,
                    ProjectMember.site_id == demo_site.id
                ).first()
                
                if not existing_membership:
                    membership = ProjectMember(
                        site_id=demo_site.id,
                        project_id=project.id,
                        user_id=staff.id,
                        role="member",
                        is_active=True
                    )
                    db.add(membership)
                    print(f"   ✅ Assigned {staff.full_name} to {project.name}")
        
        # 4. Create Sample Notifications
        print("\n🔔 Creating sample notifications...")
        
        current_date = datetime.now()
        
        # Create notifications for staff members
        notification_templates = [
            {
                "title": "Timesheet Approved",
                "message": "Your timesheet for this week has been approved by your supervisor.",
                "notification_type": "approval",
                "related_entity_type": "timesheet_submission"
            },
            {
                "title": "Project Deadline Reminder",
                "message": f"The {created_projects[0].name} project deadline is approaching in 5 days.",
                "notification_type": "reminder",
                "related_entity_type": "project",
                "related_entity_id": created_projects[0].id
            },
            {
                "title": "New Project Assignment",
                "message": f"You have been assigned to the {created_projects[1].name} project.",
                "notification_type": "system",
                "related_entity_type": "project",
                "related_entity_id": created_projects[1].id
            },
            {
                "title": "Monthly Hours Goal Achieved",
                "message": "Congratulations! You've reached your monthly hours goal of 160 hours.",
                "notification_type": "system"
            }
        ]
        
        for i, staff in enumerate(staff_users[:3]):  # Create notifications for first 3 staff
            for j, template in enumerate(notification_templates):
                notification = Notification(
                    site_id=demo_site.id,
                    user_id=staff.id,
                    is_read=j < 2,  # Mark first 2 as read
                    created_at=current_date - timedelta(days=j),
                    read_at=current_date - timedelta(hours=2) if j < 2 else None,
                    **template
                )
                db.add(notification)
        
        # Create notifications for supervisor
        supervisor_notifications = [
            {
                "title": "Pending Timesheet Approvals",
                "message": f"You have 3 timesheet submissions pending your approval.",
                "notification_type": "approval"
            },
            {
                "title": "Team Performance Report",
                "message": "Your team's monthly performance report is now available.",
                "notification_type": "system"
            }
        ]
        
        for template in supervisor_notifications:
            notification = Notification(
                site_id=demo_site.id,
                user_id=supervisor_user.id,
                is_read=False,
                **template
            )
            db.add(notification)
            
        print(f"   ✅ Created notifications for {len(staff_users)} staff and supervisor")
        
        # 5. Create Sample Timesheet Data
        print("\n📝 Creating sample timesheet entries...")
        
        # Create timesheets for current month for each staff member
        current_month_start = date(current_date.year, current_date.month, 1)
        
        for staff in staff_users[:2]:  # Create detailed data for first 2 staff
            # Create a timesheet submission
            timesheet = TimesheetSubmission(
                site_id=demo_site.id,
                user_id=staff.id,
                period_start=current_month_start,
                period_end=current_month_start + timedelta(days=6),  # Week 1
                status="approved",
                submitted_at=current_date - timedelta(days=3),
                reviewed_at=current_date - timedelta(days=1),
                reviewed_by=supervisor_user.id,
                reviewed_by_name=supervisor_user.full_name,
                review_notes="Good work this week!",
                total_hours=40
            )
            db.add(timesheet)
            db.flush()
            
            # Add timesheet entries
            work_days = [current_month_start + timedelta(days=i) for i in range(5)]  # Mon-Fri
            
            for i, work_day in enumerate(work_days):
                project = created_projects[i % len(created_projects)]
                
                entry = TimesheetEntry(
                    site_id=demo_site.id,
                    submission_id=timesheet.id,
                    date=work_day,
                    start_time=datetime.combine(work_day, datetime.min.time().replace(hour=9)),
                    end_time=datetime.combine(work_day, datetime.min.time().replace(hour=17)),
                    break_duration=60,  # 1 hour break
                    total_hours=8.0,
                    project_id=project.id,
                    project=project.name,
                    task_description=f"Development work on {project.name}",
                    entry_type="normal",
                    hourly_rate=25.0
                )
                db.add(entry)
            
            print(f"   ✅ Created timesheet with entries for {staff.full_name}")
        
        # Commit all changes
        db.commit()
        print("\n✅ All demo data created successfully!")
        
        # Summary
        print("\n📋 Demo Data Summary:")
        print(f"   • Site: {demo_site.name}")
        print(f"   • Rate Configurations: {len(rate_configs)}")
        print(f"   • Projects: {len(created_projects)}")
        print(f"   • Project Memberships: {len(staff_users) * 2}")  # Approximate
        print(f"   • Notifications: {len(staff_users) * len(notification_templates) + len(supervisor_notifications)}")
        print(f"   • Sample Timesheets: 2 with detailed entries")
        
        print("\n🎉 Demo data setup complete! You can now:")
        print("   • Test project management features")
        print("   • View notifications in the dashboard")
        print("   • Test timesheet approval workflows")
        print("   • Explore enhanced dashboard analytics")
        
    except Exception as e:
        print(f"❌ Error creating demo data: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    create_demo_data()