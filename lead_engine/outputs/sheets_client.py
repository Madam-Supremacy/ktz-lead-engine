"""
Pushes lead records to a Google Sheet using a service account.

Setup required (one-time):
1. In Google Cloud Console, enable the "Google Sheets API" for your project.
2. Go to APIs & Services -> Credentials -> Create Credentials -> Service Account.
3. Create a key for that service account (JSON format) and download it.
4. Save that JSON file somewhere safe and point GOOGLE_SERVICE_ACCOUNT_JSON at it in .env.
5. Create a Google Sheet, and share it (like sharing with a person) with the
   service account's email address (found inside the JSON file, "client_email"),
   giving it Editor access.
6. Copy the Sheet's ID from its URL:
   https://docs.google.com/spreadsheets/d/<THIS_PART>/edit
   and put it in GOOGLE_SHEET_ID in .env.
"""
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def push_to_sheet(df: pd.DataFrame, service_account_json: str, sheet_id: str, worksheet_name: str = "Leads") -> None:
    """
    Append the given DataFrame's rows to a worksheet in a Google Sheet.
    Creates the worksheet with a header row if it doesn't exist yet.
    """
    creds = Credentials.from_service_account_file(service_account_json, scopes=SCOPES)
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_key(sheet_id)

    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=len(df.columns))
        worksheet.append_row(list(df.columns))

    # If the worksheet exists but is empty, add the header row too
    if not worksheet.get_all_values():
        worksheet.append_row(list(df.columns))

    rows = df.astype(str).values.tolist()
    worksheet.append_rows(rows, value_input_option="RAW")
