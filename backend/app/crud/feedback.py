from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from app.models.user import Feedback, FeedbackResponse, User
from app.schemas.feedback import FeedbackCreate, FeedbackUpdate, FeedbackResponseCreate

class CRUDFeedback:
    def create(self, db: Session, obj_in: FeedbackCreate, user_id: int) -> Feedback:
        db_obj = Feedback(
            user_id=user_id,
            category=obj_in.category,
            type=obj_in.type,
            title=obj_in.title,
            description=obj_in.description,
            rating=obj_in.rating
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get(self, db: Session, id: int) -> Optional[Feedback]:
        return db.query(Feedback).filter(Feedback.id == id).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        user_id: Optional[int] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Feedback]:
        query = db.query(Feedback)
        
        if user_id:
            query = query.filter(Feedback.user_id == user_id)
        if category:
            query = query.filter(Feedback.category == category)
        if status:
            query = query.filter(Feedback.status == status)
        if priority:
            query = query.filter(Feedback.priority == priority)
            
        return query.order_by(desc(Feedback.created_at)).offset(skip).limit(limit).all()
    
    def update(self, db: Session, db_obj: Feedback, obj_in: FeedbackUpdate) -> Feedback:
        update_data = obj_in.dict(exclude_unset=True)
        
        # Handle resolved_at timestamp
        if 'status' in update_data and update_data['status'] == 'resolved':
            from datetime import datetime
            update_data['resolved_at'] = datetime.utcnow()
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
            
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, id: int) -> Feedback:
        obj = db.query(Feedback).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj
    
    def get_feedback_with_user_info(self, db: Session, feedback_id: int) -> Optional[Feedback]:
        """Get feedback with user information populated"""
        feedback = db.query(Feedback).join(User, Feedback.user_id == User.id).filter(Feedback.id == feedback_id).first()
        if feedback:
            # Populate user name
            feedback.user_name = feedback.user.full_name if feedback.user else None
            # Populate assigned user name if exists
            if feedback.assigned_to:
                assigned_user = db.query(User).filter(User.id == feedback.assigned_to).first()
                feedback.assigned_user_name = assigned_user.full_name if assigned_user else None
        return feedback
    
    def get_feedback_stats(self, db: Session, user_id: Optional[int] = None) -> dict:
        """Get comprehensive feedback statistics"""
        query = db.query(Feedback)
        if user_id:
            query = query.filter(Feedback.user_id == user_id)
        
        total_feedback = query.count()
        
        # Stats by category
        category_stats = db.query(
            Feedback.category, 
            func.count(Feedback.id)
        ).group_by(Feedback.category)
        
        if user_id:
            category_stats = category_stats.filter(Feedback.user_id == user_id)
        
        by_category = dict(category_stats.all())
        
        # Stats by status
        status_stats = db.query(
            Feedback.status,
            func.count(Feedback.id)
        ).group_by(Feedback.status)
        
        if user_id:
            status_stats = status_stats.filter(Feedback.user_id == user_id)
            
        by_status = dict(status_stats.all())
        
        # Stats by priority
        priority_stats = db.query(
            Feedback.priority,
            func.count(Feedback.id)
        ).group_by(Feedback.priority)
        
        if user_id:
            priority_stats = priority_stats.filter(Feedback.user_id == user_id)
            
        by_priority = dict(priority_stats.all())
        
        # Average rating
        rating_query = db.query(func.avg(Feedback.rating)).filter(Feedback.rating.isnot(None))
        if user_id:
            rating_query = rating_query.filter(Feedback.user_id == user_id)
        
        average_rating = rating_query.scalar()
        
        return {
            "total_feedback": total_feedback,
            "by_category": by_category,
            "by_status": by_status,
            "by_priority": by_priority,
            "average_rating": float(average_rating) if average_rating else None
        }


class CRUDFeedbackResponse:
    def create(self, db: Session, obj_in: FeedbackResponseCreate, feedback_id: int, user_id: int) -> FeedbackResponse:
        db_obj = FeedbackResponse(
            feedback_id=feedback_id,
            user_id=user_id,
            message=obj_in.message,
            is_internal=obj_in.is_internal
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_by_feedback(self, db: Session, feedback_id: int) -> List[FeedbackResponse]:
        return db.query(FeedbackResponse).filter(
            FeedbackResponse.feedback_id == feedback_id
        ).order_by(FeedbackResponse.created_at).all()
    
    def get_responses_with_user_info(self, db: Session, feedback_id: int) -> List[FeedbackResponse]:
        """Get responses with user information populated"""
        responses = db.query(FeedbackResponse).join(User).filter(
            FeedbackResponse.feedback_id == feedback_id
        ).order_by(FeedbackResponse.created_at).all()
        
        for response in responses:
            response.user_name = response.user.full_name if response.user else None
            
        return responses
    
    def delete(self, db: Session, id: int) -> FeedbackResponse:
        obj = db.query(FeedbackResponse).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj


# Global instances
feedback = CRUDFeedback()
feedback_response = CRUDFeedbackResponse()