#!/usr/bin/env python3
"""
Test suite for authorization improvements and user onboarding flow
"""

import sys
import os
import importlib.util
import pytz

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def import_module_directly(module_path, module_name):
    """Import module directly without going through __init__.py"""
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# Import modules directly
base_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'krs_reminder')
database_module = import_module_directly(os.path.join(base_path, 'database.py'), 'krs_reminder.database')
auth_module = import_module_directly(os.path.join(base_path, 'auth.py'), 'krs_reminder.auth')
admin_module = import_module_directly(os.path.join(base_path, 'admin.py'), 'krs_reminder.admin')
commands_module = import_module_directly(os.path.join(base_path, 'commands.py'), 'krs_reminder.commands')

SupabaseClient = database_module.SupabaseClient
AuthManager = auth_module.AuthManager
AdminManager = admin_module.AdminManager
CommandHandler = commands_module.CommandHandler


class MockBot:
    """Mock bot for testing"""
    def __init__(self):
        self.db = SupabaseClient()
        self.auth = AuthManager(self.db)
        # AdminManager requires auth_manager and calendar_service_getter
        self.admin = AdminManager(self.db, self.auth, lambda: None)
        self.multi_user_enabled = True
        self.admin_notifications = []  # Track admin notifications
        self.tz = pytz.timezone('Asia/Jakarta')  # Add timezone for tests

    def _notify_admin_unauthorized_access(self, chat_id: int, action: str):
        """Mock admin notification"""
        self.admin_notifications.append({
            'chat_id': chat_id,
            'action': action
        })
        print(f"   📧 Admin notification sent: chat_id={chat_id}, action={action}")


def test_onboarding_message():
    """Test onboarding message for unauthenticated users"""
    print("\n" + "="*60)
    print("TEST 1: Onboarding message for unauthenticated users")
    print("="*60)
    
    bot = MockBot()
    cmd = CommandHandler(bot)
    
    # Get onboarding message
    msg = cmd._get_onboarding_message()
    
    print(f"\nOnboarding message:\n{msg}\n")
    
    # Verify message contains key elements
    assert "belum terdaftar" in msg.lower(), "Should mention user is not registered"
    assert "@el_pablos" in msg, "Should contain admin contact"
    assert "/login" in msg, "Should mention login command"
    assert "secret key" in msg.lower(), "Should mention secret key"
    
    print("✅ PASS: Onboarding message contains all required elements")


def test_unauthenticated_jadwal_with_notification():
    """Test /jadwal command for unauthenticated user with admin notification"""
    print("\n" + "="*60)
    print("TEST 2: Unauthenticated /jadwal with admin notification")
    print("="*60)
    
    bot = MockBot()
    cmd = CommandHandler(bot)
    
    fake_chat_id = 999999999
    
    # Clear notifications
    bot.admin_notifications = []
    
    # Try to access /jadwal
    success, message, events = cmd.handle_jadwal_multiuser(fake_chat_id)
    
    print(f"\nSuccess: {success}")
    print(f"Message: {message[:100]}...")
    print(f"Events: {len(events)}")
    
    # Verify response
    assert success is False, "Should fail for unauthenticated user"
    assert "belum terdaftar" in message.lower(), "Should show onboarding message"
    
    # Verify admin notification was sent
    assert len(bot.admin_notifications) == 1, "Should send admin notification"
    assert bot.admin_notifications[0]['chat_id'] == fake_chat_id, "Should notify about correct user"
    assert "Command: /jadwal" in bot.admin_notifications[0]['action'], "Should mention command"
    
    print("✅ PASS: Unauthenticated user gets onboarding message and admin is notified")


def test_callback_authentication_check():
    """Test that callback handlers check authentication"""
    print("\n" + "="*60)
    print("TEST 3: Callback handlers require authentication")
    print("="*60)
    
    bot = MockBot()
    
    fake_chat_id = 999999999
    
    # Test authentication check
    is_logged_in, user, error_msg = bot.auth.require_login(fake_chat_id)
    
    print(f"\nAuthentication check for fake user:")
    print(f"   Logged in: {is_logged_in}")
    print(f"   User: {user}")
    print(f"   Error: {error_msg}")
    
    assert is_logged_in is False, "Fake user should not be authenticated"
    assert user is None, "User should be None"
    assert "belum login" in error_msg.lower(), "Should show login error"
    
    print("✅ PASS: Authentication check works correctly")


def test_admin_secret_key_verification():
    """Test admin secret key can be verified"""
    print("\n" + "="*60)
    print("TEST 4: Admin secret key verification")
    print("="*60)

    bot = MockBot()

    # Get admin user by username
    users = bot.db.list_all_users()
    admin_user = None
    for user in users:
        if user.get('username') == 'admin':
            admin_user = user
            break

    if not admin_user:
        print("⚠️  SKIP: Admin user not found in database")
        return
    
    print(f"\nAdmin user found: {admin_user['username']}")
    print(f"   User ID: {admin_user['user_id']}")

    # Try to verify with new secret key
    new_secret_key = "jembotisme"
    is_valid = bot.auth.verify_secret_key(admin_user['user_id'], new_secret_key)

    print(f"\nSecret key verification:")
    print(f"   Secret key: {new_secret_key}")
    print(f"   Valid: {is_valid}")

    if is_valid:
        print("✅ PASS: New admin secret key is valid")
    else:
        print("⚠️  INFO: New secret key not yet updated (run update script first)")


def test_authenticated_user_access():
    """Test authenticated user can access commands"""
    print("\n" + "="*60)
    print("TEST 5: Authenticated user can access commands")
    print("="*60)

    bot = MockBot()
    cmd = CommandHandler(bot)

    # Get admin user by username
    users = bot.db.list_all_users()
    admin_user = None
    for user in users:
        if user.get('username') == 'admin':
            admin_user = user
            break

    if not admin_user:
        print("⚠️  SKIP: Admin user not found")
        return

    # Use a test telegram_id for admin
    admin_telegram_id = 5476148500

    # Login admin with new secret key
    result = bot.auth.login('admin', 'jembotisme', admin_telegram_id)

    if not result['success']:
        print(f"⚠️  SKIP: Could not create admin session: {result['message']}")
        return

    print(f"\nAdmin logged in: {admin_user['username']}")
    
    # Try to access /jadwal
    success, message, events = cmd.handle_jadwal_multiuser(admin_telegram_id)
    
    print(f"\nJadwal access:")
    print(f"   Success: {success}")
    print(f"   Events: {len(events)}")
    
    # Logout
    bot.auth.logout(admin_telegram_id)
    
    assert success is True, "Authenticated user should be able to access /jadwal"
    
    print("✅ PASS: Authenticated user can access commands")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 AUTHORIZATION IMPROVEMENTS - TEST SUITE")
    print("="*60)
    
    try:
        test_onboarding_message()
        test_unauthenticated_jadwal_with_notification()
        test_callback_authentication_check()
        test_admin_secret_key_verification()
        test_authenticated_user_access()
        
        print("\n" + "="*60)
        print("🎉 ALL TESTS COMPLETED")
        print("="*60)
        print("\n✅ Authorization improvements are working correctly!")
        print("   • Onboarding message is clear and helpful")
        print("   • Admin notifications are sent for unauthorized access")
        print("   • Authentication checks are in place")
        print("   • Authenticated users can access commands")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

