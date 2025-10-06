"""
Admin module for KRS Reminder Bot
Handles admin operations: user management, schedule import, etc.
"""
import json
from typing import Optional, Dict, List
from datetime import datetime
import pytz


class AdminManager:
    """Manages admin operations for KRS Reminder Bot"""
    
    def __init__(self, db_client, auth_manager, calendar_service_getter):
        """
        Initialize AdminManager
        
        Args:
            db_client: SupabaseClient instance
            auth_manager: AuthManager instance
            calendar_service_getter: Function to get Google Calendar service
        """
        self.db = db_client
        self.auth = auth_manager
        self.get_calendar_service = calendar_service_getter
        self.tz = pytz.timezone('Asia/Jakarta')
    
    def is_admin(self, telegram_chat_id: int) -> bool:
        """Check if user is admin"""
        return self.db.is_admin(telegram_chat_id)
    
    def require_admin(self, telegram_chat_id: int) -> tuple[bool, str]:
        """
        Check if user is admin
        
        Returns:
            Tuple of (is_admin, error_message)
        """
        if self.is_admin(telegram_chat_id):
            return (True, '')
        else:
            return (False, '❌ Anda bukan admin. Perintah ini hanya untuk admin.')
    
    # ============================================================
    # USER MANAGEMENT
    # ============================================================
    
    def add_user(self, username: str, secret_key: Optional[str] = None) -> Dict:
        """
        Add a new user
        
        Args:
            username: Username
            secret_key: Secret key (generated if not provided)
            
        Returns:
            Dict with 'success', 'message', 'user_id', 'secret_key'
        """
        # Check if username already exists
        existing_user = self.db.get_user_by_username(username)
        if existing_user:
            return {
                'success': False,
                'message': f'❌ Username "{username}" sudah ada'
            }
        
        # Generate secret key if not provided
        if not secret_key:
            secret_key = self.auth.generate_secret_key()
        
        # Hash secret key
        secret_key_hash = self.auth.hash_secret_key(secret_key)
        
        # Create user
        user = self.db.create_user(username, secret_key_hash)
        
        if not user:
            return {
                'success': False,
                'message': '❌ Gagal membuat user'
            }
        
        return {
            'success': True,
            'message': f'✅ User "{username}" berhasil dibuat',
            'user_id': user['user_id'],
            'username': username,
            'secret_key': secret_key
        }
    
    def delete_user(self, user_id: str) -> Dict:
        """Delete a user"""
        user = self.db.get_user_by_id(user_id)
        if not user:
            return {
                'success': False,
                'message': f'❌ User dengan ID {user_id} tidak ditemukan'
            }
        
        success = self.db.delete_user(user_id)
        
        if success:
            return {
                'success': True,
                'message': f'✅ User "{user[" username"]}" berhasil dihapus'
            }
        else:
            return {
                'success': False,
                'message': '❌ Gagal menghapus user'
            }
    
    def list_users(self) -> Dict:
        """List all users"""
        users = self.db.list_all_users()
        
        return {
            'success': True,
            'users': users,
            'count': len(users)
        }
    
    # ============================================================
    # CALENDAR MANAGEMENT
    # ============================================================
    
    def setup_calendar(self, user_id: str, calendar_token_json: str) -> Dict:
        """
        Setup Google Calendar token for a user
        
        Args:
            user_id: User ID
            calendar_token_json: Google Calendar token as JSON string
            
        Returns:
            Dict with 'success' and 'message'
        """
        user = self.db.get_user_by_id(user_id)
        if not user:
            return {
                'success': False,
                'message': f'❌ User dengan ID {user_id} tidak ditemukan'
            }
        
        # Encrypt token
        try:
            encrypted_token = self.auth.encrypt_calendar_token(calendar_token_json)
        except Exception as e:
            return {
                'success': False,
                'message': f'❌ Gagal encrypt token: {e}'
            }
        
        # Save to database
        success = self.db.update_user_calendar_token(user_id, encrypted_token)
        
        if success:
            return {
                'success': True,
                'message': f'✅ Calendar token berhasil di-setup untuk user "{user["username"]}"'
            }
        else:
            return {
                'success': False,
                'message': '❌ Gagal menyimpan calendar token'
            }
    
    def import_schedule(self, user_id: str, days_ahead: int = 30) -> Dict:
        """
        Import schedule from Google Calendar for a user
        
        Args:
            user_id: User ID
            days_ahead: Number of days to import
            
        Returns:
            Dict with 'success', 'message', 'count'
        """
        user = self.db.get_user_by_id(user_id)
        if not user:
            return {
                'success': False,
                'message': f'❌ User dengan ID {user_id} tidak ditemukan'
            }
        
        # Get calendar token
        if not user.get('google_calendar_token_encrypted'):
            return {
                'success': False,
                'message': f'❌ User "{user["username"]}" belum setup calendar token'
            }
        
        # Decrypt token
        try:
            token_json = self.auth.decrypt_calendar_token(user['google_calendar_token_encrypted'])
            # TODO: Use token to get calendar service
            # For now, we'll use the default calendar service
        except Exception as e:
            return {
                'success': False,
                'message': f'❌ Gagal decrypt token: {e}'
            }
        
        # Get events from Google Calendar
        try:
            service = self.get_calendar_service()
            now = datetime.now(self.tz)
            end_time = now + pytz.timedelta(days=days_ahead)
            
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now.isoformat(),
                timeMax=end_time.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
        except Exception as e:
            return {
                'success': False,
                'message': f'❌ Gagal fetch events dari Google Calendar: {e}'
            }
        
        # Parse and save events to database
        schedules = []
        for event in events:
            schedule_data = self._parse_event_to_schedule(event)
            if schedule_data:
                schedules.append({
                    'user_id': user_id,
                    **schedule_data
                })
        
        # Delete old schedules
        self.db.delete_user_schedules(user_id)
        
        # Bulk insert new schedules
        if schedules:
            success = self.db.bulk_create_schedules(schedules)
            if success:
                return {
                    'success': True,
                    'message': f'✅ Berhasil import {len(schedules)} jadwal untuk user "{user["username"]}"',
                    'count': len(schedules)
                }
            else:
                return {
                    'success': False,
                    'message': '❌ Gagal menyimpan jadwal ke database'
                }
        else:
            return {
                'success': True,
                'message': f'⚠️  Tidak ada jadwal ditemukan untuk user "{user["username"]}"',
                'count': 0
            }
    
    def _parse_event_to_schedule(self, event: Dict) -> Optional[Dict]:
        """Parse Google Calendar event to schedule format"""
        try:
            start = event.get('start', {}).get('dateTime')
            end = event.get('end', {}).get('dateTime')
            
            if not start or not end:
                return None
            
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
            
            # Convert to Jakarta timezone
            if start_dt.tzinfo is None:
                start_dt = self.tz.localize(start_dt)
            else:
                start_dt = start_dt.astimezone(self.tz)
            
            if end_dt.tzinfo is None:
                end_dt = self.tz.localize(end_dt)
            else:
                end_dt = end_dt.astimezone(self.tz)
            
            # Extract course info from description
            description = event.get('description', '')
            facilitator = self._extract_facilitator(description)
            course_code = self._extract_course_code(description)
            class_type = self._infer_class_type(event.get('summary', ''), event.get('location', ''))
            
            return {
                'course_name': event.get('summary', 'No Title').replace('📚 ', ''),
                'course_code': course_code,
                'day_of_week': start_dt.weekday(),  # 0=Monday
                'start_time': start_dt.isoformat(),
                'end_time': end_dt.isoformat(),
                'location': event.get('location', ''),
                'facilitator': facilitator,
                'class_type': class_type,
                'google_event_id': event.get('id', '')
            }
        
        except Exception as e:
            print(f"❌ Error parsing event: {e}")
            return None
    
    @staticmethod
    def _extract_facilitator(description: str) -> str:
        """Extract facilitator from description"""
        for line in description.split('\n'):
            if 'Dosen:' in line or '👨‍🏫' in line:
                return line.split(':')[-1].strip()
        return ''
    
    @staticmethod
    def _extract_course_code(description: str) -> str:
        """Extract course code from description"""
        for line in description.split('\n'):
            if 'Kode:' in line or '🔢' in line:
                return line.split(':')[-1].strip()
        return ''
    
    @staticmethod
    def _infer_class_type(summary: str, location: str) -> str:
        """Infer class type from summary and location"""
        summary_lower = summary.lower()
        location_lower = location.lower()
        
        if 'lab' in location_lower or 'praktikum' in summary_lower:
            return 'Praktikum'
        elif 'seminar' in summary_lower:
            return 'Seminar'
        else:
            return 'Kuliah Teori'

