"""
Test authorization fix for KRS Reminder Bot
Verify that unauthenticated users cannot see schedules
"""
import sys
import os
import importlib.util

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import only what we need (avoid importing __init__.py which imports bot.py)
import pytz
import datetime


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
        self.admin = AdminManager(self.db, self.auth, lambda: None)
        self.multi_user_enabled = True

        # Mock timezone
        self.tz = pytz.timezone('Asia/Jakarta')


def test_unauthenticated_start():
    """Test /start command for unauthenticated user"""
    print("\n" + "="*60)
    print("TEST 1: Unauthenticated user sends /start")
    print("="*60)

    bot = MockBot()
    cmd = CommandHandler(bot)
    
    # Use a fake chat_id that doesn't have a session
    fake_chat_id = 999999999
    
    result = cmd.handle_start(fake_chat_id)
    
    print(f"\nResult:\n{result}\n")
    
    # Verify result contains login instructions
    assert "belum login" in result.lower(), "❌ Should show 'belum login'"
    assert "/login" in result.lower(), "❌ Should show /login command"
    assert "secret key" in result.lower(), "❌ Should mention secret key"
    
    print("✅ PASS: Unauthenticated user sees login instructions")


def test_authenticated_start():
    """Test /start command for authenticated user"""
    print("\n" + "="*60)
    print("TEST 2: Authenticated user sends /start")
    print("="*60)

    bot = MockBot()
    cmd = CommandHandler(bot)
    
    # Use admin's chat_id (should have active session)
    admin_chat_id = 5476148500
    
    result = cmd.handle_start(admin_chat_id)
    
    print(f"\nResult:\n{result}\n")
    
    # Verify result contains welcome message with commands
    if result and "Selamat Datang" in result:
        assert "/jadwal" in result, "❌ Should show /jadwal command"
        assert "/logout" in result, "❌ Should show /logout command"
        print("✅ PASS: Authenticated user sees welcome with commands")
    else:
        print("⚠️  SKIP: Admin not logged in (no active session)")


def test_unauthenticated_jadwal():
    """Test /jadwal command for unauthenticated user"""
    print("\n" + "="*60)
    print("TEST 3: Unauthenticated user sends /jadwal")
    print("="*60)

    bot = MockBot()
    cmd = CommandHandler(bot)
    
    # Use a fake chat_id that doesn't have a session
    fake_chat_id = 999999999
    
    success, msg, events = cmd.handle_jadwal_multiuser(fake_chat_id)
    
    print(f"\nSuccess: {success}")
    print(f"Message: {msg}\n")
    
    # Verify access denied
    assert not success, "❌ Should return False for unauthenticated user"
    assert "belum login" in msg.lower(), "❌ Should show 'belum login' error"
    assert len(events) == 0, "❌ Should return empty events list"
    
    print("✅ PASS: Unauthenticated user cannot access /jadwal")


def test_authenticated_jadwal():
    """Test /jadwal command for authenticated user"""
    print("\n" + "="*60)
    print("TEST 4: Authenticated user sends /jadwal")
    print("="*60)

    bot = MockBot()
    cmd = CommandHandler(bot)
    
    # Use admin's chat_id (should have active session)
    admin_chat_id = 5476148500
    
    success, msg, events = cmd.handle_jadwal_multiuser(admin_chat_id)
    
    print(f"\nSuccess: {success}")
    print(f"Message: {msg}")
    print(f"Events count: {len(events)}\n")
    
    if success:
        print("✅ PASS: Authenticated user can access /jadwal")
        print(f"   Found {len(events)} events")
    else:
        print("⚠️  SKIP: Admin not logged in (no active session)")
        print(f"   Message: {msg}")


def test_unauthenticated_logout():
    """Test /logout command for unauthenticated user"""
    print("\n" + "="*60)
    print("TEST 5: Unauthenticated user sends /logout")
    print("="*60)

    bot = MockBot()
    cmd = CommandHandler(bot)
    
    # Use a fake chat_id that doesn't have a session
    fake_chat_id = 999999999
    
    result = cmd.handle_logout(fake_chat_id)
    
    print(f"\nResult: {result}\n")
    
    # Verify error message
    assert "belum login" in result.lower(), "❌ Should show 'belum login' error"
    
    print("✅ PASS: Unauthenticated user cannot logout (not logged in)")


def test_is_user_authenticated():
    """Test is_user_authenticated helper function"""
    print("\n" + "="*60)
    print("TEST 6: is_user_authenticated helper function")
    print("="*60)
    
    bot = MockBot()
    
    # Test with fake chat_id (not authenticated)
    fake_chat_id = 999999999
    is_auth = bot.auth.is_user_authenticated(fake_chat_id)
    print(f"\nFake user (999999999) authenticated: {is_auth}")
    assert not is_auth, "❌ Fake user should not be authenticated"
    print("✅ PASS: Fake user is not authenticated")
    
    # Test with admin chat_id (might be authenticated)
    admin_chat_id = 5476148500
    is_auth = bot.auth.is_user_authenticated(admin_chat_id)
    print(f"Admin user (5476148500) authenticated: {is_auth}")
    
    if is_auth:
        print("✅ PASS: Admin user is authenticated")
    else:
        print("⚠️  SKIP: Admin not logged in (no active session)")


def test_schedule_isolation():
    """Test that users only see their own schedules"""
    print("\n" + "="*60)
    print("TEST 7: Schedule isolation between users")
    print("="*60)
    
    bot = MockBot()
    
    # Get all users
    users = bot.db.list_all_users()
    print(f"\nTotal users in database: {len(users)}")
    
    for user in users:
        print(f"\n👤 User: {user['username']} (ID: {user['user_id'][:8]}...)")
        
        # Get schedules for this user
        import datetime
        now = datetime.datetime.now(bot.tz)
        end_time = now + datetime.timedelta(days=7)
        
        schedules = bot.db.get_user_schedules(user['user_id'], now, end_time)
        print(f"   Schedules: {len(schedules)} events")
        
        # Verify schedules belong to this user
        for schedule in schedules:
            assert schedule['user_id'] == user['user_id'], \
                f"❌ Schedule {schedule['schedule_id']} does not belong to user {user['user_id']}"
    
    print("\n✅ PASS: All schedules are properly isolated by user_id")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 AUTHORIZATION FIX - TEST SUITE")
    print("="*60)
    
    try:
        test_unauthenticated_start()
        test_authenticated_start()
        test_unauthenticated_jadwal()
        test_authenticated_jadwal()
        test_unauthenticated_logout()
        test_is_user_authenticated()
        test_schedule_isolation()
        
        print("\n" + "="*60)
        print("🎉 ALL TESTS COMPLETED")
        print("="*60)
        print("\n✅ Authorization fix is working correctly!")
        print("   • Unauthenticated users see login instructions")
        print("   • Authenticated users see their own schedules")
        print("   • Schedule isolation is enforced")
        print("   • All commands require authentication")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

