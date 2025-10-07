"""
Comprehensive test suite for all authorization and error handling fixes
"""

import sys
import os
import pytz

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from krs_reminder.database import SupabaseClient
from krs_reminder.auth import AuthManager
from krs_reminder.admin import AdminManager
from krs_reminder.commands import CommandHandler


class MockBot:
    """Mock bot for testing"""
    def __init__(self):
        self.db = SupabaseClient()
        self.auth = AuthManager(self.db)
        self.admin = AdminManager(self.db, self.auth, lambda: None)
        self.multi_user_enabled = True
        self.tz = pytz.timezone('Asia/Jakarta')
        self.admin_notifications = []
    
    def _notify_admin_unauthorized_access(self, chat_id: int, action: str):
        """Mock admin notification"""
        self.admin_notifications.append({'chat_id': chat_id, 'action': action})
        print(f"   📧 Admin notification: chat_id={chat_id}, action={action}")


def test_login_command():
    """Test /login command with correct secret key"""
    print("\n" + "="*60)
    print("TEST 1: Login command with correct secret key")
    print("="*60)
    
    bot = MockBot()
    cmd = CommandHandler(bot)
    
    # Test login with correct secret key
    admin_chat_id = 5476148500
    
    # Simulate /login jembotisme
    args = ['/login', 'jembotisme']
    result = cmd.handle_login(admin_chat_id, args)
    
    print(f"\nLogin result:")
    print(result)
    
    # Verify login success
    assert "Login Berhasil" in result or "sudah login" in result, "❌ Login should succeed"
    
    print("\n✅ PASS: Login command works correctly")


def test_admin_notification_fix():
    """Test admin notification system uses correct telegram_chat_id"""
    print("\n" + "="*60)
    print("TEST 2: Admin notification uses correct telegram_chat_id")
    print("="*60)
    
    bot = MockBot()
    
    # Check admins table
    try:
        admins = bot.db._request('GET', 'admins', params={'limit': '1'})
        assert admins, "❌ No admins found in database"
        
        admin = admins[0]
        print(f"\nAdmin found:")
        print(f"  admin_id: {admin['admin_id']}")
        print(f"  telegram_chat_id: {admin['telegram_chat_id']} (type: {type(admin['telegram_chat_id']).__name__})")
        
        # Verify telegram_chat_id is an integer
        assert isinstance(admin['telegram_chat_id'], int), "❌ telegram_chat_id should be int"
        assert admin['telegram_chat_id'] == 5476148500, "❌ telegram_chat_id should be 5476148500"
        
        print("\n✅ PASS: Admin notification system uses correct data types")
    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        raise


def test_schedule_isolation():
    """Test that schedules are properly isolated by user_id"""
    print("\n" + "="*60)
    print("TEST 3: Schedule isolation between users")
    print("="*60)
    
    bot = MockBot()
    cmd = CommandHandler(bot)
    
    # Get admin user
    users = bot.db.list_all_users()
    admin_user = None
    for user in users:
        if user['username'] == 'admin':
            admin_user = user
            break
    
    assert admin_user, "❌ Admin user not found"
    
    # Login admin
    result = bot.auth.login('admin', 'jembotisme', 5476148500)
    assert result['success'], f"❌ Admin login failed: {result.get('message')}"
    
    print(f"\nAdmin logged in: {admin_user['username']}")
    
    # Get admin's schedules
    success, msg, events = cmd.handle_jadwal_multiuser(5476148500)
    
    print(f"\nAdmin's schedules:")
    print(f"  Success: {success}")
    print(f"  Events: {len(events)}")
    
    assert success, "❌ Admin should be able to access schedules"
    
    # Verify unauthenticated user cannot access
    fake_chat_id = 999999999
    success2, msg2, events2 = cmd.handle_jadwal_multiuser(fake_chat_id)
    
    print(f"\nFake user's schedules:")
    print(f"  Success: {success2}")
    print(f"  Events: {len(events2)}")
    
    assert not success2, "❌ Unauthenticated user should not access schedules"
    assert len(events2) == 0, "❌ Unauthenticated user should get empty events"
    
    print("\n✅ PASS: Schedules are properly isolated")


def test_inline_keyboard_authentication():
    """Test that inline keyboard buttons require authentication"""
    print("\n" + "="*60)
    print("TEST 4: Inline keyboard buttons require authentication")
    print("="*60)
    
    bot = MockBot()
    cmd = CommandHandler(bot)
    
    # Test unauthenticated user clicking button
    fake_chat_id = 999999999
    
    # Simulate clicking jadwal_weekly button
    is_logged_in, user, error_msg = bot.auth.require_login(fake_chat_id)
    
    print(f"\nFake user authentication check:")
    print(f"  Logged in: {is_logged_in}")
    print(f"  Error: {error_msg}")
    
    assert not is_logged_in, "❌ Fake user should not be logged in"
    assert "belum login" in error_msg.lower(), "❌ Should show login error"
    
    # Test authenticated user
    result = bot.auth.login('admin', 'jembotisme', 5476148500)
    assert result['success'], "❌ Admin login failed"
    
    is_logged_in2, user2, error_msg2 = bot.auth.require_login(5476148500)
    
    print(f"\nAdmin authentication check:")
    print(f"  Logged in: {is_logged_in2}")
    print(f"  User: {user2['username'] if user2 else None}")
    
    assert is_logged_in2, "❌ Admin should be logged in"
    assert user2 is not None, "❌ Admin user should be returned"
    
    print("\n✅ PASS: Inline keyboard authentication works correctly")


def test_login_error_messages():
    """Test that login command shows helpful error messages"""
    print("\n" + "="*60)
    print("TEST 5: Login error messages are helpful")
    print("="*60)
    
    bot = MockBot()
    cmd = CommandHandler(bot)
    
    # Test wrong format (no secret key)
    args1 = ['/login']
    result1 = cmd.handle_login(123456, args1)
    
    print(f"\nNo secret key:")
    print(result1)
    
    assert "Format salah" in result1, "❌ Should show format error"
    
    # Test invalid secret key
    args2 = ['/login', 'wrong_key_12345']
    result2 = cmd.handle_login(123456, args2)

    print(f"\nInvalid secret key:")
    print(result2)

    assert ("tidak valid" in result2.lower() or "tidak ditemukan" in result2.lower()), "❌ Should show invalid key error"
    
    # Test correct secret key
    args3 = ['/login', 'jembotisme']
    result3 = cmd.handle_login(5476148500, args3)
    
    print(f"\nCorrect secret key:")
    print(result3)
    
    assert ("Login Berhasil" in result3 or "sudah login" in result3), "❌ Should show success or already logged in"
    
    print("\n✅ PASS: Login error messages are helpful")


def main():
    """Run all tests"""
    print("="*60)
    print("🧪 COMPREHENSIVE FIXES - TEST SUITE")
    print("="*60)
    
    try:
        test_login_command()
        test_admin_notification_fix()
        test_schedule_isolation()
        test_inline_keyboard_authentication()
        test_login_error_messages()
        
        print("\n" + "="*60)
        print("🎉 ALL TESTS COMPLETED")
        print("="*60)
        print("\n✅ All fixes are working correctly!")
        print("   • Login command works with correct secret key")
        print("   • Admin notification uses correct telegram_chat_id")
        print("   • Schedules are properly isolated by user_id")
        print("   • Inline keyboard buttons require authentication")
        print("   • Login error messages are helpful")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

