#!/usr/bin/env python3
"""
Create tables directly using psycopg2 with connection string
"""
import sys
import json
from pathlib import Path

def create_tables():
    print("="*60)
    print("🗄️  Creating Database Tables")
    print("="*60)
    
    # Load Supabase config
    config_path = Path('configs/supabase/config.json')
    with open(config_path) as f:
        config = json.load(f)
    
    db_url = config['db_url']
    
    print(f"\n📡 Connecting to database...")
    print(f"   Host: db.qdklwiuazobrmyjrofdq.supabase.co")
    
    try:
        import psycopg2
        
        # Try to connect
        conn = psycopg2.connect(db_url)
        print("✅ Connected to database")
        
        # Read migration SQL
        migration_file = Path('migrations/001_initial_schema.sql')
        with open(migration_file) as f:
            sql = f.read()
        
        print("\n📝 Executing migration SQL...")
        
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        
        print("✅ Tables created successfully")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n⚠️  Direct connection failed")
        print("\n📝 Alternative: Manual setup via Supabase Dashboard")
        print("   1. Go to: https://supabase.com/dashboard/project/qdklwiuazobrmyjrofdq")
        print("   2. Click 'SQL Editor'")
        print("   3. Create new query")
        print("   4. Copy-paste content from: migrations/001_initial_schema.sql")
        print("   5. Click 'Run'")
        return False

if __name__ == '__main__':
    success = create_tables()
    sys.exit(0 if success else 1)

