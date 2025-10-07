"""
Command handlers for multi-user KRS Reminder Bot
"""
import datetime
from typing import Dict, Optional


class CommandHandler:
    """Handle user and admin commands"""

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.auth = bot.auth
        self.admin = bot.admin

    # ============================================================
    # HELPER METHODS
    # ============================================================

    def _get_onboarding_message(self) -> str:
        """
        Get onboarding message for unauthenticated users

        Returns:
            Formatted onboarding message
        """
        return (
            "❌ <b>Anda belum terdaftar di sistem.</b>\n\n"
            "📋 <b>Untuk menggunakan bot ini:</b>\n\n"
            "1️⃣ Kirim jadwal kuliah Anda ke admin: @el_pablos\n"
            "2️⃣ Admin akan menambahkan Anda ke database\n"
            "3️⃣ Anda akan menerima <b>secret key</b> untuk login\n"
            "4️⃣ Login dengan command:\n"
            "     <code>/login &lt;secret_key&gt;</code>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📧 <b>Hubungi admin untuk registrasi:</b> @el_pablos\n\n"
            "ℹ️ Bot ini menggunakan sistem multi-user dengan autentikasi "
            "untuk menjaga privasi jadwal setiap user."
        )

    # ============================================================
    # USER COMMANDS
    # ============================================================

    def handle_start(self, chat_id: int) -> str:
        """Handle /start command - Check authentication status"""
        if not self.bot.multi_user_enabled:
            # Single-user mode: show regular welcome
            return None  # Let bot.py handle single-user welcome

        # Check if user is logged in
        is_logged_in, user, error_msg = self.auth.require_login(chat_id)

        if is_logged_in:
            # User is logged in: show welcome with available commands
            return (
                f"👋 <b>Selamat Datang, {user['username']}!</b>\n\n"
                "🎓 <b>KRS Reminder Bot V3</b>\n"
                "Asisten pintar untuk jadwal kuliahmu\n\n"
                "━━━━━━━━━━━━━━━━━━━\n\n"
                "<b>✨ Fitur Utama</b>\n"
                "  🔔 Reminder otomatis (5j, 3j, 2j, 1j sebelum)\n"
                "  📅 Jadwal kuliah personal\n"
                "  ⏰ Notifikasi tepat waktu\n"
                "  📊 Monitoring real-time\n\n"
                "━━━━━━━━━━━━━━━━━━━\n\n"
                "<b>📋 Perintah yang Tersedia:</b>\n"
                "  /jadwal - Lihat jadwal kuliah\n"
                "  /stats - Lihat statistik bot\n"
                "  /logout - Keluar dari akun\n\n"
                "💡 <b>Gunakan menu di bawah untuk navigasi cepat</b>"
            )
        else:
            # User NOT logged in: show login instructions
            return (
                "👋 <b>Selamat datang di KRS Reminder Bot V3!</b>\n\n"
                "🔒 <b>Anda belum login.</b> Untuk menggunakan bot ini:\n\n"
                "1️⃣ Hubungi admin untuk membuat akun\n"
                "2️⃣ Admin akan memberikan <b>secret key</b> kepada Anda\n"
                "3️⃣ Login dengan command:\n"
                "     <code>/login &lt;secret_key&gt;</code>\n"
                "4️⃣ Setelah login, Anda bisa melihat jadwal Anda\n\n"
                "━━━━━━━━━━━━━━━━━━━\n\n"
                "📧 <b>Kontak Admin:</b> @el_pablos\n\n"
                "ℹ️ Bot ini menggunakan sistem multi-user dengan autentikasi "
                "untuk menjaga privasi jadwal setiap user."
            )

    def handle_login(self, chat_id: int, args: list) -> str:
        """Handle /login <secret_key>"""
        if not self.bot.multi_user_enabled:
            return "❌ Multi-user support tidak aktif"
        
        if len(args) < 2:
            return (
                "❌ <b>Format salah!</b>\n\n"
                "Gunakan: <code>/login &lt;secret_key&gt;</code>\n\n"
                "Contoh: <code>/login rahasia123</code>"
            )
        
        secret_key = args[1].strip()

        # Check if already logged in
        existing_session = self.auth.validate_session(chat_id)
        if existing_session:
            user = self.db.get_user_by_id(existing_session['user_id'])
            return f"⚠️  Anda sudah login sebagai <b>{user['username']}</b>"

        # Try to login - search for user by secret_key hash
        users = self.db.list_all_users()

        matched_user = None
        for user in users:
            # Verify secret key (correct argument order: plain_text, hash)
            if self.auth.verify_secret_key(secret_key, user['secret_key_hash']):
                matched_user = user
                break

        if not matched_user:
            return (
                "❌ <b>Secret key tidak valid</b>\n\n"
                "Pastikan Anda memasukkan secret key yang benar.\n"
                "Hubungi admin jika Anda lupa secret key Anda."
            )

        # Create session
        result = self.auth.login(matched_user['username'], secret_key, chat_id)
        if result['success']:
            return (
                f"✅ <b>Login Berhasil!</b>\n\n"
                f"👤 Username: <b>{result['username']}</b>\n"
                f"🔑 Session aktif selama 24 jam\n\n"
                f"Gunakan /jadwal untuk melihat jadwal Anda"
            )
        else:
            return result['message']
    
    def handle_logout(self, chat_id: int) -> str:
        """Handle /logout"""
        if not self.bot.multi_user_enabled:
            return "❌ Multi-user support tidak aktif"

        # Check if logged in first
        is_logged_in, user, error_msg = self.auth.require_login(chat_id)
        if not is_logged_in:
            return "❌ Anda belum login"

        result = self.auth.logout(chat_id)
        if result['success']:
            return "✅ <b>Logout Berhasil!</b>\n\nGunakan /login untuk login kembali"
        else:
            return result['message']
    
    def handle_jadwal_multiuser(self, chat_id: int) -> tuple[bool, str, list]:
        """
        Handle /jadwal for multi-user
        Returns: (success, message, events)
        """
        if not self.bot.multi_user_enabled:
            return (False, "Multi-user disabled", [])

        # Check if logged in
        is_logged_in, user, error_msg = self.auth.require_login(chat_id)
        if not is_logged_in:
            # Send improved onboarding message
            onboarding_msg = self._get_onboarding_message()

            # Notify admin about unauthorized access
            self.bot._notify_admin_unauthorized_access(chat_id, "Command: /jadwal")

            return (False, onboarding_msg, [])
        
        # Get schedules from database
        now = datetime.datetime.now(self.bot.tz)
        end_time = now + datetime.timedelta(days=7)
        
        schedules = self.db.get_user_schedules(
            user_id=user['user_id'],
            start_time=now,
            end_time=end_time
        )
        
        if not schedules:
            msg = (
                "📭 <b>Tidak ada jadwal</b>\n\n"
                "Belum ada jadwal untuk 7 hari ke depan.\n"
                "Hubungi admin untuk import jadwal."
            )
            return (False, msg, [])
        
        # Convert schedules to event format for compatibility
        events = self._schedules_to_events(schedules)
        return (True, "", events)
    
    def _schedules_to_events(self, schedules: list) -> list:
        """Convert database schedules to Google Calendar event format"""
        events = []
        for schedule in schedules:
            event = {
                'id': schedule.get('google_event_id', schedule['schedule_id']),
                'summary': f"📚 {schedule['course_name']}",
                'start': {'dateTime': schedule['start_time']},
                'end': {'dateTime': schedule['end_time']},
                'location': schedule.get('location', ''),
                'description': self._build_description(schedule)
            }
            events.append(event)
        return events
    
    def _build_description(self, schedule: Dict) -> str:
        """Build event description from schedule"""
        parts = [
            f"📚 Mata Kuliah: {schedule['course_name']}",
        ]
        if schedule.get('facilitator'):
            parts.append(f"👨‍🏫 Dosen: {schedule['facilitator']}")
        if schedule.get('course_code'):
            parts.append(f"🔢 Kode: {schedule['course_code']}")
        if schedule.get('location'):
            parts.append(f"📍 Lokasi: {schedule['location']}")
        if schedule.get('class_type'):
            parts.append(f"📖 Tipe: {schedule['class_type']}")
        
        return '\n'.join(parts)
    
    # ============================================================
    # ADMIN COMMANDS
    # ============================================================
    
    def handle_admin_add_user(self, chat_id: int, args: list) -> str:
        """Handle /admin_add_user <username> [secret_key]"""
        if not self.bot.multi_user_enabled:
            return "❌ Multi-user support tidak aktif"
        
        # Check admin
        is_admin, error_msg = self.admin.require_admin(chat_id)
        if not is_admin:
            return error_msg
        
        if len(args) < 2:
            return (
                "❌ <b>Format salah!</b>\n\n"
                "Gunakan: <code>/admin_add_user &lt;username&gt; [secret_key]</code>\n\n"
                "Contoh: <code>/admin_add_user tama</code>\n"
                "Atau: <code>/admin_add_user tama rahasia123</code>"
            )
        
        username = args[1]
        secret_key = args[2] if len(args) > 2 else None
        
        result = self.admin.add_user(username, secret_key)
        
        if result['success']:
            return (
                f"✅ <b>User Berhasil Dibuat!</b>\n\n"
                f"👤 Username: <code>{result['username']}</code>\n"
                f"🔑 Secret Key: <code>{result['secret_key']}</code>\n"
                f"🆔 User ID: <code>{result['user_id']}</code>\n\n"
                f"⚠️  <b>PENTING:</b> Simpan secret key ini!\n"
                f"Berikan ke user untuk login."
            )
        else:
            return result['message']
    
    def handle_admin_list_users(self, chat_id: int) -> str:
        """Handle /admin_list_users"""
        if not self.bot.multi_user_enabled:
            return "❌ Multi-user support tidak aktif"
        
        is_admin, error_msg = self.admin.require_admin(chat_id)
        if not is_admin:
            return error_msg
        
        result = self.admin.list_users()
        
        if result['count'] == 0:
            return "📭 Belum ada user terdaftar"
        
        lines = [
            f"👥 <b>Daftar User ({result['count']})</b>\n",
            "━━━━━━━━━━━━━━━━━━━\n"
        ]
        
        for i, user in enumerate(result['users'], 1):
            has_calendar = "✅" if user.get('google_calendar_token_encrypted') else "❌"
            lines.append(
                f"{i}. <b>{user['username']}</b>\n"
                f"   🆔 <code>{user['user_id']}</code>\n"
                f"   📅 Calendar: {has_calendar}\n"
            )
        
        return ''.join(lines)
    
    def handle_admin_import_schedule(self, chat_id: int, args: list) -> str:
        """Handle /admin_import_schedule <user_id>"""
        if not self.bot.multi_user_enabled:
            return "❌ Multi-user support tidak aktif"
        
        is_admin, error_msg = self.admin.require_admin(chat_id)
        if not is_admin:
            return error_msg
        
        if len(args) < 2:
            return (
                "❌ <b>Format salah!</b>\n\n"
                "Gunakan: <code>/admin_import_schedule &lt;user_id&gt;</code>\n\n"
                "Gunakan /admin_list_users untuk melihat user_id"
            )
        
        user_id = args[1]
        
        # Import schedule
        result = self.admin.import_schedule(user_id, days_ahead=30)
        
        if result['success']:
            count = result.get('count', 0)
            return (
                f"✅ <b>Import Berhasil!</b>\n\n"
                f"📅 Total jadwal: <b>{count}</b>\n"
                f"📆 Range: 30 hari ke depan\n\n"
                f"{result['message']}"
            )
        else:
            return result['message']
    
    def handle_admin_delete_user(self, chat_id: int, args: list) -> str:
        """Handle /admin_delete_user <user_id>"""
        if not self.bot.multi_user_enabled:
            return "❌ Multi-user support tidak aktif"
        
        is_admin, error_msg = self.admin.require_admin(chat_id)
        if not is_admin:
            return error_msg
        
        if len(args) < 2:
            return (
                "❌ <b>Format salah!</b>\n\n"
                "Gunakan: <code>/admin_delete_user &lt;user_id&gt;</code>\n\n"
                "Gunakan /admin_list_users untuk melihat user_id"
            )
        
        user_id = args[1]
        result = self.admin.delete_user(user_id)
        
        if result['success']:
            return f"✅ {result['message']}"
        else:
            return result['message']

