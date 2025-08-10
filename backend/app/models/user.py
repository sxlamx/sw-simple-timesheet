from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, Enum, UniqueConstraint
import enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class UserRole(enum.Enum):
    STAFF = "staff"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"

class EntryType(enum.Enum):
    NORMAL = "normal"
    OVERTIME = "overtime"
    HOLIDAY = "holiday"

class Site(Base):
    __tablename__ = "sites"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    domain = Column(String, nullable=True, index=True)  # For domain-based site assignment
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="site")
    site_members = relationship("SiteMember", back_populates="site")

class SiteMember(Base):
    __tablename__ = "site_members"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.STAFF, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Unique constraint to prevent duplicate memberships
    __table_args__ = (UniqueConstraint('site_id', 'user_id', name='_site_user_uc'),)
    
    # Relationships
    site = relationship("Site", back_populates="site_members")
    user = relationship("User", back_populates="site_memberships")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)
    email = Column(String, index=True, nullable=False)  # Remove unique constraint for multi-tenancy
    full_name = Column(String, nullable=False)
    google_id = Column(String, index=True, nullable=True)  # Allow null for other auth methods
    keycloak_id = Column(String, index=True, nullable=True)  # For Keycloak authentication
    profile_picture = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.STAFF, nullable=False)
    is_supervisor = Column(Boolean, default=False)  # Keep for backward compatibility
    department = Column(String, nullable=True)
    supervisor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    google_sheet_id = Column(String, nullable=True)  # Individual timesheet Google Sheet
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Unique constraint for email within a site
    __table_args__ = (UniqueConstraint('site_id', 'email', name='_site_email_uc'),)
    
    # Relationships
    site = relationship("Site", back_populates="users")
    site_memberships = relationship("SiteMember", back_populates="user")
    supervisor = relationship("User", remote_side=[id], backref="staff_members")
    timesheet_submissions = relationship("TimesheetSubmission", foreign_keys="TimesheetSubmission.user_id", back_populates="user")
    
    # Supervisor-Direct Report relationships
    supervised_users = relationship("SupervisorDirectReport", foreign_keys="SupervisorDirectReport.supervisor_id")
    supervisor_mappings = relationship("SupervisorDirectReport", foreign_keys="SupervisorDirectReport.direct_report_id")

class TimesheetSubmission(Base):
    __tablename__ = "timesheet_submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    google_sheet_url = Column(String, nullable=True)  # No longer required
    status = Column(String, default="draft")  # draft, pending, approved, rejected
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(Integer, nullable=True)  # Keep for backward compatibility but no longer FK
    reviewed_by_name = Column(String, nullable=True)  # Store reviewer name directly
    review_notes = Column(String, nullable=True)
    total_hours = Column(Integer, nullable=True)  # Total hours for the period
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="timesheet_submissions")
    entries = relationship("TimesheetEntry", back_populates="submission")

class SupervisorDirectReport(Base):
    __tablename__ = "supervisor_direct_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)
    supervisor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    direct_report_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    supervisor = relationship("User", foreign_keys=[supervisor_id], overlaps="supervised_users")
    direct_report = relationship("User", foreign_keys=[direct_report_id], overlaps="supervisor_mappings")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    objectives = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    project_manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Unique constraint for project name within a site
    __table_args__ = (UniqueConstraint('site_id', 'name', name='_site_project_uc'),)
    
    # Relationships
    project_manager = relationship("User", foreign_keys=[project_manager_id])
    timesheet_entries = relationship("TimesheetEntry", back_populates="project_rel")

class SiteRateConfig(Base):
    __tablename__ = "site_rate_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)
    entry_type = Column(String, nullable=False)
    hourly_rate = Column(Float, nullable=False)  # Default rate for this entry type
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Unique constraint for entry type within a site
    __table_args__ = (UniqueConstraint('site_id', 'entry_type', name='_site_entry_type_rate_uc'),)

class ProjectMember(Base):
    __tablename__ = "project_members"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, default="member")  # member, lead, contributor
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Unique constraint to prevent duplicate project memberships
    __table_args__ = (UniqueConstraint('site_id', 'project_id', 'user_id', name='_site_project_user_uc'),)
    
    # Relationships
    project = relationship("Project")
    user = relationship("User")

class Department(Base):
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    supervisor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Unique constraint for department name within a site
    __table_args__ = (UniqueConstraint('site_id', 'name', name='_site_department_uc'),)
    
    # Relationships
    supervisor = relationship("User")

class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(String, nullable=False)  # 'app', 'feature', 'bug', 'suggestion'
    type = Column(String, nullable=False)  # 'rating', 'comment', 'feature_request'
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    rating = Column(Float, nullable=True)  # 1-5 rating
    status = Column(String, default="open")  # open, in_review, resolved, closed
    priority = Column(String, default="medium")  # low, medium, high, critical
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    assigned_user = relationship("User", foreign_keys=[assigned_to])

class FeedbackResponse(Base):
    __tablename__ = "feedback_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)
    feedback_id = Column(Integer, ForeignKey("feedback.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)  # Internal notes vs user-visible responses
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    feedback = relationship("Feedback")
    user = relationship("User")

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Recipient
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String, nullable=False)  # approval, comment, reminder, system
    related_entity_type = Column(String, nullable=True)  # timesheet_submission, project, etc.
    related_entity_id = Column(Integer, nullable=True)  # ID of the related entity
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User")

class TimesheetEntry(Base):
    __tablename__ = "timesheet_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)
    submission_id = Column(Integer, ForeignKey("timesheet_submissions.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    break_duration = Column(Integer, default=0)  # in minutes
    total_hours = Column(Float, default=0.0)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)  # Link to Project model
    project = Column(String, nullable=True)  # Keep for backward compatibility
    task_description = Column(Text, nullable=True)
    entry_type = Column(String, default="normal")  # normal, overtime, holiday
    hourly_rate = Column(Float, nullable=True)  # For different entry types
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    submission = relationship("TimesheetSubmission", back_populates="entries")
    project_rel = relationship("Project", back_populates="timesheet_entries")