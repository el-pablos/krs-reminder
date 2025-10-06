#!/usr/bin/env python3
"""
Simple Authentication - Manual Token Input
Paling simpel, pasti work, untuk published app
"""

import json

from scripts._bootstrap import bootstrap

bootstrap()

from krs_reminder import config  # noqa: E402

def simple_manual_auth():
    """Manual auth - user provide token dari Google OAuth Playground"""
    print("="*70)
    print("🔐 GOOGLE CALENDAR - SIMPLE MANUAL AUTHENTICATION")
    print("="*70)
    print()
    print("Karena app sudah published, cara paling mudah adalah:")
    print()
    print("METHOD 1: Gunakan Google OAuth 2.0 Playground")
    print("="*70)
    print()
    print("STEP 1: BUKA OAUTH PLAYGROUND")
    print("-" * 70)
    print()
    print("  https://developers.google.com/oauthplayground/")
    print()
    print("STEP 2: KONFIGURASI")
    print("-" * 70)
    print()
    print("  1. Klik ⚙️ (Settings) di kanan atas")
    print("  2. Centang: [✓] Use your own OAuth credentials")
    print()

    # Load credentials
    try:
        with config.CREDENTIALS_FILE.open('r', encoding='utf-8') as f:
            data = json.load(f)
            if 'installed' in data:
                creds = data['installed']
            elif 'web' in data:
                creds = data['web']
            else:
                print("  ❌ Invalid credentials.json format")
                return False

        client_id = creds['client_id']
        client_secret = creds['client_secret']

        print("  3. OAuth Client ID:")
        print(f"     {client_id}")
        print()
        print("  4. OAuth Client secret:")
        print(f"     {client_secret}")
        print()
        print("  5. Klik 'Close'")
        print()

        print("STEP 3: SELECT SCOPES")
        print("-" * 70)
        print()
        print("  1. Di kolom 'Input your own scopes', masukkan:")
        print("     https://www.googleapis.com/auth/calendar.readonly")
        print()
        print("  2. Klik 'Authorize APIs'")
        print()
        print("  3. Pilih account: tamskun29@gmail.com")
        print()
        print("  4. Klik 'Allow'")
        print()

        print("STEP 4: EXCHANGE CODE FOR TOKENS")
        print("-" * 70)
        print()
        print("  1. Klik 'Exchange authorization code for tokens'")
        print()
        print("  2. Copy 'Refresh token' yang muncul")
        print()

        print("="*70)
        print()

        # Get refresh token from user
        refresh_token = input("PASTE REFRESH TOKEN di sini: ").strip()

        if not refresh_token:
            print("\n❌ Refresh token tidak boleh kosong!")
            return False

        # Create token.json
        token_data = {
            "refresh_token": refresh_token,
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": client_id,
            "client_secret": client_secret,
            "scopes": ["https://www.googleapis.com/auth/calendar.readonly"]
        }

        with config.TOKEN_FILE.open('w', encoding='utf-8') as f:
            json.dump(token_data, f, indent=2)

        print()
        print("="*70)
        print("✅ TOKEN BERHASIL DISIMPAN!")
        print("="*70)
        print()
        print(f"✅ File created: {config.TOKEN_FILE}")
        print()
        print("🚀 SEKARANG JALANKAN BOT:")
        print()
        print("   python3 -m krs_reminder.cli.run_bot")
        print()
        print("="*70)
        return True

    except FileNotFoundError:
        print(f"  ❌ credentials.json not found at {config.CREDENTIALS_FILE}!")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    simple_manual_auth()
