#!/usr/bin/env python3
"""
Authentication Script untuk Published App
Compatible dengan published Google Cloud app
Menggunakan device flow untuk auth
"""

import json
import requests
import time

from scripts._bootstrap import bootstrap

bootstrap()

from krs_reminder import config  # noqa: E402

SCOPES = ' '.join(config.SCOPES)

def load_credentials():
    """Load client credentials"""
    with config.CREDENTIALS_FILE.open('r', encoding='utf-8') as f:
        data = json.load(f)
        if 'installed' in data:
            return data['installed']
        elif 'web' in data:
            return data['web']
        else:
            raise ValueError("Invalid credentials format")

def device_code_auth():
    """Authenticate menggunakan device code flow"""
    print("="*70)
    print("🔐 GOOGLE CALENDAR AUTHENTICATION - PUBLISHED APP")
    print("="*70)
    print()

    creds = load_credentials()
    client_id = creds['client_id']
    client_secret = creds['client_secret']

    # Step 1: Request device code
    print("🔄 Requesting device code...")
    device_code_url = "https://oauth2.googleapis.com/device/code"
    device_params = {
        'client_id': client_id,
        'scope': SCOPES
    }

    try:
        response = requests.post(device_code_url, data=device_params)
        response.raise_for_status()
        device_data = response.json()

        verification_url = device_data.get('verification_url')
        user_code = device_data.get('user_code')
        device_code = device_data.get('device_code')
        expires_in = device_data.get('expires_in', 1800)
        interval = device_data.get('interval', 5)

        print()
        print("="*70)
        print("📋 LANGKAH-LANGKAH:")
        print("="*70)
        print()
        print(f"1️⃣  BUKA URL ini di BROWSER (laptop/HP manapun):")
        print()
        print(f"    {verification_url}")
        print()
        print(f"2️⃣  MASUKKAN KODE ini:")
        print()
        print(f"    {user_code}")
        print()
        print("3️⃣  LOGIN dengan Google Account: tamskun29@gmail.com")
        print("4️⃣  KLIK 'Allow' untuk izinkan akses")
        print()
        print("-" * 70)
        print()
        print(f"⏱️  Kode berlaku: {expires_in // 60} menit")
        print()
        print("🔄 Waiting for authorization...")
        print("   (Jangan tutup terminal ini!)")
        print()

        # Step 2: Poll for token
        token_url = "https://oauth2.googleapis.com/token"
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > expires_in:
                print("\n❌ Timeout! Kode sudah expired.")
                print("   Run script lagi: python3 auth_published.py")
                return False

            # Wait before polling
            time.sleep(interval)

            # Poll for token
            token_params = {
                'client_id': client_id,
                'client_secret': client_secret,
                'device_code': device_code,
                'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
            }

            token_response = requests.post(token_url, data=token_params)
            token_data = token_response.json()

            if token_response.status_code == 200:
                # Success!
                access_token = token_data.get('access_token')
                refresh_token = token_data.get('refresh_token')

                # Save token
                token_json = {
                    "token": access_token,
                    "refresh_token": refresh_token,
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "scopes": [SCOPES]
                }

                with config.TOKEN_FILE.open('w', encoding='utf-8') as f:
                    json.dump(token_json, f, indent=2)

                print()
                print("="*70)
                print("✅ AUTHENTICATION BERHASIL!")
                print("="*70)
                print()
                print(f"✅ Token saved    : {config.TOKEN_FILE}")
                print(f"✅ Access Token   : {access_token[:30]}...")
                if refresh_token:
                    print(f"✅ Refresh Token  : {refresh_token[:30]}...")
                print()
                print("🚀 SEKARANG JALANKAN BOT:")
                print()
                print("   python3 -m krs_reminder.cli.run_bot")
                print()
                print("="*70)
                return True

            elif 'error' in token_data:
                error = token_data['error']
                if error == 'authorization_pending':
                    # Still waiting for user
                    print(f"⏳ Waiting... ({int(elapsed)}s)", end='\r')
                    continue
                elif error == 'slow_down':
                    # Increase polling interval
                    interval += 5
                    continue
                elif error == 'expired_token':
                    print("\n❌ Kode expired! Run script lagi.")
                    return False
                elif error == 'access_denied':
                    print("\n❌ User denied access!")
                    return False
                else:
                    print(f"\n❌ Error: {error}")
                    if 'error_description' in token_data:
                        print(f"   {token_data['error_description']}")
                    return False

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request Error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    device_code_auth()
