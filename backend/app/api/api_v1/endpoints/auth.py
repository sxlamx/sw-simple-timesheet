from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.auth import verify_google_token, create_access_token
from app.core.config import settings
from app.crud.user import user
from app.schemas.user import User, UserCreate
import urllib.parse

router = APIRouter()

class GoogleTokenRequest(BaseModel):
    token: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: User

@router.post("/google", response_model=TokenResponse)
async def authenticate_with_google(
    token_request: GoogleTokenRequest,
    db: Session = Depends(get_db)
):
    """Authenticate user with Google OAuth token"""
    # Verify Google token
    google_user_info = verify_google_token(token_request.token)
    
    # Check if user exists
    existing_user = user.get_by_google_id(db, google_id=google_user_info['google_id'])
    
    if not existing_user:
        # Check if user exists by email
        existing_user = user.get_by_email(db, email=google_user_info['email'])
        
        if existing_user:
            # Update existing user with Google ID
            existing_user.google_id = google_user_info['google_id']
            existing_user.profile_picture = google_user_info['profile_picture']
            db.commit()
            db.refresh(existing_user)
        else:
            # Create new user
            user_create = UserCreate(
                email=google_user_info['email'],
                full_name=google_user_info['full_name'],
                google_id=google_user_info['google_id'],
                profile_picture=google_user_info['profile_picture']
            )
            existing_user = user.create(db, obj_in=user_create)
    else:
        # Update user info from Google
        existing_user.full_name = google_user_info['full_name']
        existing_user.profile_picture = google_user_info['profile_picture']
        db.commit()
        db.refresh(existing_user)
    
    # Create access token
    access_token = create_access_token(data={"sub": str(existing_user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": existing_user
    }

@router.get("/google")
async def google_auth_redirect():
    """Redirect to Google OAuth"""
    google_auth_url = "https://accounts.google.com/o/oauth2/auth"
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "scope": "openid email profile",
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent"
    }
    
    url = f"{google_auth_url}?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url=url)

@router.get("/callback")
async def google_auth_callback(code: str, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    # Exchange authorization code for tokens
    import requests
    
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
    }
    
    token_response = requests.post(token_url, data=token_data)
    
    if token_response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange authorization code"
        )
    
    tokens = token_response.json()
    
    # Verify the ID token
    google_user_info = verify_google_token(tokens['id_token'])
    
    # Check if user exists
    existing_user = user.get_by_google_id(db, google_id=google_user_info['google_id'])
    
    if not existing_user:
        # Check if user exists by email
        existing_user = user.get_by_email(db, email=google_user_info['email'])
        
        if existing_user:
            # Update existing user with Google ID
            existing_user.google_id = google_user_info['google_id']
            existing_user.profile_picture = google_user_info['profile_picture']
            db.commit()
            db.refresh(existing_user)
        else:
            # Create new user
            user_create = UserCreate(
                email=google_user_info['email'],
                full_name=google_user_info['full_name'],
                google_id=google_user_info['google_id'],
                profile_picture=google_user_info['profile_picture']
            )
            existing_user = user.create(db, obj_in=user_create)
    
    # Create access token
    access_token = create_access_token(data={"sub": str(existing_user.id)})
    
    # Redirect to frontend with token
    frontend_url = settings.CORS_ORIGINS.split(',')[0]  # Get first CORS origin
    redirect_url = f"{frontend_url}/auth/callback?token={access_token}&user_id={existing_user.id}"
    
    return RedirectResponse(url=redirect_url)

@router.get("/me", response_model=User)
async def get_current_user_info(
    db: Session = Depends(get_db)
):
    """Get current user information - placeholder for now"""
    # This endpoint will be properly implemented with authentication dependency
    return {"message": "Current user info endpoint - requires authentication"}