#!/usr/bin/env python3
"""
AUTH FINAL - Metode Paling Mudah untuk Published App
Menggunakan manual authorization code flow
"""

import json
from pathlib import Path
from urllib.parse import urlencode

from scripts._bootstrap import bootstrap

bootstrap()

from krs_reminder import config  # noqa: E402


def load_credentials(path: Path | None = None):
    """Load credentials dari file konfigurasi Google OAuth."""

    credentials_path = path or config.CREDENTIALS_FILE
    with credentials_path.open('r', encoding='utf-8') as handle:
        creds_data = json.load(handle)
        return creds_data['installed']

def get_authorization_url(client_id):
    """Generate authorization URL"""
    params = {
        'client_id': client_id,
        'redirect_uri': 'http://localhost',
        'response_type': 'code',
        'scope': 'https://www.googleapis.com/auth/calendar.readonly',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

def exchange_code_for_token(code, client_id, client_secret):
    """Exchange authorization code for refresh token"""
    import requests

    data = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': 'http://localhost',
        'grant_type': 'authorization_code'
    }

    response = requests.post('https://oauth2.googleapis.com/token', data=data)
    return response.json()

def main():
    print("=" * 70)
    print("🔐 AUTHENTICATION FINAL - Published App Method")
    print("=" * 70)
    print()

    # Load credentials
    creds = load_credentials()
    client_id = creds['client_id']
    client_secret = creds['client_secret']

    print("📋 Client ID yang akan digunakan:")
    print(f"   {client_id}")
    print()

    # Generate auth URL
    auth_url = get_authorization_url(client_id)

    print("📍 LANGKAH 1: Buka URL ini di browser")
    print("=" * 70)
    print(auth_url)
    print("=" * 70)
    print()

    print("📍 LANGKAH 2: Login dengan akun Google (tamskun29@gmail.com)")
    print("📍 LANGKAH 3: Klik 'Allow' untuk memberikan akses")
    print("📍 LANGKAH 4: Browser akan redirect ke localhost (akan error - NORMAL!)")
    print("📍 LANGKAH 5: COPY SELURUH URL dari address bar browser")
    print()
    print("   Contoh URL yang akan kamu dapat:")
    print("   http://localhost/?code=4/0AVG7fi... &scope=...")
    print()
    print("   Yang penting adalah bagian 'code=...' sampai sebelum '&scope'")
    print()

    # Get code from user
    full_url = input("PASTE FULL URL dari browser di sini: ").strip()

    # Extract code from URL
    if 'code=' in full_url:
        code = full_url.split('code=')[1].split('&')[0]
        print(f"\n✅ Authorization code extracted: {code[:20]}...")
    else:
        print("\n❌ Error: Tidak ditemukan 'code=' di URL")
        return

    # Exchange code for token
    print("\n🔄 Menukar authorization code dengan refresh token...")

    try:
        token_response = exchange_code_for_token(code, client_id, client_secret)

        if 'error' in token_response:
            print(f"\n❌ Error: {token_response.get('error_description', token_response['error'])}")
            return

        # Create token.json
        token_data = {
            "refresh_token": token_response['refresh_token'],
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": client_id,
            "client_secret": client_secret,
            "scopes": ["https://www.googleapis.com/auth/calendar.readonly"]
        }

        with config.TOKEN_FILE.open('w', encoding='utf-8') as handle:
            json.dump(token_data, handle, indent=2)

        print("\n" + "=" * 70)
        print("✅ SUKSES! token.json berhasil dibuat")
        print("=" * 70)
        print()
        print("📋 Token info:")
        print(f"   Client ID: {client_id}")
        print(f"   Refresh Token: {token_response['refresh_token'][:30]}...")
        print()
        print("✅ Sekarang kamu bisa jalankan bot:")
        print("   python3 -m krs_reminder.cli.run_bot")
        print()

    except Exception as e:
        print(f"\n❌ Error saat exchange token: {e}")

if __name__ == "__main__":
    main()
