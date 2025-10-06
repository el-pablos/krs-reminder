"""
Database module for KRS Reminder Bot - Multi-User Support
Handles all Supabase database operations
"""
import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import requests


class SupabaseClient:
    """Supabase database client for KRS Reminder Bot"""
    
    def __init__(self, config_path: str = 'configs/supabase/config.json'):
        """Initialize Supabase client"""
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.url = self.config['url']
        self.service_key = self.config['service_role_key']
        self.base_url = f"{self.url}/rest/v1"
        
        # Headers for API requests
        self.headers = {
            'apikey': self.service_key,
            'Authorization': f"Bearer {self.service_key}",
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
        """Make HTTP request to Supabase"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, headers=self.headers, json=data, params=params, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers, params=params, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json() if response.text else {}
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Database request error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Response: {e.response.text}")
            raise
    
    # ============================================================
    # USER OPERATIONS
    # ============================================================
    
    def create_user(self, username: str, secret_key_hash: str) -> Optional[Dict]:
        """Create a new user"""
        data = {
            'username': username,
            'secret_key_hash': secret_key_hash
        }
        try:
            result = self._request('POST', 'users', data=data)
            return result[0] if isinstance(result, list) and result else result
        except Exception as e:
            print(f"❌ Error creating user: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        try:
            params = {'username': f'eq.{username}', 'limit': 1}
            result = self._request('GET', 'users', params=params)
            return result[0] if result else None
        except Exception as e:
            print(f"❌ Error getting user: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        try:
            params = {'user_id': f'eq.{user_id}', 'limit': 1}
            result = self._request('GET', 'users', params=params)
            return result[0] if result else None
        except Exception as e:
            print(f"❌ Error getting user: {e}")
            return None
    
    def update_user_calendar_token(self, user_id: str, encrypted_token: str) -> bool:
        """Update user's Google Calendar token"""
        try:
            data = {'google_calendar_token_encrypted': encrypted_token}
            params = {'user_id': f'eq.{user_id}'}
            self._request('PATCH', 'users', data=data, params=params)
            return True
        except Exception as e:
            print(f"❌ Error updating calendar token: {e}")
            return False
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        try:
            params = {'user_id': f'eq.{user_id}'}
            self._request('DELETE', 'users', params=params)
            return True
        except Exception as e:
            print(f"❌ Error deleting user: {e}")
            return False
    
    def list_all_users(self) -> List[Dict]:
        """List all users"""
        try:
            result = self._request('GET', 'users')
            return result if isinstance(result, list) else []
        except Exception as e:
            print(f"❌ Error listing users: {e}")
            return []
    
    # ============================================================
    # SCHEDULE OPERATIONS
    # ============================================================
    
    def create_schedule(self, user_id: str, schedule_data: Dict) -> Optional[Dict]:
        """Create a new schedule entry"""
        data = {
            'user_id': user_id,
            **schedule_data
        }
        try:
            result = self._request('POST', 'schedules', data=data)
            return result[0] if isinstance(result, list) and result else result
        except Exception as e:
            print(f"❌ Error creating schedule: {e}")
            return None
    
    def get_user_schedules(self, user_id: str, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> List[Dict]:
        """Get schedules for a user"""
        try:
            params = {'user_id': f'eq.{user_id}', 'order': 'start_time.asc'}
            
            if start_time:
                params['start_time'] = f'gte.{start_time.isoformat()}'
            if end_time:
                params['start_time'] = f'lte.{end_time.isoformat()}'
            
            result = self._request('GET', 'schedules', params=params)
            return result if isinstance(result, list) else []
        except Exception as e:
            print(f"❌ Error getting schedules: {e}")
            return []
    
    def delete_user_schedules(self, user_id: str) -> bool:
        """Delete all schedules for a user"""
        try:
            params = {'user_id': f'eq.{user_id}'}
            self._request('DELETE', 'schedules', params=params)
            return True
        except Exception as e:
            print(f"❌ Error deleting schedules: {e}")
            return False
    
    def bulk_create_schedules(self, schedules: List[Dict]) -> bool:
        """Bulk create schedules"""
        try:
            self._request('POST', 'schedules', data=schedules)
            return True
        except Exception as e:
            print(f"❌ Error bulk creating schedules: {e}")
            return False
    
    # ============================================================
    # SESSION OPERATIONS
    # ============================================================
    
    def create_session(self, user_id: str, telegram_chat_id: int, session_token: str, expires_hours: int = 24) -> Optional[Dict]:
        """Create a new session"""
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        data = {
            'user_id': user_id,
            'telegram_chat_id': telegram_chat_id,
            'session_token': session_token,
            'expires_at': expires_at.isoformat(),
            'is_active': True
        }
        try:
            result = self._request('POST', 'sessions', data=data)
            return result[0] if isinstance(result, list) and result else result
        except Exception as e:
            print(f"❌ Error creating session: {e}")
            return None
    
    def get_active_session(self, telegram_chat_id: int) -> Optional[Dict]:
        """Get active session for a Telegram chat"""
        try:
            now = datetime.utcnow().isoformat()
            params = {
                'telegram_chat_id': f'eq.{telegram_chat_id}',
                'is_active': 'eq.true',
                'expires_at': f'gt.{now}',
                'limit': 1,
                'order': 'created_at.desc'
            }
            result = self._request('GET', 'sessions', params=params)
            return result[0] if result else None
        except Exception as e:
            print(f"❌ Error getting session: {e}")
            return None
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session"""
        try:
            data = {'is_active': False}
            params = {'session_id': f'eq.{session_id}'}
            self._request('PATCH', 'sessions', data=data, params=params)
            return True
        except Exception as e:
            print(f"❌ Error invalidating session: {e}")
            return False
    
    def invalidate_user_sessions(self, telegram_chat_id: int) -> bool:
        """Invalidate all sessions for a Telegram chat"""
        try:
            data = {'is_active': False}
            params = {'telegram_chat_id': f'eq.{telegram_chat_id}'}
            self._request('PATCH', 'sessions', data=data, params=params)
            return True
        except Exception as e:
            print(f"❌ Error invalidating sessions: {e}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """Cleanup expired sessions"""
        try:
            now = datetime.utcnow().isoformat()
            data = {'is_active': False}
            params = {'expires_at': f'lt.{now}', 'is_active': 'eq.true'}
            self._request('PATCH', 'sessions', data=data, params=params)
            return 0  # Can't get count from PATCH
        except Exception as e:
            print(f"❌ Error cleaning up sessions: {e}")
            return 0
    
    # ============================================================
    # ADMIN OPERATIONS
    # ============================================================
    
    def is_admin(self, telegram_chat_id: int) -> bool:
        """Check if a Telegram user is an admin"""
        try:
            params = {'telegram_chat_id': f'eq.{telegram_chat_id}', 'limit': 1}
            result = self._request('GET', 'admins', params=params)
            return bool(result)
        except Exception as e:
            print(f"❌ Error checking admin: {e}")
            return False
    
    def add_admin(self, telegram_chat_id: int, permissions: Optional[Dict] = None) -> bool:
        """Add a new admin"""
        if permissions is None:
            permissions = {
                'can_add_user': True,
                'can_delete_user': True,
                'can_import_schedule': True,
                'can_view_all_users': True
            }
        
        data = {
            'telegram_chat_id': telegram_chat_id,
            'permissions': permissions
        }
        try:
            self._request('POST', 'admins', data=data)
            return True
        except Exception as e:
            print(f"❌ Error adding admin: {e}")
            return False
    
    # ============================================================
    # REMINDER OPERATIONS
    # ============================================================
    
    def create_reminder(self, user_id: str, schedule_id: str, reminder_type: str, scheduled_time: datetime) -> Optional[Dict]:
        """Create a reminder"""
        data = {
            'user_id': user_id,
            'schedule_id': schedule_id,
            'reminder_type': reminder_type,
            'scheduled_time': scheduled_time.isoformat(),
            'status': 'pending'
        }
        try:
            result = self._request('POST', 'reminders', data=data)
            return result[0] if isinstance(result, list) and result else result
        except Exception as e:
            print(f"❌ Error creating reminder: {e}")
            return None
    
    def mark_reminder_sent(self, reminder_id: str) -> bool:
        """Mark reminder as sent"""
        try:
            data = {'status': 'sent', 'sent_at': datetime.utcnow().isoformat()}
            params = {'reminder_id': f'eq.{reminder_id}'}
            self._request('PATCH', 'reminders', data=data, params=params)
            return True
        except Exception as e:
            print(f"❌ Error marking reminder sent: {e}")
            return False

