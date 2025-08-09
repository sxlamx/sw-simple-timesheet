from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    is_active: bool = True
    is_supervisor: bool = False
    department: Optional[str] = None

class UserCreate(UserBase):
    google_id: str
    profile_picture: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_supervisor: Optional[bool] = None
    department: Optional[str] = None
    supervisor_id: Optional[int] = None
    google_sheet_id: Optional[str] = None

class User(UserBase):
    id: int
    google_id: str
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
    google_sheet_url: str
    total_hours: Optional[int] = None

class TimesheetSubmissionCreate(TimesheetSubmissionBase):
    pass

class TimesheetSubmissionUpdate(BaseModel):
    status: Optional[str] = None
    review_notes: Optional[str] = None
    total_hours: Optional[int] = None

class TimesheetSubmission(TimesheetSubmissionBase):
    id: int
    user_id: int
    status: str
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None
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