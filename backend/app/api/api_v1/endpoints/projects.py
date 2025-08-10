from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_site_from_user
from app.crud.project import project as project_crud, project_member as project_member_crud
from app.models.user import User
from app.schemas.project import (
    Project,
    ProjectCreate, 
    ProjectUpdate,
    ProjectMember,
    ProjectMemberCreate,
    ProjectMemberUpdate,
    ProjectWithMembers
)

router = APIRouter()

@router.get("/", response_model=List[Project])
def read_projects(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=1000),
    active_only: bool = True,
    current_user: User = Depends(get_current_user)
):
    """Get all projects for the user's site"""
    site_id = get_site_from_user(current_user)
    projects = project_crud.get_multi(
        db=db, site_id=site_id, skip=skip, limit=limit, active_only=active_only
    )
    return projects

@router.get("/my-projects", response_model=List[Project])
def read_my_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get projects the current user is a member of"""
    site_id = get_site_from_user(current_user)
    projects = project_crud.get_user_projects(
        db=db, user_id=current_user.id, site_id=site_id
    )
    return projects

@router.post("/", response_model=Project)
def create_project(
    *,
    db: Session = Depends(get_db),
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new project (Admin/Supervisor only)"""
    if current_user.role.value not in ["admin", "supervisor"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    site_id = get_site_from_user(current_user)
    project_in.site_id = site_id
    
    # Check if project name already exists
    if project_crud.get_by_name(db=db, name=project_in.name, site_id=site_id):
        raise HTTPException(status_code=400, detail="Project name already exists")
    
    project = project_crud.create(db=db, obj_in=project_in)
    return project

@router.get("/{project_id}", response_model=ProjectWithMembers)
def read_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific project with its members"""
    site_id = get_site_from_user(current_user)
    project = project_crud.get(db=db, id=project_id, site_id=site_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get project members
    members = project_member_crud.get_project_members(
        db=db, project_id=project_id, site_id=site_id
    )
    
    # Return project with members
    project_dict = project.__dict__.copy()
    project_dict["members"] = members
    return project_dict

@router.put("/{project_id}", response_model=Project)
def update_project(
    *,
    db: Session = Depends(get_db),
    project_id: int,
    project_in: ProjectUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a project (Admin/Supervisor only)"""
    if current_user.role.value not in ["admin", "supervisor"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    site_id = get_site_from_user(current_user)
    project = project_crud.get(db=db, id=project_id, site_id=site_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if new name conflicts with existing project
    if project_in.name and project_in.name != project.name:
        if project_crud.get_by_name(db=db, name=project_in.name, site_id=site_id):
            raise HTTPException(status_code=400, detail="Project name already exists")
    
    project = project_crud.update(db=db, db_obj=project, obj_in=project_in)
    return project

@router.delete("/{project_id}", response_model=Project)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a project (Admin only)"""
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    site_id = get_site_from_user(current_user)
    project = project_crud.delete(db=db, id=project_id, site_id=site_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

# Project Member endpoints
@router.post("/{project_id}/members", response_model=ProjectMember)
def add_project_member(
    *,
    db: Session = Depends(get_db),
    project_id: int,
    member_in: ProjectMemberCreate,
    current_user: User = Depends(get_current_user)
):
    """Add a member to a project (Admin/Supervisor only)"""
    if current_user.role.value not in ["admin", "supervisor"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    site_id = get_site_from_user(current_user)
    
    # Check if project exists
    project = project_crud.get(db=db, id=project_id, site_id=site_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if user is already a member
    existing_member = project_member_crud.get_by_project_and_user(
        db=db, project_id=project_id, user_id=member_in.user_id, site_id=site_id
    )
    if existing_member and existing_member.is_active:
        raise HTTPException(status_code=400, detail="User is already a project member")
    
    # Set the project_id and site_id
    member_in.project_id = project_id
    member_in.site_id = site_id
    
    # If the member existed but was inactive, reactivate them
    if existing_member:
        member_in_update = ProjectMemberUpdate(
            role=member_in.role, 
            is_active=True
        )
        member = project_member_crud.update(db=db, db_obj=existing_member, obj_in=member_in_update)
    else:
        member = project_member_crud.create(db=db, obj_in=member_in)
    
    return member

@router.get("/{project_id}/members", response_model=List[ProjectMember])
def read_project_members(
    project_id: int,
    db: Session = Depends(get_db),
    active_only: bool = True,
    current_user: User = Depends(get_current_user)
):
    """Get all members of a project"""
    site_id = get_site_from_user(current_user)
    
    # Check if project exists
    project = project_crud.get(db=db, id=project_id, site_id=site_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    members = project_member_crud.get_project_members(
        db=db, project_id=project_id, site_id=site_id, active_only=active_only
    )
    return members

@router.put("/{project_id}/members/{user_id}", response_model=ProjectMember)
def update_project_member(
    *,
    db: Session = Depends(get_db),
    project_id: int,
    user_id: int,
    member_in: ProjectMemberUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a project member's role (Admin/Supervisor only)"""
    if current_user.role.value not in ["admin", "supervisor"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    site_id = get_site_from_user(current_user)
    member = project_member_crud.get_by_project_and_user(
        db=db, project_id=project_id, user_id=user_id, site_id=site_id
    )
    if not member:
        raise HTTPException(status_code=404, detail="Project member not found")
    
    member = project_member_crud.update(db=db, db_obj=member, obj_in=member_in)
    return member

@router.delete("/{project_id}/members/{user_id}", response_model=ProjectMember)
def remove_project_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a member from a project (Admin/Supervisor only)"""
    if current_user.role.value not in ["admin", "supervisor"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    site_id = get_site_from_user(current_user)
    member = project_member_crud.remove(
        db=db, project_id=project_id, user_id=user_id, site_id=site_id
    )
    if not member:
        raise HTTPException(status_code=404, detail="Project member not found")
    return member