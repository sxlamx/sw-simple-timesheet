from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_admin, get_current_supervisor_or_admin
from app.models.user import SupervisorDirectReport, User
from app.schemas.supervisor_mapping import (
    SupervisorMapping, SupervisorMappingCreate, SupervisorMappingUpdate
)
from pydantic import BaseModel

router = APIRouter()

class SupervisorMappingResponse(BaseModel):
    id: int
    supervisor_id: int
    direct_report_id: int
    supervisor_name: str
    direct_report_name: str
    created_at: str
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[SupervisorMappingResponse])
async def get_supervisor_mappings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_supervisor_or_admin)
):
    """Get all supervisor mappings"""
    mappings = db.query(SupervisorDirectReport).all()
    
    # Enrich with user names
    result = []
    for mapping in mappings:
        supervisor = db.query(User).filter(User.id == mapping.supervisor_id).first()
        direct_report = db.query(User).filter(User.id == mapping.direct_report_id).first()
        
        result.append(SupervisorMappingResponse(
            id=mapping.id,
            supervisor_id=mapping.supervisor_id,
            direct_report_id=mapping.direct_report_id,
            supervisor_name=supervisor.full_name if supervisor else "Unknown",
            direct_report_name=direct_report.full_name if direct_report else "Unknown",
            created_at=mapping.created_at.isoformat() if mapping.created_at else ""
        ))
    
    return result

@router.post("/", response_model=SupervisorMappingResponse)
async def create_supervisor_mapping(
    mapping_data: SupervisorMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new supervisor mapping (admin only)"""
    
    # Check if supervisor exists and has supervisor/admin role
    supervisor = db.query(User).filter(User.id == mapping_data.supervisor_id).first()
    if not supervisor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supervisor not found"
        )
    
    if supervisor.role not in ["SUPERVISOR", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected user is not a supervisor or admin"
        )
    
    # Check if direct report exists
    direct_report = db.query(User).filter(User.id == mapping_data.direct_report_id).first()
    if not direct_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Direct report user not found"
        )
    
    # Check if mapping already exists
    existing_mapping = db.query(SupervisorDirectReport).filter(
        SupervisorDirectReport.supervisor_id == mapping_data.supervisor_id,
        SupervisorDirectReport.direct_report_id == mapping_data.direct_report_id
    ).first()
    
    if existing_mapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mapping already exists"
        )
    
    # Create new mapping
    new_mapping = SupervisorDirectReport(
        supervisor_id=mapping_data.supervisor_id,
        direct_report_id=mapping_data.direct_report_id
    )
    
    db.add(new_mapping)
    db.commit()
    db.refresh(new_mapping)
    
    # Also update the traditional supervisor_id field for backward compatibility
    direct_report.supervisor_id = mapping_data.supervisor_id
    db.commit()
    
    return SupervisorMappingResponse(
        id=new_mapping.id,
        supervisor_id=new_mapping.supervisor_id,
        direct_report_id=new_mapping.direct_report_id,
        supervisor_name=supervisor.full_name,
        direct_report_name=direct_report.full_name,
        created_at=new_mapping.created_at.isoformat() if new_mapping.created_at else ""
    )

@router.put("/{mapping_id}", response_model=SupervisorMappingResponse)
async def update_supervisor_mapping(
    mapping_id: int,
    mapping_data: SupervisorMappingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a supervisor mapping (admin only)"""
    
    # Get existing mapping
    mapping = db.query(SupervisorDirectReport).filter(SupervisorDirectReport.id == mapping_id).first()
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supervisor mapping not found"
        )
    
    # Update mapping
    if mapping_data.supervisor_id is not None:
        supervisor = db.query(User).filter(User.id == mapping_data.supervisor_id).first()
        if not supervisor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supervisor not found"
            )
        mapping.supervisor_id = mapping_data.supervisor_id
    
    if mapping_data.direct_report_id is not None:
        direct_report = db.query(User).filter(User.id == mapping_data.direct_report_id).first()
        if not direct_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Direct report user not found"
            )
        mapping.direct_report_id = mapping_data.direct_report_id
    
    db.commit()
    db.refresh(mapping)
    
    # Update traditional supervisor_id field
    direct_report = db.query(User).filter(User.id == mapping.direct_report_id).first()
    if direct_report:
        direct_report.supervisor_id = mapping.supervisor_id
        db.commit()
    
    # Get updated user names
    supervisor = db.query(User).filter(User.id == mapping.supervisor_id).first()
    direct_report = db.query(User).filter(User.id == mapping.direct_report_id).first()
    
    return SupervisorMappingResponse(
        id=mapping.id,
        supervisor_id=mapping.supervisor_id,
        direct_report_id=mapping.direct_report_id,
        supervisor_name=supervisor.full_name if supervisor else "Unknown",
        direct_report_name=direct_report.full_name if direct_report else "Unknown",
        created_at=mapping.created_at.isoformat() if mapping.created_at else ""
    )

@router.delete("/{mapping_id}")
async def delete_supervisor_mapping(
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a supervisor mapping (admin only)"""
    
    mapping = db.query(SupervisorDirectReport).filter(SupervisorDirectReport.id == mapping_id).first()
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supervisor mapping not found"
        )
    
    # Remove traditional supervisor_id reference
    direct_report = db.query(User).filter(User.id == mapping.direct_report_id).first()
    if direct_report:
        direct_report.supervisor_id = None
        db.commit()
    
    # Delete mapping
    db.delete(mapping)
    db.commit()
    
    return {"message": "Supervisor mapping deleted successfully"}

@router.get("/user/{user_id}/direct-reports", response_model=List[dict])
async def get_user_direct_reports(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_supervisor_or_admin)
):
    """Get direct reports for a specific user"""
    
    # Only allow users to see their own direct reports, or admins to see anyone's
    if current_user.role != "ADMIN" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these direct reports"
        )
    
    direct_reports = db.query(User).join(
        SupervisorDirectReport, User.id == SupervisorDirectReport.direct_report_id
    ).filter(SupervisorDirectReport.supervisor_id == user_id).all()
    
    return [
        {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active
        }
        for user in direct_reports
    ]