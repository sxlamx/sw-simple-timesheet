#!/usr/bin/env python3
"""
Create test users for the demo site
"""

import sys
sys.path.append('/Volumes/X9Pro/github/sw-simple-timesheet/backend')

from app.core.database import get_db
from app.models.user import User, Site, SiteMember, UserRole

def create_test_users():
    db = next(get_db())
    
    try:
        # Get demo site
        demo_site = db.query(Site).filter(Site.name == "Demo Site").first()
        if not demo_site:
            print("Demo site not found")
            return
            
        print(f"Creating test users for site: {demo_site.name}")
        
        # Test users to create
        test_users = [
            {
                "email": "admin@demo.com",
                "full_name": "Demo Admin",
                "role": UserRole.ADMIN
            },
            {
                "email": "supervisor@demo.com", 
                "full_name": "Demo Supervisor",
                "role": UserRole.SUPERVISOR,
                "is_supervisor": True
            },
            {
                "email": "alice.smith@demo.com",
                "full_name": "Alice Smith",
                "role": UserRole.STAFF,
                "department": "Engineering"
            },
            {
                "email": "bob.jones@demo.com",
                "full_name": "Bob Jones", 
                "role": UserRole.STAFF,
                "department": "Engineering"
            },
            {
                "email": "carol.davis@demo.com",
                "full_name": "Carol Davis",
                "role": UserRole.STAFF,
                "department": "Design"
            },
            {
                "email": "david.wilson@demo.com",
                "full_name": "David Wilson",
                "role": UserRole.STAFF,
                "department": "Marketing"
            }
        ]
        
        created_users = []
        supervisor_user = None
        
        for user_data in test_users:
            # Check if user already exists
            existing = db.query(User).filter(
                User.email == user_data["email"],
                User.site_id == demo_site.id
            ).first()
            
            if existing:
                print(f"User {user_data['email']} already exists")
                if user_data["role"] == UserRole.SUPERVISOR:
                    supervisor_user = existing
                created_users.append(existing)
                continue
                
            # Create new user
            user = User(
                site_id=demo_site.id,
                email=user_data["email"],
                full_name=user_data["full_name"],
                role=user_data["role"],
                is_supervisor=user_data.get("is_supervisor", False),
                department=user_data.get("department"),
                is_active=True
            )
            
            db.add(user)
            db.flush()
            created_users.append(user)
            
            if user_data["role"] == UserRole.SUPERVISOR:
                supervisor_user = user
            
            print(f"Created user: {user.full_name} ({user.email}) - {user.role.value}")
            
            # Create site membership
            membership = SiteMember(
                site_id=demo_site.id,
                user_id=user.id,
                role=user_data["role"],
                is_active=True
            )
            db.add(membership)
        
        # Set supervisor relationships for staff
        if supervisor_user:
            staff_users = [u for u in created_users if u.role == UserRole.STAFF]
            for staff in staff_users:
                staff.supervisor_id = supervisor_user.id
                print(f"Set {supervisor_user.full_name} as supervisor for {staff.full_name}")
        
        db.commit()
        print(f"\n✅ Created {len(test_users)} test users successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_test_users()