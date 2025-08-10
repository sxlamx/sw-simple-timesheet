from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_supervisor, get_current_admin, get_current_supervisor_or_admin
from app.crud.user import user
from app.schemas.user import User, UserCreate, UserUpdate
from app.models.user import User as UserModel, UserRole

router = APIRouter()

@router.get("/me", response_model=User)
async def get_current_user(
    current_user: UserModel = Depends(get_current_user)
):
    """Get current authenticated user"""
    return current_user

@router.put("/me", response_model=User) 
async def update_current_user(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Update current user profile"""
    updated_user = user.update(db, db_obj=current_user, obj_in=user_update)
    return updated_user

@router.get("/", response_model=List[User])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_supervisor_or_admin)
):
    """Get all users (supervisor/admin only)"""
    users = user.get_multi(db, skip=skip, limit=limit)
    return users

@router.get("/staff", response_model=List[User])
async def get_staff_members(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_supervisor_or_admin)
):
    """Get staff members under current supervisor"""
    staff_members = user.get_staff_by_supervisor(db, supervisor_id=current_user.id)
    return staff_members

@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get user by ID"""
    target_user = user.get(db, id=user_id)
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Users can only see their own profile or supervisors can see their staff
    if (current_user.id != user_id and 
        not current_user.is_supervisor and 
        current_user.id != target_user.supervisor_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return target_user

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_supervisor_or_admin)
):
    """Update user (supervisor/admin only)"""
    target_user = user.get(db, id=user_id)
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Only admins can change roles
    if user_update.role is not None and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can change user roles"
        )
    
    updated_user = user.update(db, db_obj=target_user, obj_in=user_update)
    return updated_user

@router.post("/{user_id}/promote", response_model=User)
async def promote_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin)
):
    """Promote user to supervisor (admin only)"""
    target_user = user.get(db, id=user_id)
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_update = UserUpdate(role=UserRole.SUPERVISOR, is_supervisor=True)
    updated_user = user.update(db, db_obj=target_user, obj_in=user_update)
    return updated_user

@router.post("/{user_id}/demote", response_model=User)
async def demote_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin)
):
    """Demote user to staff (admin only)"""
    target_user = user.get(db, id=user_id)
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_update = UserUpdate(role=UserRole.STAFF, is_supervisor=False)
    updated_user = user.update(db, db_obj=target_user, obj_in=user_update)
    return updated_user

@router.put("/{user_id}/role", response_model=User)
async def change_user_role(
    user_id: int,
    role: UserRole,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_admin)
):
    """Change user role (admin only)"""
    target_user = user.get(db, id=user_id)
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update both role and is_supervisor for compatibility
    is_supervisor = role in [UserRole.SUPERVISOR, UserRole.ADMIN]
    user_update = UserUpdate(role=role, is_supervisor=is_supervisor)
    updated_user = user.update(db, db_obj=target_user, obj_in=user_update)
    return updated_user