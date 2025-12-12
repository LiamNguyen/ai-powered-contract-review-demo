"""Google API authentication helper."""

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes required for reading docs and managing comments
SCOPES = [
    "https://www.googleapis.com/auth/documents",  # Read and create docs
    "https://www.googleapis.com/auth/drive.file",  # Access files created by app
    "https://www.googleapis.com/auth/gmail.send",  # Send emails via Gmail
]

# Paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token.json"


def get_credentials() -> Credentials:
    """Get or refresh OAuth credentials.

    First run will open a browser for authentication.
    Subsequent runs use cached token.
    """
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"credentials.json not found at {CREDENTIALS_FILE}. "
                    "Download it from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token for next run
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return creds


def get_docs_service():
    """Get Google Docs API service."""
    creds = get_credentials()
    return build("docs", "v1", credentials=creds)


def get_drive_service():
    """Get Google Drive API service."""
    creds = get_credentials()
    return build("drive", "v3", credentials=creds)


def get_gmail_service():
    """Get Gmail API service."""
    creds = get_credentials()
    return build("gmail", "v1", credentials=creds)
