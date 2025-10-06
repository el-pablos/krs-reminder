"""
Tests for multi-user functionality
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_database_module():
    """Test database module can be imported"""
    try:
        from krs_reminder.database import SupabaseClient
        print("✅ Database module imported")
        return True
    except Exception as e:
        print(f"❌ Database module error: {e}")
        return False

def test_auth_module():
    """Test auth module"""
    try:
        from krs_reminder.auth import AuthManager
        
        # Test password hashing
        secret = "test123"
        hashed = AuthManager.hash_secret_key(secret)
        assert AuthManager.verify_secret_key(secret, hashed)
        assert not AuthManager.verify_secret_key("wrong", hashed)
        
        print("✅ Auth module working")
        return True
    except Exception as e:
        print(f"❌ Auth module error: {e}")
        return False

def test_admin_module():
    """Test admin module can be imported"""
    try:
        from krs_reminder.admin import AdminManager
        print("✅ Admin module imported")
        return True
    except Exception as e:
        print(f"❌ Admin module error: {e}")
        return False

def test_commands_module():
    """Test commands module"""
    try:
        from krs_reminder.commands import CommandHandler
        print("✅ Commands module imported")
        return True
    except Exception as e:
        print(f"❌ Commands module error: {e}")
        return False

def test_bot_multiuser_init():
    """Test bot can initialize with multi-user support"""
    try:
        from krs_reminder.bot import KRSReminderBotV2
        bot = KRSReminderBotV2()
        
        # Check multi-user attributes
        assert hasattr(bot, 'multi_user_enabled')
        assert hasattr(bot, 'db')
        assert hasattr(bot, 'auth')
        assert hasattr(bot, 'admin')
        assert hasattr(bot, 'cmd_handler')
        
        print(f"✅ Bot initialized (multi-user: {bot.multi_user_enabled})")
        return True
    except Exception as e:
        print(f"❌ Bot init error: {e}")
        return False

def run_all_tests():
    """Run all multi-user tests"""
    print("="*60)
    print("🧪 Multi-User Tests")
    print("="*60)
    
    tests = [
        ("Database Module", test_database_module),
        ("Auth Module", test_auth_module),
        ("Admin Module", test_admin_module),
        ("Commands Module", test_commands_module),
        ("Bot Multi-User Init", test_bot_multiuser_init),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n📝 Test: {name}")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Test failed: {e}")
            results.append((name, False))
    
    print("\n" + "="*60)
    print("📊 Test Results")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} tests passed")
    print(f"{'='*60}")
    
    return passed == total

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

