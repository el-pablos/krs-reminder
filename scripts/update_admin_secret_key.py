#!/usr/bin/env python3
"""
Script to update admin user's secret key in the database
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from krs_reminder.database import SupabaseClient
from krs_reminder.auth import AuthManager
import bcrypt


def update_admin_secret_key(new_secret_key: str, admin_username: str = 'admin'):
    """
    Update admin user's secret key

    Args:
        new_secret_key: New secret key to set
        admin_username: Admin's username (default: 'admin')

    Note:
        telegram_chat_id is stored in sessions table, not users table
    """
    print("="*60)
    print("🔑 UPDATE ADMIN SECRET KEY")
    print("="*60)

    # Initialize database
    db = SupabaseClient()

    # Get admin user by username
    print(f"\n1. Looking for admin user with username: {admin_username}...")
    users = db.list_all_users()

    admin_user = None
    for user in users:
        if user.get('username') == admin_username:
            admin_user = user
            break

    if not admin_user:
        print(f"❌ Admin user with username '{admin_username}' not found!")
        return False

    print(f"✅ Found admin user: {admin_user['username']} (ID: {admin_user['user_id']})")

    # Hash the new secret key
    print(f"\n2. Hashing new secret key...")
    hashed_key = bcrypt.hashpw(new_secret_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    print(f"✅ Secret key hashed")

    # Update in database using REST API
    print(f"\n3. Updating secret_key_hash in database...")
    try:
        # Use PATCH request to update user
        result = db._request(
            'PATCH',
            'users',
            data={
                'secret_key_hash': hashed_key
            },
            params={'user_id': f'eq.{admin_user["user_id"]}'}
        )

        if result:
            print(f"✅ Secret key updated successfully!")
            print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"\n🎉 SUCCESS!")
            print(f"\nUpdated:")
            print(f"   • Secret key: {new_secret_key}")
            print(f"\nAdmin can now login with:")
            print(f"   /login {new_secret_key}")
            print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            return True
        else:
            print(f"❌ Failed to update secret key")
            return False
            
    except Exception as e:
        print(f"❌ Error updating secret key: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    # New secret key and settings
    new_secret_key = "jembotisme"
    admin_username = "admin"

    print(f"\nNew secret key: {new_secret_key}")
    print(f"Admin username: {admin_username}")
    print(f"\nProceed? (y/n): ", end='')

    # Auto-confirm for script execution
    confirm = input().strip().lower()

    if confirm != 'y':
        print("❌ Cancelled")
        return

    success = update_admin_secret_key(new_secret_key, admin_username)
    
    if success:
        print("\n✅ Admin secret key updated successfully!")
        sys.exit(0)
    else:
        print("\n❌ Failed to update admin secret key")
        sys.exit(1)


if __name__ == "__main__":
    main()

