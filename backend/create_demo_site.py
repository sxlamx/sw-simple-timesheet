#!/usr/bin/env python3
"""
Script to create demo site and migrate existing users
"""
import os
import sys
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.core.database import SessionLocal, engine
from app.models.user import Site, User, SiteMember, UserRole
from sqlalchemy.orm import Session

def create_demo_site_and_migrate_users():
    """Create demo site and assign all existing users to it"""
    db: Session = SessionLocal()
    
    try:
        print("🌟 Creating Demo Site...")
        
        # Check if demo site already exists
        demo_site = db.query(Site).filter(Site.name == "Demo Site").first()
        if demo_site:
            print(f"✅ Demo site already exists with ID: {demo_site.id}")
        else:
            # Create demo site
            demo_site = Site(
                name="Demo Site",
                description="Demo site for Simple Timesheet application",
                domain="demo.com",
                is_active=True
            )
            db.add(demo_site)
            db.commit()
            db.refresh(demo_site)
            print(f"✅ Created demo site with ID: {demo_site.id}")
        
        # Get all users that don't have a site_id set
        print("\n🔍 Finding users without site assignment...")
        users_without_site = db.query(User).filter(User.site_id == None).all()
        
        if not users_without_site:
            print("ℹ️ No users found without site assignment.")
            
            # Check for users with site_id but not matching any site
            orphaned_users = db.query(User).filter(
                ~db.query(Site).filter(Site.id == User.site_id).exists()
            ).all()
            
            if orphaned_users:
                print(f"🔧 Found {len(orphaned_users)} orphaned users, assigning to demo site...")
                for user in orphaned_users:
                    user.site_id = demo_site.id
                    print(f"  - {user.email} -> Demo Site")
                db.commit()
                print("✅ Orphaned users assigned to demo site")
            else:
                print("✅ All users are properly assigned to sites")
        else:
            print(f"📝 Found {len(users_without_site)} users to assign to demo site:")
            
            # Assign all users without site to demo site
            for user in users_without_site:
                user.site_id = demo_site.id
                print(f"  - {user.email} ({user.full_name}) -> Demo Site")
            
            db.commit()
            print(f"✅ Successfully assigned {len(users_without_site)} users to demo site")
        
        # Create SiteMember records for all users in demo site
        print("\n👥 Creating site memberships...")
        demo_site_users = db.query(User).filter(User.site_id == demo_site.id).all()
        
        for user in demo_site_users:
            # Check if site membership already exists
            existing_membership = db.query(SiteMember).filter(
                SiteMember.site_id == demo_site.id,
                SiteMember.user_id == user.id
            ).first()
            
            if not existing_membership:
                site_member = SiteMember(
                    site_id=demo_site.id,
                    user_id=user.id,
                    role=user.role,  # Use existing role from user
                    is_active=user.is_active
                )
                db.add(site_member)
                print(f"  + Created membership for {user.email} as {user.role.value}")
        
        db.commit()
        print("✅ Site memberships created")
        
        # Create admin user if it doesn't exist
        print("\n👑 Checking for admin user...")
        admin_email = "bonbonxjaggerx@gmail.com"
        admin_user = db.query(User).filter(
            User.email == admin_email,
            User.site_id == demo_site.id
        ).first()
        
        if not admin_user:
            # Check if admin exists in another site or without site
            existing_admin = db.query(User).filter(User.email == admin_email).first()
            
            if existing_admin:
                # Move to demo site
                existing_admin.site_id = demo_site.id
                existing_admin.role = UserRole.ADMIN
                existing_admin.is_supervisor = True
                
                # Create or update site membership
                existing_membership = db.query(SiteMember).filter(
                    SiteMember.user_id == existing_admin.id
                ).first()
                
                if existing_membership:
                    existing_membership.site_id = demo_site.id
                    existing_membership.role = UserRole.ADMIN
                else:
                    site_member = SiteMember(
                        site_id=demo_site.id,
                        user_id=existing_admin.id,
                        role=UserRole.ADMIN,
                        is_active=True
                    )
                    db.add(site_member)
                
                print(f"✅ Moved existing admin user to demo site: {admin_email}")
            else:
                # Create new admin user
                google_id = f"google_admin_{datetime.utcnow().timestamp()}"
                admin_user = User(
                    site_id=demo_site.id,
                    email=admin_email,
                    full_name="Admin User",
                    google_id=google_id,
                    role=UserRole.ADMIN,
                    is_supervisor=True,
                    is_active=True
                )
                db.add(admin_user)
                db.flush()  # Get the ID
                
                # Create site membership
                site_member = SiteMember(
                    site_id=demo_site.id,
                    user_id=admin_user.id,
                    role=UserRole.ADMIN,
                    is_active=True
                )
                db.add(site_member)
                
                print(f"✅ Created new admin user: {admin_email}")
        else:
            print(f"✅ Admin user already exists: {admin_email}")
        
        db.commit()
        
        # Summary
        print("\n📊 SUMMARY:")
        print(f"Demo Site ID: {demo_site.id}")
        print(f"Demo Site Name: {demo_site.name}")
        
        total_users = db.query(User).filter(User.site_id == demo_site.id).count()
        total_memberships = db.query(SiteMember).filter(SiteMember.site_id == demo_site.id).count()
        admin_count = db.query(User).filter(User.site_id == demo_site.id, User.role == UserRole.ADMIN).count()
        supervisor_count = db.query(User).filter(User.site_id == demo_site.id, User.role == UserRole.SUPERVISOR).count()
        staff_count = db.query(User).filter(User.site_id == demo_site.id, User.role == UserRole.STAFF).count()
        
        print(f"Total Users: {total_users}")
        print(f"Total Site Memberships: {total_memberships}")
        print(f"Admins: {admin_count}")
        print(f"Supervisors: {supervisor_count}")
        print(f"Staff: {staff_count}")
        
        print("\n🎉 Demo site setup completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_demo_site_and_migrate_users()