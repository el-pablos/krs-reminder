"""
Authentication module for KRS Reminder Bot
Handles user authentication, session management, and encryption
"""
import bcrypt
import secrets
from typing import Optional, Dict
from cryptography.fernet import Fernet
from datetime import datetime
import base64
import hashlib


class AuthManager:
    """Manages authentication and encryption for KRS Reminder Bot"""
    
    def __init__(self, db_client, encryption_key: Optional[str] = None):
        """
        Initialize AuthManager
        
        Args:
            db_client: SupabaseClient instance
            encryption_key: Base64-encoded encryption key (generated if not provided)
        """
        self.db = db_client
        
        # Initialize encryption
        if encryption_key:
            self.encryption_key = encryption_key.encode()
        else:
            # Generate a new key (should be stored securely in production)
            self.encryption_key = Fernet.generate_key()
        
        self.cipher = Fernet(self.encryption_key)
    
    # ============================================================
    # PASSWORD HASHING
    # ============================================================
    
    @staticmethod
    def hash_secret_key(secret_key: str) -> str:
        """
        Hash a secret key using bcrypt
        
        Args:
            secret_key: Plain text secret key
            
        Returns:
            Bcrypt hash string
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(secret_key.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_secret_key(secret_key: str, hashed: str) -> bool:
        """
        Verify a secret key against its hash
        
        Args:
            secret_key: Plain text secret key
            hashed: Bcrypt hash to verify against
            
        Returns:
            True if secret key matches hash
        """
        try:
            return bcrypt.checkpw(secret_key.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            print(f"❌ Error verifying secret key: {e}")
            return False
    
    # ============================================================
    # TOKEN ENCRYPTION
    # ============================================================
    
    def encrypt_calendar_token(self, token: str) -> str:
        """
        Encrypt Google Calendar token
        
        Args:
            token: Plain text token (JSON string)
            
        Returns:
            Base64-encoded encrypted token
        """
        try:
            encrypted = self.cipher.encrypt(token.encode('utf-8'))
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            print(f"❌ Error encrypting token: {e}")
            raise
    
    def decrypt_calendar_token(self, encrypted_token: str) -> str:
        """
        Decrypt Google Calendar token
        
        Args:
            encrypted_token: Base64-encoded encrypted token
            
        Returns:
            Plain text token (JSON string)
        """
        try:
            encrypted_bytes = base64.b64decode(encrypted_token.encode('utf-8'))
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except Exception as e:
            print(f"❌ Error decrypting token: {e}")
            raise
    
    # ============================================================
    # SESSION MANAGEMENT
    # ============================================================
    
    @staticmethod
    def generate_session_token() -> str:
        """
        Generate a secure random session token
        
        Returns:
            Hex-encoded random token (64 characters)
        """
        return secrets.token_hex(32)
    
    def login(self, username: str, secret_key: str, telegram_chat_id: int) -> Dict:
        """
        Authenticate user and create session
        
        Args:
            username: Username
            secret_key: Plain text secret key
            telegram_chat_id: Telegram chat ID
            
        Returns:
            Dict with 'success', 'message', 'user_id', 'session_token'
        """
        # Get user from database
        user = self.db.get_user_by_username(username)
        
        if not user:
            return {
                'success': False,
                'message': '❌ Username tidak ditemukan'
            }
        
        # Verify secret key
        if not self.verify_secret_key(secret_key, user['secret_key_hash']):
            return {
                'success': False,
                'message': '❌ Secret key salah'
            }
        
        # Invalidate old sessions
        self.db.invalidate_user_sessions(telegram_chat_id)
        
        # Create new session
        session_token = self.generate_session_token()
        session = self.db.create_session(
            user_id=user['user_id'],
            telegram_chat_id=telegram_chat_id,
            session_token=session_token,
            expires_hours=24
        )
        
        if not session:
            return {
                'success': False,
                'message': '❌ Gagal membuat session'
            }
        
        return {
            'success': True,
            'message': f'✅ Login berhasil! Selamat datang, {username}',
            'user_id': user['user_id'],
            'username': username,
            'session_token': session_token
        }
    
    def logout(self, telegram_chat_id: int) -> Dict:
        """
        Logout user and invalidate session
        
        Args:
            telegram_chat_id: Telegram chat ID
            
        Returns:
            Dict with 'success' and 'message'
        """
        success = self.db.invalidate_user_sessions(telegram_chat_id)
        
        if success:
            return {
                'success': True,
                'message': '✅ Logout berhasil'
            }
        else:
            return {
                'success': False,
                'message': '❌ Gagal logout'
            }
    
    def validate_session(self, telegram_chat_id: int) -> Optional[Dict]:
        """
        Validate active session for a Telegram chat
        
        Args:
            telegram_chat_id: Telegram chat ID
            
        Returns:
            Session dict if valid, None otherwise
        """
        session = self.db.get_active_session(telegram_chat_id)
        
        if not session:
            return None
        
        # Check if session is expired
        expires_at = datetime.fromisoformat(session['expires_at'].replace('Z', '+00:00'))
        if datetime.utcnow() > expires_at.replace(tzinfo=None):
            # Session expired, invalidate it
            self.db.invalidate_session(session['session_id'])
            return None
        
        return session
    
    def get_user_from_session(self, telegram_chat_id: int) -> Optional[Dict]:
        """
        Get user info from active session
        
        Args:
            telegram_chat_id: Telegram chat ID
            
        Returns:
            User dict if session valid, None otherwise
        """
        session = self.validate_session(telegram_chat_id)
        
        if not session:
            return None
        
        user = self.db.get_user_by_id(session['user_id'])
        return user
    
    def require_login(self, telegram_chat_id: int) -> tuple[bool, Optional[Dict], str]:
        """
        Check if user is logged in
        
        Args:
            telegram_chat_id: Telegram chat ID
            
        Returns:
            Tuple of (is_logged_in, user_dict, error_message)
        """
        user = self.get_user_from_session(telegram_chat_id)
        
        if user:
            return (True, user, '')
        else:
            return (False, None, '❌ Anda belum login. Gunakan /login <secret_key>')
    
    # ============================================================
    # UTILITY FUNCTIONS
    # ============================================================
    
    @staticmethod
    def generate_secret_key(length: int = 16) -> str:
        """
        Generate a random secret key for new users
        
        Args:
            length: Length of secret key
            
        Returns:
            Random alphanumeric string
        """
        return secrets.token_urlsafe(length)
    
    def get_encryption_key_base64(self) -> str:
        """
        Get the encryption key as base64 string (for storage)
        
        Returns:
            Base64-encoded encryption key
        """
        return base64.b64encode(self.encryption_key).decode('utf-8')

