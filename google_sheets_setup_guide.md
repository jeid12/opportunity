# Google Sheets Setup Guide

To enable automatic upload to Google Sheets, follow these steps:

## 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Google Sheets API
   - Google Drive API

## 2. Create Service Account

1. In Google Cloud Console, go to "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Enter a name (e.g., "opportunity-scraper")
4. Click "Create and Continue"
5. Skip role assignment (click "Continue")
6. Click "Done"

## 3. Generate Credentials

1. Click on the created service account
2. Go to "Keys" tab
3. Click "Add Key" > "Create new key"
4. Select "JSON" format
5. Download the file
6. Rename it to `google_credentials.json`
7. Place it in the same folder as main.py

## 4. Share Google Sheet

1. Create a new Google Sheet or use existing one
2. Click "Share" button
3. Add the service account email (found in the JSON file under "client_email")
4. Give it "Editor" permissions

## 5. Run the Script

The script will automatically:

- Create a new spreadsheet called "Opportunity Scraper Results" if it doesn't exist
- Upload all scraped opportunities
- Format the data with headers and auto-resize columns
- Provide you with the shareable link

## Example google_credentials.json structure:

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "...",
  "client_email": "opportunity-scraper@your-project.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "...",
  "client_x509_cert_url": "..."
}
```

## Security Note

- Keep your credentials file secure and never share it publicly
- Add `google_credentials.json` to your .gitignore file if using version control
