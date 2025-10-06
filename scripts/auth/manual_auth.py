"""
Manual Google Calendar Authentication untuk VPS
Gunakan ini jika tidak bisa buka browser
"""

from google_auth_oauthlib.flow import InstalledAppFlow

from scripts._bootstrap import bootstrap

bootstrap()

from krs_reminder import config  # noqa: E402

def manual_auth():
    """Manual authentication - copy URL dan paste code"""
    print("="*60)
    print("🔐 GOOGLE CALENDAR MANUAL AUTHENTICATION")
    print("="*60)
    print()
    print("Karena kita di VPS tanpa browser, ikuti langkah ini:")
    print()

    flow = InstalledAppFlow.from_client_secrets_file(
        str(config.CREDENTIALS_FILE),
        config.SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob'  # Out-of-band mode
    )

    # Get authorization URL
    auth_url, _ = flow.authorization_url(prompt='consent')

    print("1️⃣  COPY URL ini dan buka di browser (laptop/HP):")
    print()
    print(auth_url)
    print()
    print("2️⃣  Login dengan Google account Anda")
    print("3️⃣  Izinkan akses ke Calendar")
    print("4️⃣  Copy KODE yang muncul")
    print()

    # Prompt for code
    code = input("5️⃣  Paste KODE di sini: ").strip()

    # Exchange code for credentials
    flow.fetch_token(code=code)
    creds = flow.credentials

    # Save credentials
    with config.TOKEN_FILE.open('w', encoding='utf-8') as token:
        token.write(creds.to_json())

    print()
    print("="*60)
    print("✅ Authentication berhasil!")
    print(f"✅ Token tersimpan di: {config.TOKEN_FILE}")
    print("="*60)
    print()
    print("Sekarang jalankan bot:")
    print("  python3 -m krs_reminder.cli.run_bot")
    print()

if __name__ == "__main__":
    manual_auth()
