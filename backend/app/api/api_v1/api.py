from fastapi import APIRouter
from app.api.api_v1.endpoints import auth, users, timesheets, timesheet_entries, notifications, feedback, supervisor_mapping

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(timesheets.router, prefix="/timesheets", tags=["timesheets"])
api_router.include_router(timesheet_entries.router, prefix="/timesheet-entries", tags=["timesheet-entries"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
api_router.include_router(supervisor_mapping.router, prefix="/supervisor-mappings", tags=["supervisor-mapping"])