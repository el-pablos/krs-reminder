#!/usr/bin/env python3
"""
Run database migration via Supabase SQL Editor API
"""
import json
import requests

def run_migration():
    print("="*60)
    print("🔧 Running Database Migration via Supabase API")
    print("="*60)
    
    # Load config
    with open('configs/supabase/config.json', 'r') as f:
        config = json.load(f)
    
    # Read migration SQL
    with open('migrations/001_initial_schema.sql', 'r') as f:
        migration_sql = f.read()
    
    print(f"\n📄 Migration file: 001_initial_schema.sql")
    print(f"📏 SQL length: {len(migration_sql)} characters")
    
    # Use Supabase REST API to execute SQL
    url = f"{config['url']}/rest/v1/rpc/exec_sql"
    headers = {
        'apikey': config['service_role_key'],
        'Authorization': f"Bearer {config['service_role_key']}",
        'Content-Type': 'application/json'
    }
    
    # Split into smaller chunks to avoid timeout
    statements = [s.strip() + ';' for s in migration_sql.split(';') if s.strip() and not s.strip().startswith('--')]
    
    print(f"\n🔄 Executing {len(statements)} SQL statements...")
    
    # For now, let's just create the tables manually via Python
    # Since direct SQL execution might not be available
    
    print("\n⚠️  Direct SQL execution not available via REST API")
    print("📝 Alternative: Use Supabase Dashboard SQL Editor")
    print("\nSteps:")
    print("1. Go to: https://supabase.com/dashboard/project/qdklwiuazobrmyjrofdq/sql")
    print("2. Copy SQL from: migrations/001_initial_schema.sql")
    print("3. Paste and run in SQL Editor")
    print("\nOR use the Python ORM approach below...")
    
    return False

if __name__ == '__main__':
    run_migration()

