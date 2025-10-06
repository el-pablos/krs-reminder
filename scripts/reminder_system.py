"""
KRS Reminder System - Multi-Jam Reminder untuk Kuliah
Integrasi Google Calendar & Telegram Bot dengan Notifikasi Premium
"""

import os
import datetime
import pytz
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
import time
import config

class KRSReminderBot:
    def __init__(self):
        self.tz = pytz.timezone(config.TIMEZONE)
        self.scheduler = BackgroundScheduler(timezone=config.TIMEZONE)
        self.sent_reminders = set()  # Track reminder yang sudah dikirim

    def authenticate_google_calendar(self):
        """Autentikasi ke Google Calendar menggunakan OAuth 2.0"""
        creds = None

        # Load token jika sudah ada
        if os.path.exists(config.TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(config.TOKEN_FILE, config.SCOPES)

        # Refresh atau buat token baru
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    config.CREDENTIALS_FILE, config.SCOPES)
                creds = flow.run_local_server(port=0)

            # Simpan token untuk session berikutnya
            with open(config.TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())

        return creds

    def get_todays_events(self, service):
        """Ambil semua event hari ini dari Google Calendar"""
        now = datetime.datetime.now(self.tz)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)

        try:
            events_result = service.events().list(
                calendarId='primary',
                timeMin=start_of_day.isoformat(),
                timeMax=end_of_day.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            print(f"✅ Berhasil mengambil {len(events)} event untuk hari ini")
            return events
        except Exception as e:
            print(f"❌ Error mengambil events: {e}")
            return []

    def format_reminder_message(self, event, hours_before=None):
        """Format pesan reminder dengan style premium dan detail"""

        # Parse waktu event
        start_time = event['start'].get('dateTime', event['start'].get('date'))
        if 'T' in start_time:
            start_dt = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            if start_dt.tzinfo is None:
                start_dt = self.tz.localize(start_dt)
            else:
                start_dt = start_dt.astimezone(self.tz)
        else:
            # All-day event
            start_dt = datetime.datetime.fromisoformat(start_time)
            start_dt = self.tz.localize(start_dt)

        # Informasi event
        summary = event.get('summary', 'Kuliah')
        location = event.get('location', 'Lokasi tidak disebutkan')
        description = event.get('description', '')

        # Header berdasarkan waktu reminder
        if hours_before is None:
            # Reminder tepat waktu
            header = "🔔 <b>KULIAH DIMULAI SEKARANG!</b> 🔔"
            urgency_emoji = "🚨"
        elif hours_before >= 5:
            header = f"📅 <b>REMINDER {hours_before} JAM SEBELUM KULIAH</b>"
            urgency_emoji = "📚"
        elif hours_before >= 3:
            header = f"⏰ <b>REMINDER {hours_before} JAM SEBELUM KULIAH</b>"
            urgency_emoji = "📖"
        elif hours_before >= 2:
            header = f"⚠️ <b>REMINDER {hours_before} JAM SEBELUM KULIAH</b>"
            urgency_emoji = "⏳"
        else:
            header = f"🚨 <b>URGENT! {hours_before} JAM LAGI!</b> 🚨"
            urgency_emoji = "🔥"

        # Format waktu
        time_str = start_dt.strftime('%H:%M')
        date_str = start_dt.strftime('%A, %d %B %Y')

        # Hitung countdown
        now = datetime.datetime.now(self.tz)
        time_diff = start_dt - now

        if time_diff.total_seconds() > 0:
            hours_left = int(time_diff.total_seconds() // 3600)
            minutes_left = int((time_diff.total_seconds() % 3600) // 60)
            countdown = f"{hours_left} jam {minutes_left} menit"
        else:
            countdown = "Sudah dimulai!"

        # Build message dengan formatting premium
        message = f"{header}\n"
        message += f"{'='*40}\n\n"
        message += f"{urgency_emoji} <b>MATA KULIAH</b>\n"
        message += f"📌 {summary}\n\n"
        message += f"🕐 <b>WAKTU</b>\n"
        message += f"⏰ {time_str} WIB\n"
        message += f"📆 {date_str}\n\n"
        message += f"⏳ <b>COUNTDOWN</b>\n"
        message += f"🔻 {countdown}\n\n"
        message += f"📍 <b>LOKASI</b>\n"
        message += f"🏫 {location}\n"

        if description:
            message += f"\n📝 <b>CATATAN</b>\n"
            message += f"{description[:200]}\n"  # Limit 200 karakter

        message += f"\n{'='*40}\n"

        # Call to action berdasarkan urgency
        if hours_before is None:
            message += "🎯 <b>SEGERA KE KELAS!</b>"
        elif hours_before <= 1:
            message += "🎯 <b>SEGERA PERSIAPKAN DIRI!</b>\n"
            message += "✅ Cek materi kuliah\n"
            message += "✅ Siapkan peralatan\n"
            message += "✅ Berangkat sekarang!"
        elif hours_before <= 2:
            message += "📚 <b>WAKTU PERSIAPAN:</b>\n"
            message += "✅ Review materi kuliah\n"
            message += "✅ Siapkan buku & laptop\n"
            message += "✅ Cek lokasi kelas"
        else:
            message += "💡 <b>TIPS:</b>\n"
            message += "✅ Sempat belajar materi\n"
            message += "✅ Sempat makan\n"
            message += "✅ Sempat istirahat"

        return message

    def send_telegram_message(self, message):
        """Kirim pesan ke Telegram dengan HTML formatting"""
        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': config.CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'  # Enable HTML formatting
        }

        try:
            response = requests.post(url, data=payload)
            if response.status_code == 200:
                print(f"✅ Pesan terkirim ke Telegram")
                return True
            else:
                print(f"❌ Gagal kirim pesan: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error kirim pesan: {e}")
            return False

    def schedule_reminders(self, events):
        """Jadwalkan reminder untuk semua event"""
        now = datetime.datetime.now(self.tz)
        scheduled_count = 0

        for event in events:
            # Parse start time
            start_time = event['start'].get('dateTime', None)
            if not start_time:
                continue  # Skip all-day events

            start_dt = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            if start_dt.tzinfo is None:
                start_dt = self.tz.localize(start_dt)
            else:
                start_dt = start_dt.astimezone(self.tz)

            event_id = event.get('id', '')
            event_summary = event.get('summary', 'Kuliah')

            # Schedule reminder untuk setiap interval
            for hours in config.REMINDER_HOURS:
                reminder_time = start_dt - datetime.timedelta(hours=hours)

                # Cek apakah reminder sudah lewat atau sudah dijadwalkan
                reminder_key = f"{event_id}_{hours}h"

                if reminder_time > now and reminder_key not in self.sent_reminders:
                    try:
                        self.scheduler.add_job(
                            func=self.send_reminder,
                            trigger=DateTrigger(run_date=reminder_time),
                            args=[event, hours],
                            id=reminder_key,
                            replace_existing=True
                        )
                        scheduled_count += 1
                        print(f"📅 Terjadwal: {event_summary} - {hours} jam sebelum ({reminder_time.strftime('%H:%M')})")
                    except Exception as e:
                        print(f"⚠️ Error scheduling {reminder_key}: {e}")

            # Schedule reminder tepat waktu jika diaktifkan
            if config.INCLUDE_EXACT_TIME_REMINDER:
                reminder_key = f"{event_id}_exact"

                if start_dt > now and reminder_key not in self.sent_reminders:
                    try:
                        self.scheduler.add_job(
                            func=self.send_reminder,
                            trigger=DateTrigger(run_date=start_dt),
                            args=[event, None],
                            id=reminder_key,
                            replace_existing=True
                        )
                        scheduled_count += 1
                        print(f"🔔 Terjadwal: {event_summary} - Tepat waktu ({start_dt.strftime('%H:%M')})")
                    except Exception as e:
                        print(f"⚠️ Error scheduling {reminder_key}: {e}")

        print(f"\n✅ Total {scheduled_count} reminder terjadwal")

    def send_reminder(self, event, hours_before):
        """Kirim reminder dan mark sebagai terkirim"""
        message = self.format_reminder_message(event, hours_before)

        if self.send_telegram_message(message):
            # Mark sebagai terkirim
            event_id = event.get('id', '')
            reminder_key = f"{event_id}_{hours_before}h" if hours_before else f"{event_id}_exact"
            self.sent_reminders.add(reminder_key)

    def check_and_schedule_events(self):
        """Cek event baru dan jadwalkan reminder"""
        print(f"\n🔄 Checking events... ({datetime.datetime.now(self.tz).strftime('%Y-%m-%d %H:%M:%S')})")

        try:
            creds = self.authenticate_google_calendar()
            service = build('calendar', 'v3', credentials=creds)
            events = self.get_todays_events(service)

            if events:
                self.schedule_reminders(events)
            else:
                print("📭 Tidak ada event hari ini")
        except Exception as e:
            print(f"❌ Error: {e}")

    def start(self):
        """Mulai reminder system"""
        print("="*50)
        print("🚀 KRS REMINDER SYSTEM - STARTED")
        print("="*50)
        print(f"📱 Telegram Bot Token: {config.TELEGRAM_BOT_TOKEN[:20]}...")
        print(f"👤 Target Chat ID: {config.CHAT_ID}")
        print(f"🌍 Timezone: {config.TIMEZONE}")
        print(f"⏰ Reminder Intervals: {config.REMINDER_HOURS} jam sebelum")
        print(f"🔔 Exact Time Reminder: {'Aktif' if config.INCLUDE_EXACT_TIME_REMINDER else 'Nonaktif'}")
        print(f"🔄 Check Interval: Setiap {config.CHECK_INTERVAL_MINUTES} menit")
        print("="*50)

        # Send startup notification
        startup_msg = "🚀 <b>KRS REMINDER BOT ONLINE!</b>\n\n"
        startup_msg += "✅ Bot berhasil dijalankan\n"
        startup_msg += f"⏰ Auto-check setiap {config.CHECK_INTERVAL_MINUTES} menit\n"
        startup_msg += f"📅 Monitoring jadwal kuliah hari ini\n\n"
        startup_msg += "Bot siap mengirim reminder! 📚"

        self.send_telegram_message(startup_msg)

        # Initial check
        self.check_and_schedule_events()

        # Schedule periodic check setiap X menit
        self.scheduler.add_job(
            func=self.check_and_schedule_events,
            trigger='interval',
            minutes=config.CHECK_INTERVAL_MINUTES,
            id='periodic_check',
            replace_existing=True
        )

        # Start scheduler
        self.scheduler.start()

        print("\n✅ Scheduler started! Press Ctrl+C to stop.\n")

        # Keep running
        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            print("\n⏹️  Stopping scheduler...")
            self.scheduler.shutdown()

            # Send shutdown notification
            shutdown_msg = "⏹️ <b>KRS REMINDER BOT STOPPED</b>\n\n"
            shutdown_msg += "Bot telah dimatikan. Reminder tidak akan aktif."
            self.send_telegram_message(shutdown_msg)

            print("👋 Bot stopped. Goodbye!")

if __name__ == "__main__":
    bot = KRSReminderBot()
    bot.start()
