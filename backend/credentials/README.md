# Google API Credentials Directory

This directory contains the Google API service account credentials needed for the Simple Timesheet application.

## Required Files

### `service-account-key.json` (Required)
- Download this from Google Cloud Console
- Go to APIs & Services → Credentials → Create Service Account → Download JSON Key  
- Rename the downloaded file to `service-account-key.json`
- Place it in this directory

### Template File
- `service-account-key-template.json` - Shows the expected format

## Security Notes

⚠️ **IMPORTANT**: 
- Never commit actual credential files to version control
- The `.gitignore` file excludes `*.json` files in this directory
- Keep your service account key secure and rotate it regularly

## Permissions Required

Your service account needs these permissions:
- Google Sheets API access
- Google Drive API access (to create sheets in user drives)
- Editor role or custom role with necessary permissions

## Testing Credentials

You can test if your credentials work by running:
```bash
node run-tests.js
```

The test suite will verify Google API integration is working properly.