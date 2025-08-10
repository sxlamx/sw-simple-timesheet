from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.user import Project, ProjectMember
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectMemberCreate, ProjectMemberUpdate

class CRUDProject:
    def create(self, db: Session, obj_in: ProjectCreate) -> Project:
        db_obj = Project(**obj_in.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, id: int, site_id: int) -> Optional[Project]:
        return db.query(Project).filter(
            Project.id == id,
            Project.site_id == site_id
        ).first()

    def get_multi(
        self, db: Session, site_id: int, skip: int = 0, limit: int = 100, active_only: bool = True
    ) -> List[Project]:
        query = db.query(Project).filter(Project.site_id == site_id)
        if active_only:
            query = query.filter(Project.is_active == True)
        return query.offset(skip).limit(limit).all()

    def get_by_name(self, db: Session, name: str, site_id: int) -> Optional[Project]:
        return db.query(Project).filter(
            Project.name == name,
            Project.site_id == site_id
        ).first()

    def get_user_projects(self, db: Session, user_id: int, site_id: int) -> List[Project]:
        """Get all projects a user is a member of"""
        return db.query(Project).join(ProjectMember).filter(
            ProjectMember.user_id == user_id,
            ProjectMember.site_id == site_id,
            ProjectMember.is_active == True,
            Project.is_active == True
        ).all()

    def update(self, db: Session, db_obj: Project, obj_in: ProjectUpdate) -> Project:
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int, site_id: int) -> Optional[Project]:
        obj = self.get(db=db, id=id, site_id=site_id)
        if obj:
            # Soft delete
            obj.is_active = False
            db.add(obj)
            db.commit()
            return obj
        return None

class CRUDProjectMember:
    def create(self, db: Session, obj_in: ProjectMemberCreate) -> ProjectMember:
        db_obj = ProjectMember(**obj_in.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, id: int, site_id: int) -> Optional[ProjectMember]:
        return db.query(ProjectMember).filter(
            ProjectMember.id == id,
            ProjectMember.site_id == site_id
        ).first()

    def get_by_project_and_user(
        self, db: Session, project_id: int, user_id: int, site_id: int
    ) -> Optional[ProjectMember]:
        return db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
            ProjectMember.site_id == site_id
        ).first()

    def get_project_members(
        self, db: Session, project_id: int, site_id: int, active_only: bool = True
    ) -> List[ProjectMember]:
        query = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.site_id == site_id
        )
        if active_only:
            query = query.filter(ProjectMember.is_active == True)
        return query.all()

    def get_user_memberships(
        self, db: Session, user_id: int, site_id: int, active_only: bool = True
    ) -> List[ProjectMember]:
        query = db.query(ProjectMember).filter(
            ProjectMember.user_id == user_id,
            ProjectMember.site_id == site_id
        )
        if active_only:
            query = query.filter(ProjectMember.is_active == True)
        return query.all()

    def update(self, db: Session, db_obj: ProjectMember, obj_in: ProjectMemberUpdate) -> ProjectMember:
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, project_id: int, user_id: int, site_id: int) -> Optional[ProjectMember]:
        obj = self.get_by_project_and_user(
            db=db, project_id=project_id, user_id=user_id, site_id=site_id
        )
        if obj:
            # Soft delete
            obj.is_active = False
            db.add(obj)
            db.commit()
            return obj
        return None

project = CRUDProject()
project_member = CRUDProjectMember()