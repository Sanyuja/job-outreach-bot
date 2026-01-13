# export_sheet_to_csv.py

import argparse
import csv
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

# We only need read-only access to Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def get_credentials():
    """
    Load OAuth credentials from token.json / credentials.json.
    Reuses the same pattern as Gmail, but with Sheets scopes.
    """
    creds = None
    token_path = Path("token_sheets.json")
    cred_path = Path("credentials.json")

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    # If no valid credentials available, let user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not cred_path.exists():
                print("[ERROR] credentials.json not found. Put your Google OAuth client file in project root.")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(cred_path), SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for next run
        with token_path.open("w") as token_file:
            token_file.write(creds.to_json())

    return creds


def export_sheet_to_csv(spreadsheet_id: str, sheet_name: str, output_path: str):
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)

    range_name = f"{sheet_name}"
    print(f"[INFO] Fetching '{range_name}' from spreadsheet {spreadsheet_id} ...")

    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range_name)
        .execute()
    )
    values = result.get("values", [])

    if not values:
        print("[INFO] No data found in the sheet.")
        return

    # First row is header
    headers = values[0]
    rows = values[1:]

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            # Pad rows to the header length
            padded = row + [""] * (len(headers) - len(row))
            writer.writerow(padded)

    print(f"[RESULT] Wrote {len(rows)} data rows to {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Export a Google Sheets tab to CSV.")
    parser.add_argument("--spreadsheet_id", required=True, help="Google Sheets spreadsheet ID")
    parser.add_argument("--sheet_name", required=True, help="Sheet/tab name, e.g. 'raw_jobs'")
    parser.add_argument(
        "--output",
        required=False,
        default="jobs/raw_jobs.csv",
        help="Output CSV path (default: jobs/raw_jobs.csv)",
    )
    args = parser.parse_args()

    export_sheet_to_csv(args.spreadsheet_id, args.sheet_name, args.output)


if __name__ == "__main__":
    main()
