#!/usr/bin/env python3
"""
Desktop Authentication untuk Google Calendar di VPS
Menggunakan credentials.json tipe "installed" (desktop)
"""

from google_auth_oauthlib.flow import InstalledAppFlow

from scripts._bootstrap import bootstrap

bootstrap()

from krs_reminder import config  # noqa: E402

def desktop_auth():
    """Auth dengan Desktop credentials - manual copy-paste kode"""
    print("="*70)
    print("🔐 GOOGLE CALENDAR DESKTOP AUTHENTICATION")
    print("="*70)
    print()

    # Create flow dengan redirect_uri out-of-band
    flow = InstalledAppFlow.from_client_secrets_file(
        str(config.CREDENTIALS_FILE),
        config.SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob'
    )

    # Generate auth URL
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        prompt='consent'
    )

    print("📋 LANGKAH-LANGKAH:")
    print()
    print("1️⃣  COPY URL ini dan BUKA di BROWSER (laptop/HP manapun):")
    print()
    print(f"    {auth_url}")
    print()
    print("2️⃣  LOGIN dengan Google Account Anda")
    print("3️⃣  KLIK 'Allow' untuk izinkan akses ke Google Calendar")
    print("4️⃣  COPY kode authorization yang muncul di halaman")
    print()
    print("-" * 70)
    print()

    # Get code from user
    code = input("5️⃣  PASTE kode authorization di sini: ").strip()

    if not code:
        print("❌ Kode tidak boleh kosong!")
        return False

    print()
    print("🔄 Menukar kode dengan access token...")

    try:
        # Exchange code for token
        flow.fetch_token(code=code)
        creds = flow.credentials

        # Save token
        with config.TOKEN_FILE.open('w', encoding='utf-8') as token:
            token.write(creds.to_json())

        print()
        print("="*70)
        print("✅ AUTHENTICATION BERHASIL!")
        print("="*70)
        print()
        print(f"✅ Token saved    : {config.TOKEN_FILE}")
        print(f"✅ Access Token   : {creds.token[:30]}...")
        if creds.refresh_token:
            print(f"✅ Refresh Token  : {creds.refresh_token[:30]}...")
        print()
        print("🚀 SEKARANG JALANKAN BOT:")
        print()
        print("   python3 -m krs_reminder.cli.run_bot")
        print()
        print("="*70)
        return True

    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    desktop_auth()
