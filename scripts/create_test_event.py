"""
Create test event untuk hari ini - untuk testing reminder
"""

import datetime
from pathlib import Path

import pytz
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from scripts._bootstrap import bootstrap

bootstrap()

from krs_reminder import config  # noqa: E402

SCOPES = ['https://www.googleapis.com/auth/calendar']
TOKEN_FILE: Path = config.TOKEN_FILE

def authenticate():
    """Reuse existing token atau buat baru"""
    creds = None

    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(config.CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        with TOKEN_FILE.open('w', encoding='utf-8') as token:
            token.write(creds.to_json())

    return creds

def create_test_event():
    """Buat test event 2 jam dari sekarang"""
    tz = pytz.timezone('Asia/Jakarta')
    now = datetime.datetime.now(tz)

    # Event 2 jam dari sekarang
    start_time = now + datetime.timedelta(hours=2)
    end_time = start_time + datetime.timedelta(hours=1, minutes=40)

    description = """📚 Mata Kuliah: Testing dan Implementasi Sistem (TEST EVENT)
👨‍🏫 Dosen: Mohammad Aldinugroho A
🔢 Kode: SIF253417
📍 Lokasi: D.304 VB

🧪 TEST EVENT - Bot Reminder System
Akan ada reminder: 1 jam sebelum kuliah
"""

    event = {
        'summary': '🧪 TEST: Testing dan Implementasi Sistem',
        'location': 'D.304 VB',
        'description': description,
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'Asia/Jakarta',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'Asia/Jakarta',
        },
        'colorId': '9',
    }

    return event, start_time

# Authenticate dan create
print("🔐 Authenticating...")
creds = authenticate()
service = build('calendar', 'v3', credentials=creds)

print("📝 Creating test event...")
event, start_time = create_test_event()

try:
    created_event = service.events().insert(calendarId='primary', body=event).execute()
    print(f"✅ Test event created!")
    print(f"📅 Time: {start_time.strftime('%Y-%m-%d %H:%M')} WIB")
    print(f"🔗 Link: {created_event.get('htmlLink')}")
    print(f"\n🔔 Bot akan kirim reminder 1 jam sebelumnya!")
except Exception as e:
    print(f"❌ Error: {e}")
