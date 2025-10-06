#!/usr/bin/env python3
"""
Setup database tables via Supabase REST API
Workaround for direct SQL execution
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from krs_reminder.database import SupabaseClient

def setup_tables():
    print("="*60)
    print("🗄️  PHASE 7.1: Setup Database Tables")
    print("="*60)
    
    db = SupabaseClient()
    
    # Test connection
    print("\n📡 Testing Supabase connection...")
    try:
        # Try to query users table
        response = db._request('GET', '/users', params={'limit': 1})
        print("✅ Connection successful")
        print("✅ Tables already exist (users table accessible)")
        return True
    except Exception as e:
        error_str = str(e)
        if 'relation "public.users" does not exist' in error_str or '404' in error_str:
            print("⚠️  Tables don't exist yet")
            print("\n📝 Manual action required:")
            print("   1. Go to: https://supabase.com/dashboard/project/qdklwiuazobrmyjrofdq")
            print("   2. Click 'SQL Editor'")
            print("   3. Copy content from: migrations/001_initial_schema.sql")
            print("   4. Paste and run in SQL Editor")
            print("   5. Re-run this script")
            return False
        else:
            print(f"❌ Connection error: {e}")
            return False

def verify_admin():
    """Verify admin exists in admins table"""
    print("\n📝 Verifying admin...")
    
    db = SupabaseClient()
    admin_telegram_id = 5476148500
    
    try:
        if db.is_admin(admin_telegram_id):
            print(f"✅ Admin exists (telegram_id: {admin_telegram_id})")
            return True
        else:
            print(f"⚠️  Admin not found, attempting to add...")
            if db.add_admin(admin_telegram_id):
                print(f"✅ Admin added successfully")
                return True
            else:
                print(f"❌ Failed to add admin")
                return False
    except Exception as e:
        print(f"⚠️  Could not verify admin: {e}")
        print("   Admin will be created during migration")
        return True  # Continue anyway

if __name__ == '__main__':
    print("\n🔧 Database Setup Script")
    print("="*60)
    
    # Step 1: Check tables
    tables_ok = setup_tables()
    
    if not tables_ok:
        print("\n" + "="*60)
        print("⚠️  MANUAL SETUP REQUIRED")
        print("="*60)
        print("\nPlease create tables manually via Supabase Dashboard")
        print("Then re-run this script to verify")
        sys.exit(1)
    
    # Step 2: Verify admin
    admin_ok = verify_admin()
    
    print("\n" + "="*60)
    if tables_ok and admin_ok:
        print("✅ Database Setup Complete")
        print("="*60)
        print("\n📝 Next steps:")
        print("   1. Run: python3 scripts/migrate_admin_data.py")
        print("   2. Test bot: python3 -m krs_reminder.cli.run_bot")
        sys.exit(0)
    else:
        print("⚠️  Setup Incomplete")
        print("="*60)
        sys.exit(1)

