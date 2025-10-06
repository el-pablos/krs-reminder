#!/usr/bin/env python3
"""
Authentication untuk Web Credentials di VPS
Workaround untuk credentials.json tipe 'web'
"""

import json
import requests
from urllib.parse import urlencode

from scripts._bootstrap import bootstrap

bootstrap()

from krs_reminder import config  # noqa: E402

def load_web_credentials():
    """Load credentials dari file"""
    with config.CREDENTIALS_FILE.open('r', encoding='utf-8') as f:
        data = json.load(f)
        if 'web' in data:
            return data['web']
        elif 'installed' in data:
            return data['installed']
        else:
            raise ValueError("Invalid credentials format")

def web_auth_flow():
    """Manual OAuth flow untuk web credentials"""
    print("="*70)
    print("🔐 GOOGLE CALENDAR WEB AUTHENTICATION")
    print("="*70)
    print()

    # Load credentials
    creds = load_web_credentials()
    client_id = creds['client_id']
    client_secret = creds['client_secret']

    # Build authorization URL
    auth_params = {
        'client_id': client_id,
        'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
        'response_type': 'code',
        'scope': ' '.join(config.SCOPES),
        'access_type': 'offline',
        'prompt': 'consent'
    }

    auth_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(auth_params)}"

    print("📋 LANGKAH-LANGKAH:")
    print()
    print("1️⃣  Copy URL ini dan buka di BROWSER (laptop/HP/komputer manapun):")
    print()
    print(f"    {auth_url}")
    print()
    print("2️⃣  Login dengan Google Account Anda")
    print("3️⃣  Klik 'Allow' untuk izinkan akses Calendar")
    print("4️⃣  Copy AUTHORIZATION CODE yang muncul")
    print()
    print("-" * 70)
    print()

    # Get authorization code from user
    auth_code = input("5️⃣  Paste AUTHORIZATION CODE di sini: ").strip()

    if not auth_code:
        print("❌ Kode tidak boleh kosong!")
        return False

    print()
    print("🔄 Menukar code dengan access token...")

    # Exchange code for token
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        'code': auth_code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
        'grant_type': 'authorization_code'
    }

    try:
        response = requests.post(token_url, data=token_data)
        response.raise_for_status()
        token_info = response.json()

        # Build token.json format
        token_json = {
            "token": token_info.get("access_token"),
            "refresh_token": token_info.get("refresh_token"),
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": client_id,
            "client_secret": client_secret,
            "scopes": ["https://www.googleapis.com/auth/calendar.readonly"]
        }

        # Save token
        with config.TOKEN_FILE.open('w', encoding='utf-8') as f:
            json.dump(token_json, f, indent=2)

        print()
        print("="*70)
        print("✅ AUTHENTICATION BERHASIL!")
        print("="*70)
        print(f"✅ Access Token : {token_info.get('access_token')[:30]}...")
        print(f"✅ Refresh Token: {token_info.get('refresh_token', 'N/A')[:30]}...")
        print(f"✅ Token saved  : {config.TOKEN_FILE}")
        print()
        print("🚀 Sekarang jalankan bot:")
        print("   python3 -m krs_reminder.cli.run_bot")
        print()
        print("="*70)
        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return False

if __name__ == "__main__":
    web_auth_flow()
