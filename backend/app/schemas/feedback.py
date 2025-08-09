from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime

class FeedbackBase(BaseModel):
    category: str
    type: str
    title: str
    description: Optional[str] = None
    rating: Optional[float] = None
    
    @validator('category')
    def validate_category(cls, v):
        allowed_categories = ['app', 'feature', 'bug', 'suggestion']
        if v not in allowed_categories:
            raise ValueError(f'Category must be one of {allowed_categories}')
        return v
    
    @validator('type')
    def validate_type(cls, v):
        allowed_types = ['rating', 'comment', 'feature_request']
        if v not in allowed_types:
            raise ValueError(f'Type must be one of {allowed_types}')
        return v
    
    @validator('rating')
    def validate_rating(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Rating must be between 1 and 5')
        return v

class FeedbackCreate(FeedbackBase):
    pass

class FeedbackUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    rating: Optional[float] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[int] = None
    resolution_notes: Optional[str] = None
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            allowed_statuses = ['open', 'in_review', 'resolved', 'closed']
            if v not in allowed_statuses:
                raise ValueError(f'Status must be one of {allowed_statuses}')
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        if v is not None:
            allowed_priorities = ['low', 'medium', 'high', 'critical']
            if v not in allowed_priorities:
                raise ValueError(f'Priority must be one of {allowed_priorities}')
        return v

class FeedbackResponseBase(BaseModel):
    message: str
    is_internal: bool = False

class FeedbackResponseCreate(FeedbackResponseBase):
    pass

class FeedbackResponse(FeedbackResponseBase):
    id: int
    feedback_id: int
    user_id: int
    user_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class Feedback(FeedbackBase):
    id: int
    user_id: int
    user_name: Optional[str] = None
    status: str
    priority: str
    assigned_to: Optional[int] = None
    assigned_user_name: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    responses: List[FeedbackResponse] = []
    
    class Config:
        from_attributes = True

class FeedbackStats(BaseModel):
    total_feedback: int
    by_category: dict
    by_status: dict
    by_priority: dict
    average_rating: Optional[float] = None
    recent_feedback: List[Feedback] = []