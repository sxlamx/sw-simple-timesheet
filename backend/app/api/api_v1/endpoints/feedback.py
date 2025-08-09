from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_supervisor
from app.crud.feedback import feedback, feedback_response
from app.schemas.feedback import (
    Feedback, FeedbackCreate, FeedbackUpdate, FeedbackStats,
    FeedbackResponse, FeedbackResponseCreate
)
from app.models.user import User as UserModel

router = APIRouter()

@router.post("/", response_model=Feedback)
async def create_feedback(
    feedback_data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Create new feedback"""
    feedback_obj = feedback.create(db=db, obj_in=feedback_data, user_id=current_user.id)
    
    # Populate user information
    enriched_feedback = feedback.get_feedback_with_user_info(db=db, feedback_id=feedback_obj.id)
    return enriched_feedback

@router.get("/", response_model=List[Feedback])
async def get_feedback_list(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    my_feedback: bool = Query(False, description="Get only current user's feedback"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get feedback list with optional filters"""
    user_id = current_user.id if my_feedback else None
    
    # Non-supervisors can only see their own feedback
    if not current_user.is_supervisor:
        user_id = current_user.id
    
    feedback_list = feedback.get_multi(
        db=db,
        skip=skip,
        limit=limit,
        user_id=user_id,
        category=category,
        status=status,
        priority=priority
    )
    
    # Enrich with user information
    enriched_feedback = []
    for fb in feedback_list:
        enriched_fb = feedback.get_feedback_with_user_info(db=db, feedback_id=fb.id)
        if enriched_fb:
            enriched_feedback.append(enriched_fb)
    
    return enriched_feedback

@router.get("/{feedback_id}", response_model=Feedback)
async def get_feedback(
    feedback_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get specific feedback by ID"""
    feedback_obj = feedback.get_feedback_with_user_info(db=db, feedback_id=feedback_id)
    
    if not feedback_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )
    
    # Check permissions
    if not current_user.is_supervisor and feedback_obj.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get responses
    responses = feedback_response.get_responses_with_user_info(db=db, feedback_id=feedback_id)
    
    # Filter internal responses for non-supervisors
    if not current_user.is_supervisor:
        responses = [r for r in responses if not r.is_internal]
    
    feedback_obj.responses = responses
    return feedback_obj

@router.put("/{feedback_id}", response_model=Feedback)
async def update_feedback(
    feedback_id: int,
    feedback_update: FeedbackUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Update feedback (supervisors only for most fields, users can update their own title/description)"""
    feedback_obj = feedback.get(db=db, id=feedback_id)
    
    if not feedback_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )
    
    # Permission check
    if not current_user.is_supervisor and feedback_obj.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Restrict fields for non-supervisors
    if not current_user.is_supervisor:
        # Users can only update title, description, and rating of their own feedback
        allowed_updates = FeedbackUpdate(
            title=feedback_update.title,
            description=feedback_update.description,
            rating=feedback_update.rating
        )
        updated_feedback = feedback.update(db=db, db_obj=feedback_obj, obj_in=allowed_updates)
    else:
        updated_feedback = feedback.update(db=db, db_obj=feedback_obj, obj_in=feedback_update)
    
    return feedback.get_feedback_with_user_info(db=db, feedback_id=updated_feedback.id)

@router.delete("/{feedback_id}")
async def delete_feedback(
    feedback_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Delete feedback"""
    feedback_obj = feedback.get(db=db, id=feedback_id)
    
    if not feedback_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )
    
    # Only supervisors or the feedback creator can delete
    if not current_user.is_supervisor and feedback_obj.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    feedback.delete(db=db, id=feedback_id)
    return {"message": "Feedback deleted successfully"}

@router.post("/{feedback_id}/responses", response_model=FeedbackResponse)
async def add_feedback_response(
    feedback_id: int,
    response_data: FeedbackResponseCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Add response to feedback"""
    feedback_obj = feedback.get(db=db, id=feedback_id)
    
    if not feedback_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )
    
    # Check permissions
    if not current_user.is_supervisor and feedback_obj.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Only supervisors can add internal responses
    if response_data.is_internal and not current_user.is_supervisor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only supervisors can add internal responses"
        )
    
    response_obj = feedback_response.create(
        db=db,
        obj_in=response_data,
        feedback_id=feedback_id,
        user_id=current_user.id
    )
    
    # Populate user name
    response_obj.user_name = current_user.full_name
    return response_obj

@router.get("/{feedback_id}/responses", response_model=List[FeedbackResponse])
async def get_feedback_responses(
    feedback_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get responses for feedback"""
    feedback_obj = feedback.get(db=db, id=feedback_id)
    
    if not feedback_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )
    
    # Check permissions
    if not current_user.is_supervisor and feedback_obj.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    responses = feedback_response.get_responses_with_user_info(db=db, feedback_id=feedback_id)
    
    # Filter internal responses for non-supervisors
    if not current_user.is_supervisor:
        responses = [r for r in responses if not r.is_internal]
    
    return responses

@router.get("/stats/overview", response_model=FeedbackStats)
async def get_feedback_stats(
    my_stats: bool = Query(False, description="Get only current user's stats"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get feedback statistics"""
    user_id = current_user.id if my_stats or not current_user.is_supervisor else None
    
    stats_data = feedback.get_feedback_stats(db=db, user_id=user_id)
    
    # Get recent feedback
    recent_feedback = feedback.get_multi(
        db=db,
        skip=0,
        limit=5,
        user_id=user_id
    )
    
    # Enrich recent feedback with user info
    enriched_recent = []
    for fb in recent_feedback:
        enriched_fb = feedback.get_feedback_with_user_info(db=db, feedback_id=fb.id)
        if enriched_fb:
            enriched_recent.append(enriched_fb)
    
    return FeedbackStats(
        **stats_data,
        recent_feedback=enriched_recent
    )