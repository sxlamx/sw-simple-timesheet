import json
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from typing import List, Dict, Optional, Any
from datetime import datetime
from app.core.config import settings

# Shared folder ID extracted from the Google Drive URL
SHARED_FOLDER_ID = "1osLw7ztdjYZlCoofS79HvYW7_WxXpspx"

class GoogleSheetsService:
    def __init__(self):
        self.credentials = None
        self.gc = None
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Sheets service with service account credentials"""
        try:
            if settings.GOOGLE_SHEETS_CREDENTIALS_FILE:
                # Load credentials from service account file
                self.credentials = Credentials.from_service_account_file(
                    settings.GOOGLE_SHEETS_CREDENTIALS_FILE,
                    scopes=settings.GOOGLE_SHEETS_SCOPES
                )
                
                # Initialize gspread client
                self.gc = gspread.authorize(self.credentials)
                
                # Initialize Google Sheets API service
                self.service = build('sheets', 'v4', credentials=self.credentials)
                print(f"Google Sheets service initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize Google Sheets service: {e}")
    
    def test_sheet_creation(self) -> bool:
        """Test if we can create a basic Google Sheet in shared folder"""
        if not self.gc:
            return False
        
        try:
            test_sheet_name = "Test_Sheet_" + str(datetime.now().timestamp())
            
            # Create in root drive first (to avoid quota issues)
            test_sheet = self.gc.create(test_sheet_name)
            print(f"Test sheet created successfully: {test_sheet.id}")
            
            # Try to delete the test sheet to clean up immediately
            try:
                from googleapiclient.discovery import build
                drive_service = build('drive', 'v3', credentials=self.credentials)
                drive_service.files().delete(fileId=test_sheet.id).execute()
                print(f"Test sheet {test_sheet.id} deleted successfully")
            except Exception as cleanup_error:
                print(f"Could not clean up test sheet: {cleanup_error}")
                
            return True
        except Exception as e:
            print(f"Test sheet creation failed: {e}")
            return False

    def create_timesheet_sheet(self, user_email: str, year: int, month: int) -> Optional[str]:
        """Google Sheets disabled - using database-only storage"""
        print(f"Google Sheets integration disabled - using database-only storage")
        
        # Return None to indicate no Google Sheet will be created
        # The system will rely entirely on SQLite database storage
        return None
    
    def get_timesheet_data(self, spreadsheet_url: str) -> List[Dict[str, Any]]:
        """Get timesheet data from Google Sheet"""
        if not self.gc:
            raise Exception("Google Sheets service not initialized")
        
        try:
            # Extract spreadsheet ID from URL
            spreadsheet_id = self._extract_spreadsheet_id(spreadsheet_url)
            spreadsheet = self.gc.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.sheet1
            
            # Get all records
            records = worksheet.get_all_records()
            
            # Process and validate data
            timesheet_data = []
            for record in records:
                if record.get('Date') and record.get('Start Time'):  # Only include rows with data
                    timesheet_data.append({
                        'date': record.get('Date'),
                        'start_time': record.get('Start Time'),
                        'end_time': record.get('End Time'),
                        'break_duration': record.get('Break Duration (mins)', 0),
                        'total_hours': record.get('Total Hours', 0),
                        'project': record.get('Project', ''),
                        'task_description': record.get('Task Description', ''),
                        'status': record.get('Status', 'draft')
                    })
            
            return timesheet_data
            
        except Exception as e:
            print(f"Error getting timesheet data: {e}")
            return []
    
    def update_timesheet_status(self, spreadsheet_url: str, status: str) -> bool:
        """Update the status of all entries in a timesheet"""
        if not self.gc:
            raise Exception("Google Sheets service not initialized")
        
        try:
            spreadsheet_id = self._extract_spreadsheet_id(spreadsheet_url)
            spreadsheet = self.gc.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.sheet1
            
            # Get all data to find the status column
            all_values = worksheet.get_all_values()
            if not all_values:
                return False
            
            # Find status column index
            header_row = all_values[0]
            status_col_idx = None
            for i, header in enumerate(header_row):
                if 'Status' in header:
                    status_col_idx = i + 1  # gspread uses 1-based indexing
                    break
            
            if status_col_idx is None:
                return False
            
            # Update status for all data rows
            data_rows = len(all_values) - 1  # Exclude header row
            if data_rows > 0:
                # Convert column index to letter
                status_col_letter = chr(64 + status_col_idx)  # A=65, so 64+1=A
                range_notation = f"{status_col_letter}2:{status_col_letter}{data_rows + 1}"
                
                # Create list of status values for all rows
                status_values = [[status] for _ in range(data_rows)]
                worksheet.update(range_notation, status_values)
            
            return True
            
        except Exception as e:
            print(f"Error updating timesheet status: {e}")
            return False
    
    def create_supervisor_aggregate_sheet(self, supervisor_email: str, staff_timesheets: List[Dict]) -> Optional[str]:
        """Create an aggregate sheet for supervisor to view all staff timesheets"""
        if not self.gc:
            raise Exception("Google Sheets service not initialized")
        
        # Extract supervisor login ID
        supervisor_login_id = supervisor_email.split('@')[0]
        sheet_title = f"{supervisor_login_id}_Team_Timesheets_{datetime.now().strftime('%Y_%m')}"
        
        try:
            # Create new spreadsheet in shared folder
            spreadsheet = self.gc.create(sheet_title, folder_id=SHARED_FOLDER_ID)
            worksheet = spreadsheet.sheet1
            
            # Set up headers for aggregate view
            headers = [
                "Staff Member", "Date", "Total Hours", "Project", 
                "Task Description", "Status", "Sheet URL"
            ]
            worksheet.update('A1:G1', [headers])
            
            # Format header
            worksheet.format('A1:G1', {
                "backgroundColor": {"red": 0.8, "green": 0.4, "blue": 0.0},
                "textFormat": {"bold": True, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}
            })
            
            # Aggregate data from all staff timesheets
            aggregate_data = []
            for staff_sheet in staff_timesheets:
                staff_name = staff_sheet.get('staff_name', '')
                sheet_url = staff_sheet.get('sheet_url', '')
                
                # Get data from staff timesheet
                timesheet_data = self.get_timesheet_data(sheet_url)
                
                for entry in timesheet_data:
                    aggregate_data.append([
                        staff_name,
                        entry.get('date', ''),
                        entry.get('total_hours', 0),
                        entry.get('project', ''),
                        entry.get('task_description', ''),
                        entry.get('status', ''),
                        sheet_url
                    ])
            
            # Update the sheet with aggregate data
            if aggregate_data:
                worksheet.update(f'A2:G{len(aggregate_data) + 1}', aggregate_data)
            
            # Share with supervisor
            try:
                spreadsheet.share(supervisor_email, perm_type='user', role='writer')
            except Exception as e:
                print(f"Warning: Could not share aggregate sheet with supervisor {supervisor_email}: {e}")
            
            return spreadsheet.url
            
        except Exception as e:
            print(f"Error creating supervisor aggregate sheet: {e}")
            return None
    
    def _extract_spreadsheet_id(self, url: str) -> str:
        """Extract spreadsheet ID from Google Sheets URL"""
        # Handle different URL formats
        if '/spreadsheets/d/' in url:
            start = url.find('/spreadsheets/d/') + len('/spreadsheets/d/')
            end = url.find('/', start)
            if end == -1:
                end = url.find('#', start)
            if end == -1:
                end = len(url)
            return url[start:end]
        else:
            # If it's already just an ID
            return url
    
    def calculate_total_hours(self, spreadsheet_url: str) -> float:
        """Calculate total hours from a timesheet"""
        timesheet_data = self.get_timesheet_data(spreadsheet_url)
        total_hours = 0.0
        
        for entry in timesheet_data:
            try:
                hours = float(entry.get('total_hours', 0))
                total_hours += hours
            except (ValueError, TypeError):
                continue
        
        return total_hours

# Global instance
google_sheets_service = GoogleSheetsService()