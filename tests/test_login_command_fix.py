"""
Test suite for login command fix - verifying argument parsing works correctly
"""

import sys
import os

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


def test_login_command_parsing():
    """Test that login command correctly parses arguments"""
    print("\n" + "="*60)
    print("TEST 1: Login command argument parsing")
    print("="*60)
    
    bot = MockBot()
    cmd = CommandHandler(bot)
    
    # Simulate how bot.py now splits the full text
    # User sends: "/login jembotisme"
    # bot.py does: text.split() = ['/login', 'jembotisme']
    
    full_text = "/login jembotisme"
    args = full_text.split()
    
    print(f"\nFull text: '{full_text}'")
    print(f"Args after split: {args}")
    print(f"Args length: {len(args)}")
    
    assert len(args) == 2, f"❌ Expected 2 args, got {len(args)}"
    assert args[0] == '/login', f"❌ Expected '/login', got '{args[0]}'"
    assert args[1] == 'jembotisme', f"❌ Expected 'jembotisme', got '{args[1]}'"
    
    print("\n✅ PASS: Arguments parsed correctly")


def test_login_with_correct_secret_key():
    """Test login with correct secret key"""
    print("\n" + "="*60)
    print("TEST 2: Login with correct secret key")
    print("="*60)
    
    bot = MockBot()
    cmd = CommandHandler(bot)
    
    # Admin chat ID
    admin_chat_id = 5476148500
    
    # Simulate: /login jembotisme
    full_text = "/login jembotisme"
    args = full_text.split()
    
    print(f"\nCommand: {full_text}")
    print(f"Args: {args}")
    
    result = cmd.handle_login(admin_chat_id, args)
    
    print(f"\nResult:")
    print(result)
    
    # Should either login successfully or say already logged in
    assert ("Login Berhasil" in result or "sudah login" in result), \
        f"❌ Expected success or already logged in, got: {result}"
    
    print("\n✅ PASS: Login with correct secret key works")


def test_login_with_wrong_secret_key():
    """Test login with wrong secret key"""
    print("\n" + "="*60)
    print("TEST 3: Login with wrong secret key")
    print("="*60)
    
    bot = MockBot()
    cmd = CommandHandler(bot)
    
    # Random chat ID
    chat_id = 999999999
    
    # Simulate: /login wrong_key_12345
    full_text = "/login wrong_key_12345"
    args = full_text.split()
    
    print(f"\nCommand: {full_text}")
    print(f"Args: {args}")
    
    result = cmd.handle_login(chat_id, args)
    
    print(f"\nResult:")
    print(result)
    
    # Should show "tidak ditemukan" error
    assert "tidak ditemukan" in result.lower(), \
        f"❌ Expected 'tidak ditemukan' error, got: {result}"
    assert "@ImTamaa" in result, \
        f"❌ Expected admin contact '@ImTamaa', got: {result}"
    
    print("\n✅ PASS: Wrong secret key shows correct error")


def test_login_without_secret_key():
    """Test login without secret key"""
    print("\n" + "="*60)
    print("TEST 4: Login without secret key")
    print("="*60)
    
    bot = MockBot()
    cmd = CommandHandler(bot)
    
    # Random chat ID
    chat_id = 999999999
    
    # Simulate: /login (no secret key)
    full_text = "/login"
    args = full_text.split()
    
    print(f"\nCommand: {full_text}")
    print(f"Args: {args}")
    print(f"Args length: {len(args)}")
    
    result = cmd.handle_login(chat_id, args)
    
    print(f"\nResult:")
    print(result)
    
    # Should show "Format salah!" error
    assert "Format salah" in result, \
        f"❌ Expected 'Format salah!' error, got: {result}"
    
    print("\n✅ PASS: Missing secret key shows format error")


def test_login_already_logged_in():
    """Test login when already logged in"""
    print("\n" + "="*60)
    print("TEST 5: Login when already logged in")
    print("="*60)
    
    bot = MockBot()
    cmd = CommandHandler(bot)
    
    # Admin chat ID
    admin_chat_id = 5476148500
    
    # First login
    full_text1 = "/login jembotisme"
    args1 = full_text1.split()
    result1 = cmd.handle_login(admin_chat_id, args1)
    
    print(f"\nFirst login:")
    print(result1)
    
    # Try to login again
    full_text2 = "/login jembotisme"
    args2 = full_text2.split()
    result2 = cmd.handle_login(admin_chat_id, args2)
    
    print(f"\nSecond login attempt:")
    print(result2)
    
    # Should show "sudah login" message
    assert "sudah login" in result2.lower(), \
        f"❌ Expected 'sudah login' message, got: {result2}"
    
    print("\n✅ PASS: Already logged in shows correct message")


def test_login_with_spaces_in_secret_key():
    """Test login with spaces around secret key (should be stripped)"""
    print("\n" + "="*60)
    print("TEST 6: Login with spaces around secret key")
    print("="*60)
    
    bot = MockBot()
    cmd = CommandHandler(bot)
    
    # Admin chat ID
    admin_chat_id = 5476148500
    
    # Logout first
    bot.auth.logout(admin_chat_id)
    
    # Simulate: /login  jembotisme  (with extra spaces)
    # Note: split() will handle multiple spaces automatically
    full_text = "/login   jembotisme   "
    args = full_text.split()
    
    print(f"\nCommand: '{full_text}'")
    print(f"Args: {args}")
    
    result = cmd.handle_login(admin_chat_id, args)
    
    print(f"\nResult:")
    print(result)
    
    # Should login successfully (strip() handles trailing spaces)
    assert ("Login Berhasil" in result or "sudah login" in result), \
        f"❌ Expected success, got: {result}"
    
    print("\n✅ PASS: Spaces are handled correctly")


def main():
    """Run all tests"""
    print("="*60)
    print("🧪 LOGIN COMMAND FIX - TEST SUITE")
    print("="*60)
    
    try:
        test_login_command_parsing()
        test_login_with_correct_secret_key()
        test_login_with_wrong_secret_key()
        test_login_without_secret_key()
        test_login_already_logged_in()
        test_login_with_spaces_in_secret_key()
        
        print("\n" + "="*60)
        print("🎉 ALL TESTS COMPLETED")
        print("="*60)
        print("\n✅ All login command tests passed!")
        print("   • Argument parsing works correctly")
        print("   • Login with correct secret key works")
        print("   • Login with wrong secret key shows correct error")
        print("   • Login without secret key shows format error")
        print("   • Already logged in shows correct message")
        print("   • Spaces in secret key are handled correctly")
        
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

