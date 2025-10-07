"""Core bot runtime for the KRS Reminder system - Multi-User Support."""

import datetime
import html
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psutil
import pytz
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from . import config
from .database import SupabaseClient
from .auth import AuthManager
from .admin import AdminManager
from .commands import CommandHandler

class KRSReminderBotV2:
    def __init__(self):
        self.tz = pytz.timezone(config.TIMEZONE)
        self.scheduler = BackgroundScheduler(
            timezone=config.TIMEZONE,
            job_defaults={"max_instances": 1, "coalesce": True}
        )
        self.sent_reminders = set()
        self.start_time = datetime.datetime.now(self.tz)
        self.total_reminders_sent = 0
        self.total_events_checked = 0
        self.last_update_id = 0
        self.http_session = requests.Session()
        self.calendar_service = None
        self.calendar_service_expiry: Optional[datetime.datetime] = None

        # Multi-user support
        try:
            self.db = SupabaseClient()
            self.auth = AuthManager(self.db)
            self.admin = AdminManager(self.db, self.auth, self._get_calendar_service)
            self.cmd_handler = CommandHandler(self)
            self.multi_user_enabled = True
            print("✅ Multi-user support enabled")
        except Exception as e:
            print(f"⚠️  Multi-user support disabled: {e}")
            self.db = None
            self.auth = None
            self.admin = None
            self.cmd_handler = None
            self.multi_user_enabled = False

    def authenticate_google_calendar(self):
        """Autentikasi ke Google Calendar dengan auto-recovery"""
        creds = None

        token_path: Path = config.TOKEN_FILE

        if token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(token_path), config.SCOPES)
            except Exception as e:
                print(f"⚠️  Error loading token: {e}")
                print("🔄 Removing invalid token file...")
                token_path.unlink(missing_ok=True)
                creds = None

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    print("🔄 Refreshing expired token...")
                    creds.refresh(Request())
                    print("✅ Token refreshed successfully")
                except Exception as e:
                    print(f"❌ Failed to refresh token: {e}")
                    print("❌ Please run: python3 scripts/auth/auth_final.py")
                    raise Exception("Token refresh failed. Run scripts/auth/auth_final.py to generate new token.")
            else:
                print("❌ No valid token found!")
                print("❌ Please run: python3 scripts/auth/auth_final.py")
                raise Exception("No token found. Run scripts/auth/auth_final.py to generate token.")

            with token_path.open('w', encoding='utf-8') as token:
                token.write(creds.to_json())

        return creds

    def _get_calendar_service(self, force_refresh: bool = False):
        """Reuse Google Calendar service object for faster access."""

        now_utc = datetime.datetime.now(datetime.timezone.utc)
        if force_refresh or not self.calendar_service or not self.calendar_service_expiry or now_utc >= self.calendar_service_expiry:
            creds = self.authenticate_google_calendar()
            self.calendar_service = build('calendar', 'v3', credentials=creds, cache_discovery=False)
            self.calendar_service_expiry = now_utc + datetime.timedelta(seconds=config.CALENDAR_SERVICE_TTL_SECONDS)

        return self.calendar_service

    def get_todays_events(self, service):
        """Ambil semua event hari ini dan besok (untuk reminder yang cross-day)"""
        now = datetime.datetime.now(self.tz)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Ambil sampai besok untuk cover reminder 5h yang cross-day
        # Contoh: Kuliah Jumat 08:00, reminder 5h = Kamis 03:00
        end_time = now + datetime.timedelta(hours=36)  # +36 jam dari sekarang

        try:
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now.isoformat(),  # Dari sekarang
                timeMax=end_time.isoformat(),  # Sampai 36 jam ke depan
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            self.total_events_checked += len(events)

            # Separate today and tomorrow events for logging
            today_events = []
            tomorrow_events = []
            end_of_today = now.replace(hour=23, minute=59, second=59, microsecond=0)

            for event in events:
                start_time = event['start'].get('dateTime', None)
                if start_time:
                    start_dt = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    if start_dt.tzinfo is None:
                        start_dt = self.tz.localize(start_dt)
                    else:
                        start_dt = start_dt.astimezone(self.tz)

                    if start_dt <= end_of_today:
                        today_events.append(event)
                    else:
                        tomorrow_events.append(event)

            print(f"✅ Found {len(today_events)} events today, {len(tomorrow_events)} events tomorrow")
            print(f"   Total to process: {len(events)} events")
            return events
        except Exception as e:
            print(f"❌ Error getting events: {e}")
            return []

    def get_weekly_events(self, service):
        """Ambil event untuk 7 hari ke depan"""
        now = datetime.datetime.now(self.tz)
        range_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        range_end = range_start + datetime.timedelta(days=7)

        try:
            events_result = service.events().list(
                calendarId='primary',
                timeMin=range_start.isoformat(),
                timeMax=range_end.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            return events, range_start, range_end
        except Exception as e:
            print(f"❌ Error getting weekly events: {e}")
            return [], range_start, range_end

    def _escape_html(self, value):
        if not value:
            return ''
        return html.escape(value, quote=False)

    def _format_date_id(self, dt):
        day_names = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
        month_names = [
            'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
            'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
        ]
        return f"{day_names[dt.weekday()]}, {dt.day:02d} {month_names[dt.month - 1]} {dt.year}"

    def _format_time_id(self, dt):
        return dt.strftime('%H:%M')

    def _format_short_date(self, dt):
        month_short = [
            'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun',
            'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'
        ]
        day_short = ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min']
        return f"{day_short[dt.weekday()]} {dt.day:02d} {month_short[dt.month - 1]}"

    def _extract_facilitator(self, description: str) -> Optional[str]:
        if not description:
            return None

        patterns = [
            r'dosen\s*[:\-]\s*(.+)',
            r'pengajar\s*[:\-]\s*(.+)',
            r'instructor\s*[:\-]\s*(.+)',
            r'speaker\s*[:\-]\s*(.+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, description, flags=re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_description_highlights(self, description: str, limit: int = 2) -> List[str]:
        if not description:
            return []

        raw_lines = [line.strip() for line in description.split('\n') if line.strip()]
        highlights: List[str] = []

        for line in raw_lines:
            clean_line = re.sub(r'^[•\-\d\)\.\s]+', '', line)
            if not clean_line:
                continue
            lower = clean_line.lower()
            if lower.startswith(('dosen', 'pengajar', 'instructor', 'speaker')):
                continue
            highlights.append(clean_line)
            if len(highlights) >= limit:
                break

        return highlights

    def _infer_class_profile(self, summary: str, location: str, description: str) -> Dict[str, str]:
        base_text = ' '.join(filter(None, [summary, location, description])).lower()

        if any(keyword in base_text for keyword in ['praktikum', 'laboratorium', 'lab ', 'lab.']):
            category_icon = '🔬'
            category_label = 'Praktikum'
        elif any(keyword in base_text for keyword in ['seminar', 'kuliah tamu', 'guest lecture']):
            category_icon = '🎤'
            category_label = 'Seminar'
        elif any(keyword in base_text for keyword in ['workshop', 'project', 'studio']):
            category_icon = '🛠️'
            category_label = 'Workshop / Studio'
        elif any(keyword in base_text for keyword in ['ujian', 'evaluasi', 'quiz']):
            category_icon = '📝'
            category_label = 'Evaluasi / Ujian'
        else:
            category_icon = '🏛️'
            category_label = 'Kuliah Teori'

        if any(keyword in base_text for keyword in ['zoom', 'teams', 'online', 'daring', 'virtual']):
            delivery_icon = '🌐'
            delivery_label = 'Sesi Daring'
        else:
            delivery_icon = '🏫'
            delivery_label = 'Sesi Tatap Muka'

        return {
            'category_icon': category_icon,
            'category_label': category_label,
            'delivery_icon': delivery_icon,
            'delivery_label': delivery_label
        }

    def _get_reminder_theme(self, hours_before: Optional[int]) -> Dict[str, object]:
        if hours_before is None:
            return {
                'headline': '🔔 <b>KULIAH DIMULAI SEKARANG</b>',
                'tagline': 'Sesi telah dibuka — fokus penuh di kelas dan catat poin penting.',
                'checklist_title': 'Fokus Di Kelas',
                'checklist': [
                    'Lakukan absensi di awal sesi',
                    'Aktif dalam diskusi dan tanya jawab',
                    'Catat insight utama langsung di laptop/notes'
                ],
                'cta': '🎯 Tetap engaged dan follow up setelah kelas'
            }
        if hours_before >= 5:
            return {
                'headline': '🟢 <b>PREP MODE • 5 JAM LAGI</b>',
                'tagline': 'Waktu longgar — persiapkan materi dan kebutuhan logistik dari sekarang.',
                'checklist_title': 'Modal Awal',
                'checklist': [
                    'Review silabus & catatan pekan lalu',
                    'Pastikan transport & outfit sudah siap',
                    'Sync jadwal dengan teman satu kelas'
                ],
                'cta': '💡 Semakin siap sekarang, semakin tenang nanti'
            }
        if hours_before >= 3:
            return {
                'headline': '🟡 <b>FOCUS MODE • 3 JAM LAGI</b>',
                'tagline': 'Masuk fase belajar inti — review materi dan susun pertanyaan.',
                'checklist_title': 'Perdalam Materi',
                'checklist': [
                    'Highlight konsep penting & rumus kunci',
                    'Rangkum pertanyaan untuk dosen',
                    'Update progress kelompok bila ada proyek'
                ],
                'cta': '📝 Mantapkan pemahaman sebelum sesi dimulai'
            }
        if hours_before >= 2:
            return {
                'headline': '🟠 <b>SET MODE • 2 JAM LAGI</b>',
                'tagline': 'Final gear check — siap-siapkan perangkat dan file pendukung.',
                'checklist_title': 'Persiapan Teknis',
                'checklist': [
                    'Charge laptop & perangkat pendukung',
                    'Unduh materi/slide terbaru dari LMS',
                    'Konfirmasi lokasi kelas & akses gedung'
                ],
                'cta': '📦 Lengkapi perlengkapan sebelum berangkat'
            }
        return {
            'headline': '🔴 <b>RUSH MODE • 1 JAM LAGI</b>',
            'tagline': 'Hitung mundur final — waktunya berangkat dan hindari keterlambatan.',
            'checklist_title': 'Prioritas Sekarang',
            'checklist': [
                'Berangkat menuju kampus/ruang kelas',
                'Pastikan baterai perangkat aman',
                'Info kelompok jika ada perubahan'
            ],
            'cta': '🚀 Bergerak sekarang untuk tiba tepat waktu'
        }

    def _build_quick_command_footer(self):
        return '🔁 /start • /jadwal • /stats'

    def _get_week_number(self, date_obj: datetime.datetime) -> int:
        """
        Get week number relative to semester start date.
        Semester starts: September 29, 2025 (Week 1 = VA)
        """
        # Semester start date: September 29, 2025
        semester_start = datetime.datetime(2025, 9, 29, 0, 0, 0, tzinfo=self.tz)

        # Calculate days since semester start
        days_diff = (date_obj.date() - semester_start.date()).days

        # Calculate week number (1-based)
        # Week 1 = Sept 29 - Oct 5
        # Week 2 = Oct 6 - Oct 12
        # etc.
        week_num = (days_diff // 7) + 1

        return max(1, week_num)  # Ensure at least week 1

    def _is_va_week(self, date_obj: datetime.datetime) -> bool:
        """
        Determine if the given date is in a VA (Virtual Attendance) week.
        VA = Odd weeks (1, 3, 5, 7, 9, 11, 13, 15) = Online classes
        VB = Even weeks (2, 4, 6, 8, 10, 12, 14, 16) = Onsite classes

        Week 1 (starting Sept 29, 2025) = VA = Online
        """
        week_num = self._get_week_number(date_obj)
        return week_num % 2 == 1  # Odd week = VA

    def _get_week_start_end(self, date_obj: datetime.datetime) -> tuple:
        """Get the start and end dates for the week containing date_obj"""
        week_num = self._get_week_number(date_obj)
        semester_start = datetime.datetime(2025, 9, 29, 0, 0, 0, tzinfo=self.tz)

        # Calculate week start (Monday)
        week_start = semester_start + datetime.timedelta(days=(week_num - 1) * 7)
        week_end = week_start + datetime.timedelta(days=6)

        return (week_start, week_end)

    def _get_va_vb_status(self, date_obj: datetime.datetime) -> dict:
        """
        Get VA/VB status for a given date.
        Returns dict with: is_va, week_type, week_num, icon, label, description, detailed_info
        """
        is_va = self._is_va_week(date_obj)
        week_num = self._get_week_number(date_obj)
        week_start, week_end = self._get_week_start_end(date_obj)

        # Format date range
        date_range = f"{week_start.strftime('%d %b')} - {week_end.strftime('%d %b %Y')}"

        if is_va:
            return {
                'is_va': True,
                'week_type': 'VA',
                'week_num': week_num,
                'icon': '🏠',
                'label': 'Online - Minggu VA',
                'description': 'Semua kelas online (tidak ada tatap muka)',
                'detailed_header': '🏠 MINGGU VA - KELAS ONLINE',
                'detailed_info': [
                    f'📅 Minggu ke-{week_num} ({date_range})',
                    '💻 Semua kelas dilaksanakan secara ONLINE',
                    '⚠️ TIDAK ADA tatap muka di kampus minggu ini',
                    '🏠 Kuliah dari rumah'
                ]
            }
        else:
            return {
                'is_va': False,
                'week_type': 'VB',
                'week_num': week_num,
                'icon': '🏫',
                'label': 'Tatap Muka - Minggu VB',
                'description': 'Semua kelas dilaksanakan tatap muka',
                'detailed_header': '🏫 MINGGU VB - TATAP MUKA',
                'detailed_info': [
                    f'📅 Minggu ke-{week_num} ({date_range})',
                    '🏫 Semua kelas dilaksanakan TATAP MUKA di kampus',
                    '✅ Hadir ke lokasi sesuai jadwal',
                    '📍 Cek lokasi ruangan di jadwal'
                ]
            }

    def _create_main_menu_keyboard(self):
        """Create main menu inline keyboard"""
        return {
            'inline_keyboard': [
                [
                    {'text': '📅 Lihat Jadwal - Mingguan', 'callback_data': 'jadwal_weekly'}
                ],
                [
                    {'text': '📆 Lihat Jadwal - Harian', 'callback_data': 'jadwal_daily_menu'}
                ],
                [
                    {'text': '📊 Stats', 'callback_data': 'stats'}
                ]
            ]
        }

    def _create_daily_menu_keyboard(self):
        """Create daily schedule menu with day buttons"""
        days = [
            ('Senin', 'day_monday'),
            ('Selasa', 'day_tuesday'),
            ('Rabu', 'day_wednesday'),
            ('Kamis', 'day_thursday'),
            ('Jumat', 'day_friday'),
            ('Sabtu', 'day_saturday'),
            ('Minggu', 'day_sunday')
        ]

        keyboard = []
        # Add days in rows of 2
        for i in range(0, len(days), 2):
            row = []
            for j in range(2):
                if i + j < len(days):
                    day_name, callback = days[i + j]
                    row.append({'text': day_name, 'callback_data': callback})
            keyboard.append(row)

        # Add back button
        keyboard.append([{'text': '🔙 Kembali ke Menu', 'callback_data': 'back_to_main'}])

        return {'inline_keyboard': keyboard}

    def format_daily_schedule_message(self, events, target_date: datetime.datetime):
        """Format pesan jadwal harian untuk hari tertentu"""
        day_name_id = self._format_date_id(target_date)

        # Get VA/VB status for the target date
        va_vb_status = self._get_va_vb_status(target_date)

        # Build detailed VA/VB info
        detailed_info = '\n'.join(va_vb_status['detailed_info'])

        header = [
            f"📆 <b>JADWAL {day_name_id.upper()}</b>",
            "",
            f"<b>{va_vb_status['detailed_header']}</b>",
            detailed_info,
            ""
        ]

        # Filter events for the target date
        target_date_only = target_date.date()
        day_events = []

        for event in events:
            start_info = event.get('start', {})
            start_raw = start_info.get('dateTime') or start_info.get('date')

            if not start_raw:
                continue

            is_all_day = 'date' in start_info

            if 'T' in start_raw:
                start_dt = datetime.datetime.fromisoformat(start_raw.replace('Z', '+00:00'))
                if start_dt.tzinfo is None:
                    start_dt = self.tz.localize(start_dt)
                else:
                    start_dt = start_dt.astimezone(self.tz)
            else:
                start_dt = datetime.datetime.fromisoformat(start_raw)
                start_dt = self.tz.localize(start_dt)

            if start_dt.date() == target_date_only:
                end_info = event.get('end', {})
                end_raw = end_info.get('dateTime') or end_info.get('date')

                if end_raw:
                    if 'T' in end_raw:
                        end_dt = datetime.datetime.fromisoformat(end_raw.replace('Z', '+00:00'))
                        if end_dt.tzinfo is None:
                            end_dt = self.tz.localize(end_dt)
                        else:
                            end_dt = end_dt.astimezone(self.tz)
                    else:
                        end_dt = datetime.datetime.fromisoformat(end_raw)
                        end_dt = self.tz.localize(end_dt)
                else:
                    end_dt = start_dt

                day_events.append((start_dt, end_dt, event, is_all_day))

        if not day_events:
            header.extend([
                "📭 <i>Tidak ada jadwal untuk hari ini</i>",
                "",
                self._build_quick_command_footer()
            ])
            return '\n'.join(header).strip()

        # Sort events by time
        day_events.sort(key=lambda x: x[0])

        message_lines = header.copy()

        for start_dt, end_dt, event, is_all_day in day_events:
            summary_raw = event.get('summary', 'Kuliah')
            summary = self._escape_html(summary_raw)
            location_raw = event.get('location', '').strip()
            location = self._escape_html(location_raw)

            description = event.get('description', '') or ''
            facilitator = self._extract_facilitator(description)
            class_profile = self._infer_class_profile(summary_raw, location_raw, description)

            if is_all_day:
                time_info = 'Sepanjang hari'
            else:
                time_info = f"{self._format_time_id(start_dt)}—{self._format_time_id(end_dt)}"

            # Modern card-style layout
            message_lines.append(f"⏰ <b>{time_info}</b>")
            message_lines.append(f"📚 {summary}")

            if location:
                message_lines.append(f"📍 {location}")

            if facilitator:
                message_lines.append(f"👤 {self._escape_html(facilitator)}")

            message_lines.append(f"{class_profile['category_icon']} {class_profile['category_label']}")
            message_lines.append('')  # Spacing between events

        message_lines.extend(['━━━━━━━━━━━━━━━━━━━', '', self._build_quick_command_footer()])

        return '\n'.join(message_lines).strip()

    def format_weekly_schedule_message(self, events, range_start, range_end):
        """Format pesan jadwal mingguan - Mobile-first, modern design"""
        display_end = range_end - datetime.timedelta(days=1)

        # Get VA/VB status for the current week
        now = datetime.datetime.now(self.tz)
        va_vb_status = self._get_va_vb_status(now)

        # Build detailed VA/VB info
        detailed_info = '\n'.join(va_vb_status['detailed_info'])

        header = [
            "📅 <b>JADWAL MINGGUAN</b>",
            "",
            f"📆 {self._format_short_date(range_start)} — {self._format_short_date(display_end)}",
            f"🌍 {config.TIMEZONE}",
            "",
            f"<b>{va_vb_status['detailed_header']}</b>",
            detailed_info,
            ""
        ]

        if not events:
            header.extend([
                "📭 <i>Tidak ada jadwal dalam 7 hari ke depan</i>",
                "",
                self._build_quick_command_footer()
            ])
            return ['\n'.join(header).strip()]

        events_by_date = {}

        for event in events:
            start_info = event.get('start', {})
            end_info = event.get('end', {})

            start_raw = start_info.get('dateTime') or start_info.get('date')
            end_raw = end_info.get('dateTime') or end_info.get('date')

            if not start_raw:
                continue

            is_all_day = 'date' in start_info

            if 'T' in start_raw:
                start_dt = datetime.datetime.fromisoformat(start_raw.replace('Z', '+00:00'))
                if start_dt.tzinfo is None:
                    start_dt = self.tz.localize(start_dt)
                else:
                    start_dt = start_dt.astimezone(self.tz)
            else:
                start_dt = datetime.datetime.fromisoformat(start_raw)
                start_dt = self.tz.localize(start_dt)

            if end_raw:
                if 'T' in end_raw:
                    end_dt = datetime.datetime.fromisoformat(end_raw.replace('Z', '+00:00'))
                    if end_dt.tzinfo is None:
                        end_dt = self.tz.localize(end_dt)
                    else:
                        end_dt = end_dt.astimezone(self.tz)
                else:
                    end_dt = datetime.datetime.fromisoformat(end_raw)
                    end_dt = self.tz.localize(end_dt)
            else:
                end_dt = start_dt

            event_date = start_dt.date()
            events_by_date.setdefault(event_date, []).append((start_dt, end_dt, event, is_all_day))

        max_len = 3500
        continuation_header = ["🗓️ <b>JADWAL (LANJUTAN)</b>"]
        sections = []
        current_lines = header.copy()

        def flush_current():
            if current_lines:
                sections.append('\n'.join(current_lines).strip())

        def reset_to(header_lines):
            nonlocal current_lines
            current_lines = header_lines.copy()

        def add_line(line: str):
            nonlocal current_lines
            if line == '' and not current_lines:
                return
            candidate = '\n'.join(current_lines + [line])
            if len(candidate) > max_len:
                flush_current()
                reset_to(continuation_header)
                if line == '':
                    return
                candidate = '\n'.join(current_lines + [line])
                if len(candidate) > max_len:
                    # if single line still too long, truncate gracefully
                    chunks = [segment.strip() for segment in line.split('\n') if segment.strip()]
                    for chunk in chunks:
                        add_line(chunk)
                    return
            current_lines.append(line)

        def add_lines(lines):
            for line in lines:
                add_line(line)

        for event_date in sorted(events_by_date.keys()):
            day_dt = datetime.datetime.combine(event_date, datetime.time())
            add_lines(['', f"━━━ <b>{self._format_date_id(day_dt)}</b> ━━━", ''])

            day_events = sorted(events_by_date[event_date], key=lambda item: item[0])

            for start_dt, end_dt, event, is_all_day in day_events:
                summary_raw = event.get('summary', 'Kuliah')
                summary = self._escape_html(summary_raw)
                location_raw = event.get('location', '').strip()
                location = self._escape_html(location_raw)

                description = event.get('description', '') or ''
                facilitator = self._extract_facilitator(description)
                class_profile = self._infer_class_profile(summary_raw, location_raw, description)
                highlights = self._extract_description_highlights(description, limit=1)
                if facilitator and highlights:
                    highlights = [h for h in highlights if facilitator.lower() not in h.lower()]

                if is_all_day:
                    time_info = 'Sepanjang hari'
                else:
                    time_info = f"{self._format_time_id(start_dt)}—{self._format_time_id(end_dt)}"

                # Modern card-style layout
                add_line(f"⏰ <b>{time_info}</b>")
                add_line(f"📚 {summary}")

                if location:
                    add_line(f"📍 {location}")

                if facilitator:
                    add_line(f"👤 {self._escape_html(facilitator)}")

                add_line(f"{class_profile['category_icon']} {class_profile['category_label']}")

                add_line('')  # Spacing between events

        add_lines(['', '━━━━━━━━━━━━━━━━━━━', '', self._build_quick_command_footer()])
        flush_current()

        return sections

    def format_reminder_message(self, event, hours_before=None):
        """Format pesan reminder - Mobile-first, modern design"""
        start_time = event['start'].get('dateTime', event['start'].get('date'))
        if 'T' in start_time:
            start_dt = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            if start_dt.tzinfo is None:
                start_dt = self.tz.localize(start_dt)
            else:
                start_dt = start_dt.astimezone(self.tz)
        else:
            start_dt = datetime.datetime.fromisoformat(start_time)
            start_dt = self.tz.localize(start_dt)

        summary_raw = event.get('summary', 'Kuliah')
        summary = self._escape_html(summary_raw)
        location_raw = event.get('location', '') or 'Lokasi belum ditentukan'
        location = self._escape_html(location_raw)
        description_raw = event.get('description', '') or ''

        theme = self._get_reminder_theme(hours_before)

        time_str = f"{self._format_time_id(start_dt)} WIB"
        date_str = self._format_date_id(start_dt)

        now = datetime.datetime.now(self.tz)
        time_diff = start_dt - now

        if time_diff.total_seconds() > 0:
            hours_left = int(time_diff.total_seconds() // 3600)
            minutes_left = int((time_diff.total_seconds() % 3600) // 60)
            countdown = f"{hours_left}j {minutes_left}m"
        else:
            countdown = "Dimulai sekarang!"

        class_profile = self._infer_class_profile(summary_raw, location_raw, description_raw)
        facilitator = self._extract_facilitator(description_raw)

        # Modern card-style reminder
        message_lines = [
            theme['headline'],
            "",
            f"📚 <b>{summary}</b>",
            f"{class_profile['category_icon']} {class_profile['category_label']}",
            "",
            f"⏰ {time_str}",
            f"📅 {date_str}",
            f"⏳ <b>{countdown}</b>",
            "",
            f"📍 {location}"
        ]

        if facilitator:
            message_lines.append(f"👤 {self._escape_html(facilitator)}")

        # Action items - cleaner format
        message_lines.extend([
            "",
            f"<b>{theme['checklist_title']}</b>"
        ])

        for tip in theme['checklist']:
            message_lines.append(f"  ✓ {tip}")

        message_lines.extend([
            "",
            f"💡 <i>{theme['cta']}</i>",
            "",
            self._build_quick_command_footer()
        ])

        return '\n'.join(message_lines).strip()

    def send_telegram_message(self, message, *, chat_id=None, reply_markup=None, count_as_reminder=True):
        """Kirim pesan ke Telegram"""
        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': str(chat_id or config.CHAT_ID),
            'text': message,
            'parse_mode': 'HTML'
        }

        if reply_markup:
            payload['reply_markup'] = json.dumps(reply_markup)

        try:
            response = self.http_session.post(
                url,
                data=payload,
                timeout=config.TELEGRAM_REQUEST_TIMEOUT
            )
            if response.status_code == 200:
                if count_as_reminder:
                    self.total_reminders_sent += 1
                print(f"✅ Message sent to Telegram")
                return True
            else:
                print(f"❌ Failed: {response.text}")
                return False
        except requests.RequestException as e:
            print(f"❌ Error: {e}")
            return False

    def get_stats_message(self):
        """Generate stats message"""
        now = datetime.datetime.now(self.tz)
        uptime = now - self.start_time

        # System stats
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        process = psutil.Process()

        # Scheduler stats
        jobs = self.scheduler.get_jobs()
        pending_jobs = len([j for j in jobs if j.next_run_time and j.next_run_time > now])

        next_runs = [job.next_run_time.astimezone(self.tz) for job in jobs if job.next_run_time]
        if next_runs:
            next_run = min(next_runs)
            next_delta = next_run - now
            next_in = f"{int(next_delta.total_seconds() // 60)} menit" if next_delta.total_seconds() > 60 else "< 1 menit"
            next_run_info = f"{next_run.strftime('%Y-%m-%d %H:%M:%S')} ({next_in})"
        else:
            next_run_info = 'Belum ada jadwal aktif'

        uptime_hours = uptime.seconds // 3600
        uptime_minutes = (uptime.seconds // 60) % 60

        reminder_config = ', '.join([f"{h}j" for h in config.REMINDER_HOURS])

        stats_lines = [
            '📊 <b>Dashboard Bot</b>',
            '',
            f'⏱️ Uptime: <b>{uptime.days}d {uptime_hours}j {uptime_minutes}m</b>',
            f'🕐 Server: {now.strftime("%H:%M:%S")}',
            '',
            '━━━━━━━━━━━━━━━━━━━',
            '',
            '<b>🤖 Status</b>',
            f'  Jobs aktif: {len(jobs)}',
            f'  Reminder terkirim: {self.total_reminders_sent}',
            f'  Jobs pending: {pending_jobs}',
            '',
            '<b>⏰ Reminder Berikutnya</b>',
            f'  {next_run_info}',
            '',
            '<b>💻 Resource</b>',
            f'  CPU: {cpu_percent}%',
            f'  Memory: {memory_percent}%',
            f'  Process: {process.memory_info().rss // (1024**2)} MB',
            '',
            '<b>⚙️ Konfigurasi</b>',
            f'  Interval: {reminder_config}',
            f'  Cek kalender: {config.CHECK_INTERVAL_MINUTES} menit',
            f'  Timezone: {config.TIMEZONE}',
            '',
            '<b>🔗 Koneksi</b>',
            '  Telegram: ✅',
            '  Calendar: ✅',
            '',
            '━━━━━━━━━━━━━━━━━━━',
            '',
            self._build_quick_command_footer()
        ]

        return '\n'.join(stats_lines).strip()

    def answer_callback_query(self, callback_query_id, text=None):
        """Answer a callback query to remove the loading state"""
        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/answerCallbackQuery"
        payload = {'callback_query_id': callback_query_id}
        if text:
            payload['text'] = text

        try:
            self.http_session.post(url, data=payload, timeout=5)
        except Exception as e:
            print(f"⚠️  Failed to answer callback query: {e}")

    def handle_callback_query(self, callback_query):
        """Handle inline keyboard button clicks"""
        callback_id = callback_query.get('id')
        data = callback_query.get('data', '')
        message = callback_query.get('message', {})
        chat = message.get('chat', {})
        chat_id = chat.get('id')

        if not chat_id:
            return

        print(f"🔘 Callback received: {data} from {chat_id}")

        # Answer the callback query immediately to remove loading state
        self.answer_callback_query(callback_id)

        # Check authentication for schedule-related callbacks in multi-user mode
        schedule_callbacks = ['jadwal_weekly', 'jadwal_daily_menu', 'stats']
        if self.multi_user_enabled and (data in schedule_callbacks or data.startswith('day_')):
            if not self.auth:
                self.send_telegram_message(
                    "❌ Multi-user support tidak tersedia",
                    chat_id=chat_id,
                    count_as_reminder=False
                )
                return

            # Check if user is logged in
            is_logged_in, user, error_msg = self.auth.require_login(chat_id)
            if not is_logged_in:
                # User not authenticated - send error message
                self.send_telegram_message(
                    error_msg,
                    chat_id=chat_id,
                    count_as_reminder=False
                )

                # Notify admin about unauthorized access attempt
                self._notify_admin_unauthorized_access(chat_id, f"Button: {data}")
                return

        try:
            if data == 'jadwal_weekly':
                # Show weekly schedule
                print(f"📅 Weekly schedule requested from {chat_id}")

                # Use multi-user database if enabled
                if self.multi_user_enabled and self.cmd_handler:
                    success, msg, events = self.cmd_handler.handle_jadwal_multiuser(chat_id)
                    if success and events:
                        # Format and send schedule
                        now = datetime.datetime.now(self.tz)
                        range_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                        range_end = range_start + datetime.timedelta(days=7)
                        schedule_sections = self.format_weekly_schedule_message(events, range_start, range_end)
                        for section in schedule_sections:
                            self.send_telegram_message(
                                section,
                                chat_id=chat_id,
                                count_as_reminder=False
                            )
                    else:
                        # Send error message
                        self.send_telegram_message(
                            msg if msg else "❌ Gagal memuat jadwal",
                            chat_id=chat_id,
                            count_as_reminder=False
                        )
                else:
                    # Fallback to Google Calendar (legacy mode)
                    service = self._get_calendar_service()
                    events, range_start, range_end = self.get_weekly_events(service)
                    schedule_sections = self.format_weekly_schedule_message(events, range_start, range_end)
                    for section in schedule_sections:
                        self.send_telegram_message(
                            section,
                            chat_id=chat_id,
                            count_as_reminder=False
                        )

            elif data == 'jadwal_daily_menu':
                # Show daily menu with day buttons
                menu_msg = (
                    "📆 <b>PILIH HARI</b>\n"
                    "\n"
                    "Pilih hari untuk melihat jadwal:"
                )
                self.send_telegram_message(
                    menu_msg,
                    chat_id=chat_id,
                    reply_markup=self._create_daily_menu_keyboard(),
                    count_as_reminder=False
                )

            elif data.startswith('day_'):
                # Show schedule for specific day
                day_map = {
                    'day_monday': 0,
                    'day_tuesday': 1,
                    'day_wednesday': 2,
                    'day_thursday': 3,
                    'day_friday': 4,
                    'day_saturday': 5,
                    'day_sunday': 6
                }

                day_offset = day_map.get(data)
                if day_offset is not None:
                    now = datetime.datetime.now(self.tz)
                    # Calculate the target date (next occurrence of that day)
                    current_weekday = now.weekday()
                    days_ahead = (day_offset - current_weekday) % 7
                    if days_ahead == 0:
                        days_ahead = 0  # Today if it's the same day
                    target_date = now + datetime.timedelta(days=days_ahead)

                    # Use multi-user database if enabled
                    if self.multi_user_enabled and self.cmd_handler:
                        success, msg, events = self.cmd_handler.handle_jadwal_multiuser(chat_id)
                        if success and events:
                            daily_msg = self.format_daily_schedule_message(events, target_date)
                            self.send_telegram_message(
                                daily_msg,
                                chat_id=chat_id,
                                reply_markup=self._create_daily_menu_keyboard(),
                                count_as_reminder=False
                            )
                        else:
                            self.send_telegram_message(
                                msg if msg else "❌ Gagal memuat jadwal",
                                chat_id=chat_id,
                                reply_markup=self._create_daily_menu_keyboard(),
                                count_as_reminder=False
                            )
                    else:
                        # Fallback to Google Calendar (legacy mode)
                        service = self._get_calendar_service()
                        events, _, _ = self.get_weekly_events(service)
                        daily_msg = self.format_daily_schedule_message(events, target_date)
                        self.send_telegram_message(
                            daily_msg,
                            chat_id=chat_id,
                            reply_markup=self._create_daily_menu_keyboard(),
                            count_as_reminder=False
                        )

            elif data == 'stats':
                # Show stats
                print(f"📊 Stats requested from {chat_id}")
                stats_msg = self.get_stats_message()
                self.send_telegram_message(
                    stats_msg,
                    chat_id=chat_id,
                    count_as_reminder=False
                )

            elif data == 'back_to_main':
                # Show main menu
                now = datetime.datetime.now(self.tz)
                va_vb_status = self._get_va_vb_status(now)

                # Build detailed VA/VB info
                detailed_info = '\n'.join(va_vb_status['detailed_info'])

                menu_msg = (
                    "🏠 <b>MENU UTAMA</b>\n"
                    "\n"
                    f"<b>{va_vb_status['detailed_header']}</b>\n"
                    f"{detailed_info}\n"
                    "\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "\n"
                    "💡 <b>Pilih menu di bawah ini:</b>"
                )
                self.send_telegram_message(
                    menu_msg,
                    chat_id=chat_id,
                    reply_markup=self._create_main_menu_keyboard(),
                    count_as_reminder=False
                )

        except Exception as e:
            print(f"❌ Error handling callback {data}: {e}")
            error_msg = "❌ Terjadi kesalahan. Silakan coba lagi."
            self.send_telegram_message(
                error_msg,
                chat_id=chat_id,
                count_as_reminder=False
            )

    def check_telegram_updates(self):
        """Check for Telegram commands and callback queries"""
        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/getUpdates"
        params = {
            'offset': self.last_update_id + 1,
            'timeout': config.TELEGRAM_POLL_TIMEOUT,
            'allowed_updates': ['message', 'callback_query']
        }

        try:
            response = self.http_session.get(
                url,
                params=params,
                timeout=config.TELEGRAM_REQUEST_TIMEOUT
            )
            if response.status_code != 200:
                print(f"❌ Failed to fetch updates: {response.text}")
                return

            data = response.json()
            if not data.get('ok'):
                print(f"❌ Telegram API returned error: {data}")
                return

            for update in data.get('result', []):
                self.last_update_id = update['update_id']

                # Handle callback queries (button clicks)
                callback_query = update.get('callback_query')
                if callback_query:
                    self.handle_callback_query(callback_query)
                    continue

                # Handle regular messages
                message = update.get('message') or update.get('edited_message')
                if not message:
                    continue

                text = (message.get('text') or '').strip()
                if not text:
                    continue

                chat = message.get('chat', {})
                chat_id = chat.get('id')
                if chat_id is None:
                    continue

                entities = message.get('entities', [])
                command_text = text
                if entities:
                    # Trim to the command entity if Telegram sent metadata
                    for entity in entities:
                        if entity.get('type') == 'bot_command':
                            offset = entity.get('offset', 0)
                            length = entity.get('length', len(text))
                            command_text = text[offset:offset + length]
                            break

                command = command_text.split()[0].lower()
                if '@' in command:
                    command = command.split('@', 1)[0]

                if command == '/start':
                    print(f"👋 Start command received from {chat_id}")

                    # Try multi-user handler first
                    if self.multi_user_enabled and self.cmd_handler:
                        welcome_msg = self.cmd_handler.handle_start(chat_id)
                        if welcome_msg:
                            # Multi-user mode: use authentication-aware message
                            self.send_telegram_message(
                                welcome_msg,
                                chat_id=chat_id,
                                reply_markup=self._create_main_menu_keyboard(),
                                count_as_reminder=False
                            )
                            continue

                    # Fallback to single-user mode
                    # Get VA/VB status for current week
                    now = datetime.datetime.now(self.tz)
                    va_vb_status = self._get_va_vb_status(now)

                    # Build detailed VA/VB info
                    detailed_info = '\n'.join(va_vb_status['detailed_info'])

                    welcome_msg = (
                        "👋 <b>Selamat Datang!</b>\n"
                        "\n"
                        "🎓 <b>KRS Reminder Bot</b>\n"
                        "Asisten pintar untuk jadwal kuliahmu\n"
                        "\n"
                        "━━━━━━━━━━━━━━━━━━━\n"
                        "\n"
                        f"<b>{va_vb_status['detailed_header']}</b>\n"
                        f"{detailed_info}\n"
                        "\n"
                        "━━━━━━━━━━━━━━━━━━━\n"
                        "\n"
                        "<b>✨ Fitur Utama</b>\n"
                        "  🔔 Reminder otomatis (5j, 3j, 2j, 1j sebelum)\n"
                        "  📅 Sinkronisasi Google Calendar\n"
                        "  ⏰ Notifikasi tepat waktu\n"
                        "  📊 Monitoring real-time\n"
                        "\n"
                        "━━━━━━━━━━━━━━━━━━━\n"
                        "\n"
                        "💡 <b>Pilih menu di bawah ini:</b>"
                    )
                    self.send_telegram_message(
                        welcome_msg,
                        chat_id=chat_id,
                        reply_markup=self._create_main_menu_keyboard(),
                        count_as_reminder=False
                    )
                elif command == '/stats':
                    print(f"📊 Stats command received from {chat_id}")

                    # Check authentication in multi-user mode
                    if self.multi_user_enabled and self.auth:
                        is_logged_in, user, error_msg = self.auth.require_login(chat_id)
                        if not is_logged_in:
                            self.send_telegram_message(
                                error_msg,
                                chat_id=chat_id,
                                count_as_reminder=False
                            )
                            continue

                    stats_msg = self.get_stats_message()
                    self.send_telegram_message(
                        stats_msg,
                        chat_id=chat_id,
                        count_as_reminder=False
                    )
                elif command == '/jadwal':
                    print(f"🗓️ Jadwal command received from {chat_id}")

                    # Try multi-user first
                    if self.multi_user_enabled and self.cmd_handler:
                        success, msg, events = self.cmd_handler.handle_jadwal_multiuser(chat_id)
                        if success:
                            # Use events from database
                            now = datetime.datetime.now(self.tz)
                            range_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                            range_end = range_start + datetime.timedelta(days=7)
                            schedule_sections = self.format_weekly_schedule_message(events, range_start, range_end)
                            for section in schedule_sections:
                                self.send_telegram_message(section, chat_id=chat_id, count_as_reminder=False)
                        else:
                            self.send_telegram_message(msg, chat_id=chat_id, count_as_reminder=False)
                    else:
                        # Fallback to single-user mode
                        try:
                            service = self._get_calendar_service()
                            events, range_start, range_end = self.get_weekly_events(service)
                            schedule_sections = self.format_weekly_schedule_message(events, range_start, range_end)
                            for section in schedule_sections:
                                self.send_telegram_message(section, chat_id=chat_id, count_as_reminder=False)
                        except Exception as e:
                            print(f"❌ Error preparing weekly schedule: {e}")
                            error_msg = "❌ <b>Gagal memuat jadwal.</b>\nSilakan coba lagi nanti."
                            self.send_telegram_message(error_msg, chat_id=chat_id, count_as_reminder=False)

                # Multi-user commands
                elif command == '/login':
                    if self.multi_user_enabled and self.cmd_handler:
                        # Use full text for argument parsing, not just command_text
                        msg = self.cmd_handler.handle_login(chat_id, text.split())
                        self.send_telegram_message(msg, chat_id=chat_id, count_as_reminder=False)
                elif command == '/logout':
                    if self.multi_user_enabled and self.cmd_handler:
                        msg = self.cmd_handler.handle_logout(chat_id)
                        self.send_telegram_message(msg, chat_id=chat_id, count_as_reminder=False)

                # Admin commands
                elif command == '/admin_add_user':
                    if self.multi_user_enabled and self.cmd_handler:
                        # Use full text for argument parsing, not just command_text
                        msg = self.cmd_handler.handle_admin_add_user(chat_id, text.split())
                        self.send_telegram_message(msg, chat_id=chat_id, count_as_reminder=False)
                elif command == '/admin_list_users':
                    if self.multi_user_enabled and self.cmd_handler:
                        msg = self.cmd_handler.handle_admin_list_users(chat_id)
                        self.send_telegram_message(msg, chat_id=chat_id, count_as_reminder=False)
                elif command == '/admin_import_schedule':
                    if self.multi_user_enabled and self.cmd_handler:
                        msg = self.cmd_handler.handle_admin_import_schedule(chat_id, command_text.split())
                        self.send_telegram_message(msg, chat_id=chat_id, count_as_reminder=False)
                elif command == '/admin_delete_user':
                    if self.multi_user_enabled and self.cmd_handler:
                        msg = self.cmd_handler.handle_admin_delete_user(chat_id, command_text.split())
                        self.send_telegram_message(msg, chat_id=chat_id, count_as_reminder=False)
                else:
                    print(f"ℹ️  Unhandled command/text from {chat_id}: {text}")
        except requests.Timeout as e:
            # Timeout is expected with long polling, only log if it's not a read timeout
            if "Read timed out" not in str(e):
                print(f"⚠️  Telegram polling timeout: {e}")
        except requests.RequestException as e:
            print(f"⚠️  Telegram polling error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error in check_telegram_updates: {e}")

    def schedule_reminders(self, events):
        """Schedule reminders untuk events"""
        now = datetime.datetime.now(self.tz)
        scheduled_count = 0

        print(f"\n⏰ Scheduling reminders from {now.strftime('%Y-%m-%d %H:%M')}...")

        for event in events:
            start_time = event['start'].get('dateTime', None)
            if not start_time:
                print(f"⚠️  Skipping all-day event: {event.get('summary', 'No title')}")
                continue

            start_dt = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            if start_dt.tzinfo is None:
                start_dt = self.tz.localize(start_dt)
            else:
                start_dt = start_dt.astimezone(self.tz)

            event_id = event.get('id', '')
            event_summary = event.get('summary', 'Kuliah')

            print(f"\n📚 Event: {event_summary}")
            print(f"   Start: {start_dt.strftime('%Y-%m-%d %H:%M %Z')}")

            # Schedule multi-jam reminder
            for hours in config.REMINDER_HOURS:
                reminder_time = start_dt - datetime.timedelta(hours=hours)
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
                        print(f"   ✅ {hours}h before → {reminder_time.strftime('%Y-%m-%d %H:%M')}")
                    except Exception as e:
                        print(f"   ❌ Error scheduling {hours}h: {e}")
                elif reminder_time <= now:
                    print(f"   ⏭️  {hours}h before → Already passed")
                else:
                    print(f"   🔁 {hours}h before → Already scheduled/sent")

            # Exact time reminder
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
                        print(f"   ✅ Exact time → {start_dt.strftime('%Y-%m-%d %H:%M')}")
                    except Exception as e:
                        print(f"   ❌ Error scheduling exact time: {e}")
                elif start_dt <= now:
                    print(f"   ⏭️  Exact time → Already passed")
                else:
                    print(f"   🔁 Exact time → Already scheduled/sent")

        print(f"\n✅ Total {scheduled_count} new reminders scheduled")

    def send_reminder(self, event, hours_before):
        """Send reminder"""
        message = self.format_reminder_message(event, hours_before)
        if self.send_telegram_message(message):
            event_id = event.get('id', '')
            reminder_key = f"{event_id}_{hours_before}h" if hours_before else f"{event_id}_exact"
            self.sent_reminders.add(reminder_key)

    def check_and_schedule_events(self):
        """Check events dan schedule reminders - Multi-user support"""
        print(f"\n🔄 Checking events... ({datetime.datetime.now(self.tz).strftime('%Y-%m-%d %H:%M:%S')})")

        if self.multi_user_enabled:
            # Multi-user mode: check all users
            self.check_and_schedule_multiuser()
        else:
            # Single-user mode: use Google Calendar directly
            try:
                service = self._get_calendar_service()
                events = self.get_todays_events(service)
                if events:
                    self.schedule_reminders(events)
                else:
                    print("📭 No events today")
            except Exception as e:
                print(f"❌ Error: {e}")

    def check_and_schedule_multiuser(self):
        """Check and schedule reminders for all users"""
        try:
            users = self.db.list_all_users()
            print(f"👥 Checking {len(users)} users...")

            now = datetime.datetime.now(self.tz)
            end_time = now + datetime.timedelta(hours=36)

            total_events = 0
            for user in users:
                # Get user's schedules
                schedules = self.db.get_user_schedules(user['user_id'], now, end_time)

                if schedules:
                    print(f"  👤 {user['username']}: {len(schedules)} events")
                    # Convert to event format
                    events = self.cmd_handler._schedules_to_events(schedules)
                    # Schedule reminders with user context
                    self.schedule_reminders_for_user(events, user)
                    total_events += len(schedules)

            if total_events == 0:
                print("📭 No events for any user")
            else:
                print(f"✅ Processed {total_events} events")

        except Exception as e:
            print(f"❌ Error in multi-user scheduling: {e}")

    def schedule_reminders_for_user(self, events, user):
        """Schedule reminders for a specific user"""
        # Get user's active session to get chat_id
        sessions = self.db.get_active_session(user.get('telegram_chat_id', 0))
        if not sessions:
            print(f"  ⚠️  No active session for {user['username']}")
            return

        # Use existing schedule_reminders but with user context
        # For now, just use the default scheduling
        self.schedule_reminders(events)

    def _notify_admin_unauthorized_access(self, chat_id: int, action: str):
        """
        Notify admin when an unauthorized user attempts to access the bot

        Args:
            chat_id: Telegram chat ID of the unauthorized user
            action: Action attempted (e.g., "Command: /jadwal", "Button: jadwal_weekly")
        """
        if not self.multi_user_enabled or not self.admin:
            return

        try:
            # Get user info from Telegram
            url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/getChat"
            response = self.http_session.get(url, params={'chat_id': chat_id}, timeout=5)

            user_info = {}
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    chat_data = data.get('result', {})
                    user_info = {
                        'username': chat_data.get('username', 'N/A'),
                        'first_name': chat_data.get('first_name', 'N/A'),
                        'last_name': chat_data.get('last_name', ''),
                    }

            username = user_info.get('username', 'N/A')
            first_name = user_info.get('first_name', 'N/A')
            last_name = user_info.get('last_name', '')
            full_name = f"{first_name} {last_name}".strip()

            # Get admin's telegram_chat_id from admins table
            try:
                admins = self.db._request('GET', 'admins', params={'limit': '1'})
                if not admins:
                    print(f"⚠️  Cannot notify admin: no admins found in database")
                    return

                admin_telegram_id = admins[0].get('telegram_chat_id')
                if not admin_telegram_id:
                    print(f"⚠️  Cannot notify admin: admin telegram_chat_id not found")
                    return
            except Exception as e:
                print(f"⚠️  Cannot notify admin: error fetching admin - {e}")
                return

            # Send notification to admin
            notification_msg = (
                "🔔 <b>User Tidak Terdaftar Mencoba Akses Bot</b>\n\n"
                f"👤 <b>Nama:</b> {full_name}\n"
                f"🆔 <b>Username:</b> @{username if username != 'N/A' else 'tidak ada'}\n"
                f"💬 <b>Chat ID:</b> <code>{chat_id}</code>\n"
                f"📝 <b>Aksi:</b> {action}\n\n"
                "━━━━━━━━━━━━━━━━━━━\n\n"
                "💡 <b>Tambahkan user dengan:</b>\n"
                f"<code>/admin_add_user {username if username != 'N/A' else 'username'}</code>"
            )

            self.send_telegram_message(
                notification_msg,
                chat_id=admin_telegram_id,
                count_as_reminder=False
            )

            print(f"✅ Admin notified about unauthorized access from {chat_id}")

        except Exception as e:
            print(f"⚠️  Failed to notify admin about unauthorized access: {e}")

    def start(self):
        """Start bot"""
        print("="*50)
        print("🚀 KRS REMINDER BOT V2 - STARTED")
        print("="*50)
        print(f"📱 Telegram: @krs_reminderbot")
        print(f"👤 Chat ID: {config.CHAT_ID}")
        print(f"🌍 Timezone: {config.TIMEZONE}")
        print(f"⏰ Intervals: {config.REMINDER_HOURS} hours before")
        print(f"🔔 Exact Time: {'✅' if config.INCLUDE_EXACT_TIME_REMINDER else '❌'}")
        print(f"🔄 Check: Every {config.CHECK_INTERVAL_MINUTES} min")
        print("="*50)

        # Startup notification
        startup_msg = (
            "🚀 <b>KRS REMINDER BOT V2 ONLINE</b>\n"
            "────────────────────────────\n"
            "✅ Monitoring kalender aktif\n"
            f"⏰ Auto check tiap {config.CHECK_INTERVAL_MINUTES} menit\n"
            "📡 Reminder multi-jam siap jalan\n"
            f"{self._build_quick_command_footer()}"
        )

        self.send_telegram_message(startup_msg, count_as_reminder=False)

        # Initial check
        self.check_and_schedule_events()

        # Schedule periodic tasks
        self.scheduler.add_job(
            func=self.check_and_schedule_events,
            trigger='interval',
            minutes=config.CHECK_INTERVAL_MINUTES,
            id='periodic_check',
            replace_existing=True
        )

        # Start scheduler
        self.scheduler.start()
        print("\n✅ Scheduler started! Commands: /start, /jadwal, /stats")
        print("Press Ctrl+C to stop.\n")

        # Polling interval: use configured interval since long polling handles the wait
        poll_interval = config.TELEGRAM_POLL_INTERVAL_SECONDS

        try:
            while True:
                self.check_telegram_updates()
                time.sleep(poll_interval)
        except (KeyboardInterrupt, SystemExit):
            print("\n⏹️ Stopping...")
            self.scheduler.shutdown()

            shutdown_msg = "⏹️ <b>KRS REMINDER BOT STOPPED</b>\n\nBot has been shut down."
            self.send_telegram_message(shutdown_msg, count_as_reminder=False)
            print("👋 Goodbye!")
        finally:
            self.http_session.close()

if __name__ == "__main__":
    bot = KRSReminderBotV2()
    bot.start()
