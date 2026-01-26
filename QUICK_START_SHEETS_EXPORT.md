# Quick Start: Google Sheets Export

## What This Does

Automatically exports anonymized signatory data from your Supabase database to a Google Sheet daily.

**You don't need a local copy of the website** - everything runs automatically in GitHub Actions (in the cloud).

## What's Been Set Up

✅ Python script (`export_to_sheets.py`) that removes identifying info  
✅ GitHub Actions workflow updated to run the export daily  
✅ Dependencies added to `pyproject.toml`  

## What You Need To Do

### Step 1: Set Up Google Cloud (5-10 minutes)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable "Google Sheets API" (search for it in APIs & Services)
4. Create a Service Account:
   - IAM & Admin → Service Accounts → Create Service Account
   - Name it "sheets-exporter"
   - Grant it "Editor" role
5. Create a JSON key:
   - Click on the service account → Keys tab
   - Add Key → Create new key → JSON
   - Download the JSON file (keep it safe!)

### Step 2: Create Your Google Sheet

1. Go to [Google Sheets](https://sheets.google.com/)
2. Create a new blank spreadsheet
3. Copy the Sheet ID from the URL:
   - Example URL: `https://docs.google.com/spreadsheets/d/1ABC123xyz/edit`
   - Copy `1ABC123xyz` (the part between `/d/` and `/edit`)
4. Share the sheet:
   - Click "Share" button
   - Add the email from the JSON file (looks like: `sheets-exporter@project-name.iam.gserviceaccount.com`)
   - Give it "Editor" permission

### Step 3: Add Secrets to GitHub

1. Go to your GitHub repository: `https://github.com/CuttingEEG/EEG101CommunityFramework`
2. Click: Settings → Secrets and variables → Actions
3. Click "New repository secret" and add these two:

   **Secret 1: GOOGLE_SHEETS_CREDENTIALS**
   - Name: `GOOGLE_SHEETS_CREDENTIALS`
   - Value: Copy the ENTIRE contents of the JSON file you downloaded
   - (It should start with `{"type":"service_account",...}`)

   **Secret 2: GOOGLE_SHEET_ID**
   - Name: `GOOGLE_SHEET_ID`
   - Value: Paste the Sheet ID you copied (e.g., `1ABC123xyz`)

### Step 4: Merge and Done!

1. Merge this branch (`export-sheets`) to `main`
2. The workflow will run automatically and export the data
3. Check your Google Sheet - it should populate with anonymized data!

The export will now run daily at midnight UTC (along with the website build).

## What Gets Exported?

✅ **Included:** Demographics (gender, age, country, career stage), all pledges, timestamps  
❌ **Excluded:** Names, email, ID, ORCID, comments, affiliation

## Troubleshooting

**Nothing in the sheet?**
- Check GitHub Actions tab - look for errors in the "Export Anonymized Data" job
- Verify the service account email is shared with "Editor" permission on the sheet
- Double-check the GOOGLE_SHEET_ID is correct

**"Permission denied"?**
- Make sure you shared the sheet with the service account email
- Check that it has "Editor" (not just "Viewer") permission

**Need help?**
- Full documentation: `backend/google_sheets_export.md`
- Check the workflow logs in GitHub Actions tab
