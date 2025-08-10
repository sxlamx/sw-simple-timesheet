from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    objectives: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool = True
    project_manager_id: Optional[int] = None

class ProjectCreate(ProjectBase):
    site_id: int

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    objectives: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    project_manager_id: Optional[int] = None

class Project(ProjectBase):
    id: int
    site_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ProjectMemberBase(BaseModel):
    project_id: int
    user_id: int
    role: str = "member"
    is_active: bool = True

class ProjectMemberCreate(ProjectMemberBase):
    site_id: int

class ProjectMemberUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None

class ProjectMember(ProjectMemberBase):
    id: int
    site_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Extended schemas with relationships
class ProjectWithMembers(Project):
    members: Optional[List[ProjectMember]] = []

class ProjectMemberWithProject(ProjectMember):
    project: Optional[Project] = None