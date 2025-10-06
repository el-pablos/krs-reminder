#!/usr/bin/env python3
"""
Setup database tables programmatically using Supabase Management API
"""
import json
import requests
import sys

def setup_database():
    print("="*60)
    print("🔧 Setting Up Database Tables")
    print("="*60)
    
    # Load config
    with open('configs/supabase/config.json', 'r') as f:
        config = json.load(f)
    
    # Supabase Management API endpoint
    project_ref = "qdklwiuazobrmyjrofdq"
    
    # Read migration SQL
    with open('migrations/001_initial_schema.sql', 'r') as f:
        migration_sql = f.read()
    
    print(f"\n📄 Migration SQL loaded ({len(migration_sql)} chars)")
    
    # Use PostgREST to execute SQL via stored procedure
    # First, let's check if we can query existing tables
    
    url = f"{config['url']}/rest/v1/"
    headers = {
        'apikey': config['service_role_key'],
        'Authorization': f"Bearer {config['service_role_key']}",
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    
    print("\n🔍 Checking existing tables...")
    
    # Try to query a table to see if it exists
    try:
        response = requests.get(
            f"{url}users?limit=1",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ 'users' table already exists!")
            return True
        elif response.status_code == 404:
            print("⚠️  'users' table not found - need to create tables")
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            print(f"   {response.text}")
    
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
    
    print("\n" + "="*60)
    print("📝 MANUAL SETUP REQUIRED")
    print("="*60)
    print("\nPlease run the migration SQL manually:")
    print(f"\n1. Open: https://supabase.com/dashboard/project/{project_ref}/sql/new")
    print("2. Copy content from: migrations/001_initial_schema.sql")
    print("3. Paste and click 'Run'")
    print("4. Verify tables created")
    print("\nAfter that, run this script again to verify.")
    
    return False

if __name__ == '__main__':
    success = setup_database()
    sys.exit(0 if success else 1)

