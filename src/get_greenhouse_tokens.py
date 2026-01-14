import os
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

# Generic Greenhouse lookup (no API required)
SEARCH_API_KEY = os.environ.get("SEARCH_API_KEY")  # Optional for future use

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
TOKEN_PATH = Path("token_sheets.json")
CREDENTIALS_PATH = Path("credentials.json")

def search_greenhouse_board(company_name: str):
    """
    Run a web search for the company’s Greenhouse board.
    Returns a list of result URLs (strings).
    """
    urls = []
    
    # Try common variations of company names
    variants = [
        company_name.lower().replace(" ", ""),  # IBM -> ibm
        company_name.lower().replace(" ", "-"),  # IBM -> ibm (no spaces)
        company_name.lower().split()[0],  # "Apple Inc" -> "apple"
    ]
    
    for variant in set(variants):  # Remove duplicates
        if variant:
            url = f"https://boards.greenhouse.io/{variant}"
            urls.append(url)
    
    return urls

def extract_greenhouse_token_from_url(url: str):
    """
    Extract the board token from a Greenhouse URL and validate it exists.
    e.g. https://boards.greenhouse.io/openai  -> openai (if URL is reachable)
    """
    parsed = urlparse(url)
    if "boards.greenhouse.io" not in parsed.netloc:
        return None

    # Path like "/openai"
    path = parsed.path.strip("/")
    if not path:
        return None

    token = path.split("/")[0]
    
    # Validate token format
    if not re.match(r"^[a-zA-Z0-9\-]+$", token):
        return None
    
    # Quick HEAD request to verify the board exists
    try:
        resp = requests.head(url, timeout=5, allow_redirects=True)
        if resp.status_code == 200 or resp.status_code == 403:  # 403 OK (access restricted)
            return token
    except Exception:
        pass
    
    return None

def find_greenhouse_token_for_company(company_name: str):
    """
    High-level helper: try generic URL patterns then validate.
    """
    try:
        urls = search_greenhouse_board(company_name)
    except Exception as e:
        print(f"[ERROR] Lookup failed for {company_name}: {e}")
        return None

    for url in urls:
        token = extract_greenhouse_token_from_url(url)
        if token:
            return token
    return None


def get_credentials():
    """Get or refresh Google Sheets API credentials."""
    creds = None
    if TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        except Exception:
            try:
                TOKEN_PATH.unlink()
            except Exception:
                pass
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError("credentials.json not found in project root")
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        with TOKEN_PATH.open("w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return creds

def main():
    """Read companies from Google Sheets, look up Greenhouse tokens, write back in-place."""
    import argparse

    parser = argparse.ArgumentParser(description="Lookup and update Greenhouse tokens in Google Sheets")
    parser.add_argument("--spreadsheet_id", required=True, help="Google Sheets spreadsheet ID")
    parser.add_argument("--sheet_name", default="companies", help="Sheet/tab name (default: companies)")
    parser.add_argument("--limit", type=int, default=None, help="Limit to first N companies (for testing)")
    args = parser.parse_args()

    # Get credentials and build service
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)

    # Read data from sheet
    range_name = f"'{args.sheet_name}'!A1:Z1000"
    result = service.spreadsheets().values().get(spreadsheetId=args.spreadsheet_id, range=range_name).execute()
    values = result.get("values", [])

    if not values:
        print(f"No data found in {args.sheet_name}")
        return

    headers = values[0]
    if "company_name" not in headers:
        raise ValueError("Sheet must have a 'company_name' column")

    # Ensure greenhouse_board_token column exists
    if "greenhouse_board_token" not in headers:
        headers.append("greenhouse_board_token")
        # Write header row back
        service.spreadsheets().values().update(
            spreadsheetId=args.spreadsheet_id,
            range=f"'{args.sheet_name}'!A1",
            valueInputOption="RAW",
            body={"values": [headers]}
        ).execute()

    col_idx = headers.index("greenhouse_board_token")
    company_col_idx = headers.index("company_name")

    # Process each row (limit to first N if specified)
    updated_values = [headers]
    processed_count = 0
    rows_to_process = values[1:]
    
    if args.limit:
        rows_to_process = rows_to_process[:args.limit]
        print(f"Testing with first {len(rows_to_process)} companies")
    
    for row_idx, row in enumerate(rows_to_process, start=2):
        # Ensure row is long enough
        while len(row) <= col_idx:
            row.append("")

        company = (row[company_col_idx] if company_col_idx < len(row) else "").strip()
        if not company:
            updated_values.append(row)
            continue

        # Check if token already present
        if col_idx < len(row) and row[col_idx].strip():
            print(f"[SKIP] {company} already has token: {row[col_idx]}")
            updated_values.append(row)
            continue

        print(f"Looking up Greenhouse token for: {company}")
        token = find_greenhouse_token_for_company(company)
        row[col_idx] = token or ""
        updated_values.append(row)
        processed_count += 1
        time.sleep(1.0)

    # Write all rows back to sheet
    service.spreadsheets().values().update(
        spreadsheetId=args.spreadsheet_id,
        range=f"'{args.sheet_name}'!A1",
        valueInputOption="RAW",
        body={"values": updated_values}
    ).execute()

    print(f"Done. Processed {processed_count} companies, updated {len(updated_values)-1} total rows in {args.sheet_name}")

if __name__ == "__main__":
    main()
