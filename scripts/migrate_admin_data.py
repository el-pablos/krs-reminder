#!/usr/bin/env python3
"""
Migrate admin's schedule data from backup to database
"""
import sys
import json
from pathlib import Path
import datetime
import pytz

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from krs_reminder.database import SupabaseClient
from krs_reminder.auth import AuthManager

def migrate_admin_data():
    print("="*60)
    print("📦 PHASE 4: Data Migration - Admin Schedule")
    print("="*60)
    
    # Initialize
    db = SupabaseClient()
    auth = AuthManager(db)
    tz = pytz.timezone('Asia/Jakarta')
    
    # Admin info
    admin_telegram_id = 5476148500
    admin_username = "admin"
    admin_secret_key = "admin_krs_2025"
    
    print(f"\n👤 Admin: {admin_username}")
    print(f"📱 Telegram ID: {admin_telegram_id}")
    
    # Step 1: Create admin user
    print("\n📝 Step 1: Create admin user...")
    existing_user = db.get_user_by_username(admin_username)
    
    if existing_user:
        print(f"✅ Admin user already exists: {existing_user['user_id']}")
        admin_user_id = existing_user['user_id']
    else:
        secret_hash = auth.hash_secret_key(admin_secret_key)
        admin_user = db.create_user(admin_username, secret_hash)
        if admin_user:
            admin_user_id = admin_user['user_id']
            print(f"✅ Admin user created: {admin_user_id}")
        else:
            print("❌ Failed to create admin user")
            return False
    
    # Step 2: Ensure admin in admins table
    print("\n📝 Step 2: Ensure admin in admins table...")
    if db.is_admin(admin_telegram_id):
        print("✅ Admin already in admins table")
    else:
        if db.add_admin(admin_telegram_id):
            print("✅ Admin added to admins table")
        else:
            print("⚠️  Could not add to admins table (may need manual SQL)")
    
    # Step 3: Load backup data
    print("\n📝 Step 3: Load backup data...")
    backup_file = Path('var/backup_admin_schedule.json')
    
    if not backup_file.exists():
        print(f"❌ Backup file not found: {backup_file}")
        return False
    
    with open(backup_file, 'r') as f:
        backup_data = json.load(f)
    
    events = backup_data['events']
    print(f"✅ Loaded {len(events)} events from backup")
    
    # Step 4: Parse and insert schedules
    print("\n📝 Step 4: Parse and insert schedules...")
    
    schedules = []
    for event in events:
        try:
            # Parse start/end times
            start_str = event['start']
            end_str = event['end']
            
            start_dt = datetime.datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            end_dt = datetime.datetime.fromisoformat(end_str.replace('Z', '+00:00'))
            
            # Convert to Jakarta timezone
            if start_dt.tzinfo is None:
                start_dt = tz.localize(start_dt)
            else:
                start_dt = start_dt.astimezone(tz)
            
            if end_dt.tzinfo is None:
                end_dt = tz.localize(end_dt)
            else:
                end_dt = end_dt.astimezone(tz)
            
            # Extract info from description
            description = event.get('description', '')
            facilitator = extract_facilitator(description)
            course_code = extract_course_code(description)
            
            # Clean course name
            course_name = event['summary'].replace('📚 ', '')
            
            # Infer class type
            location = event.get('location', '')
            class_type = infer_class_type(course_name, location)
            
            schedule = {
                'user_id': admin_user_id,
                'course_name': course_name,
                'course_code': course_code,
                'day_of_week': start_dt.weekday(),
                'start_time': start_dt.isoformat(),
                'end_time': end_dt.isoformat(),
                'location': location,
                'facilitator': facilitator,
                'class_type': class_type,
                'google_event_id': event.get('event_id', '')
            }
            
            schedules.append(schedule)
            
        except Exception as e:
            print(f"⚠️  Error parsing event: {e}")
            continue
    
    print(f"✅ Parsed {len(schedules)} schedules")
    
    # Step 5: Delete old schedules
    print("\n📝 Step 5: Delete old schedules...")
    if db.delete_user_schedules(admin_user_id):
        print("✅ Old schedules deleted")
    
    # Step 6: Bulk insert
    print("\n📝 Step 6: Bulk insert schedules...")
    if db.bulk_create_schedules(schedules):
        print(f"✅ Inserted {len(schedules)} schedules")
    else:
        print("❌ Failed to insert schedules")
        return False
    
    # Step 7: Verify
    print("\n📝 Step 7: Verify...")
    now = datetime.datetime.now(tz)
    end_time = now + datetime.timedelta(days=30)
    
    saved_schedules = db.get_user_schedules(admin_user_id, now, end_time)
    print(f"✅ Verified: {len(saved_schedules)} schedules in database")
    
    print("\n" + "="*60)
    print("✅ PHASE 4 COMPLETE: Data Migration Success!")
    print("="*60)
    print(f"\n📊 Summary:")
    print(f"  • Admin User ID: {admin_user_id}")
    print(f"  • Admin Username: {admin_username}")
    print(f"  • Admin Secret Key: {admin_secret_key}")
    print(f"  • Total Schedules: {len(saved_schedules)}")
    print(f"\n💡 Admin can now login with:")
    print(f"   /login {admin_secret_key}")
    
    return True

def extract_facilitator(description: str) -> str:
    """Extract facilitator from description"""
    for line in description.split('\n'):
        if 'Dosen:' in line or '👨‍🏫' in line:
            return line.split(':')[-1].strip()
    return ''

def extract_course_code(description: str) -> str:
    """Extract course code from description"""
    for line in description.split('\n'):
        if 'Kode:' in line or '🔢' in line:
            return line.split(':')[-1].strip()
    return ''

def infer_class_type(course_name: str, location: str) -> str:
    """Infer class type"""
    name_lower = course_name.lower()
    loc_lower = location.lower()
    
    if 'lab' in loc_lower or 'praktikum' in name_lower:
        return 'Praktikum'
    elif 'seminar' in name_lower:
        return 'Seminar'
    else:
        return 'Kuliah Teori'

if __name__ == '__main__':
    try:
        success = migrate_admin_data()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

