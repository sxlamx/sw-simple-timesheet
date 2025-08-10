from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class SupervisorMappingBase(BaseModel):
    supervisor_id: int
    direct_report_id: int

class SupervisorMappingCreate(SupervisorMappingBase):
    pass

class SupervisorMappingUpdate(BaseModel):
    supervisor_id: Optional[int] = None
    direct_report_id: Optional[int] = None

class SupervisorMapping(SupervisorMappingBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True