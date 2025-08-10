from typing import Optional, Union
from datetime import datetime
from pydantic import BaseModel, EmailStr
from enum import Enum

class UserRole(str, Enum):
    STAFF = "staff"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"

class EntryType(str, Enum):
    NORMAL = "normal"
    OVERTIME = "overtime"
    HOLIDAY = "holiday"

class SiteBase(BaseModel):
    name: str
    description: Optional[str] = None
    domain: Optional[str] = None
    is_active: bool = True

class Site(SiteBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    is_active: bool = True
    role: UserRole = UserRole.STAFF
    is_supervisor: bool = False  # Keep for backward compatibility
    department: Optional[str] = None

class UserCreate(UserBase):
    google_id: Optional[str] = None
    keycloak_id: Optional[str] = None
    profile_picture: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None
    is_supervisor: Optional[bool] = None
    department: Optional[str] = None
    supervisor_id: Optional[int] = None
    google_sheet_id: Optional[str] = None

class User(UserBase):
    id: int
    site_id: int
    google_id: Optional[str] = None
    keycloak_id: Optional[str] = None
    profile_picture: Optional[str] = None
    supervisor_id: Optional[int] = None
    google_sheet_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TimesheetSubmissionBase(BaseModel):
    period_start: datetime
    period_end: datetime
    google_sheet_url: Optional[str] = None
    total_hours: Optional[int] = None

class TimesheetSubmissionCreate(TimesheetSubmissionBase):
    pass

class TimesheetSubmissionUpdate(BaseModel):
    status: Optional[str] = None
    review_notes: Optional[str] = None
    total_hours: Optional[int] = None

class TimesheetSubmission(TimesheetSubmissionBase):
    id: int
    site_id: int
    user_id: int
    status: str
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    reviewed_by_name: Optional[str] = None
    review_notes: Optional[str] = None

    class Config:
        from_attributes = True

class DepartmentBase(BaseModel):
    name: str
    description: Optional[str] = None

class DepartmentCreate(DepartmentBase):
    supervisor_id: Optional[int] = None

class Department(DepartmentBase):
    id: int
    supervisor_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class TimesheetEntryBase(BaseModel):
    date: Union[datetime, str]
    start_time: Optional[Union[datetime, str]] = None
    end_time: Optional[Union[datetime, str]] = None
    break_duration: int = 0  # in minutes
    total_hours: float = 0.0
    project_id: Optional[int] = None
    project: Optional[str] = None  # Keep for backward compatibility
    task_description: Optional[str] = None
    entry_type: EntryType = EntryType.NORMAL
    hourly_rate: Optional[float] = None

class TimesheetEntryCreate(TimesheetEntryBase):
    submission_id: int

class TimesheetEntryUpdate(BaseModel):
    date: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    break_duration: Optional[int] = None
    total_hours: Optional[float] = None
    project_id: Optional[int] = None
    project: Optional[str] = None
    task_description: Optional[str] = None
    entry_type: Optional[EntryType] = None
    hourly_rate: Optional[float] = None

class TimesheetEntry(TimesheetEntryBase):
    id: int
    submission_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SiteRateConfigBase(BaseModel):
    entry_type: EntryType
    hourly_rate: float
    is_active: bool = True

class SiteRateConfigCreate(SiteRateConfigBase):
    site_id: int

class SiteRateConfigUpdate(BaseModel):
    hourly_rate: Optional[float] = None
    is_active: Optional[bool] = None

class SiteRateConfig(SiteRateConfigBase):
    id: int
    site_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class NotificationBase(BaseModel):
    title: str
    message: str
    notification_type: str  # approval, comment, reminder, system
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None

class NotificationCreate(NotificationBase):
    site_id: int
    user_id: int

class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None

class Notification(NotificationBase):
    id: int
    site_id: int
    user_id: int
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True