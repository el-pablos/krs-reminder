Reminder Multi-Jam untuk Kuliah dengan Google Kalender dan Telegram Bot
1. Persiapan Awal
1.1 Buat Project di Google Cloud Console

Buka Google Cloud Console
.

Klik "Select a Project" > "New Project".

Berikan nama project dan klik "Create".

Pilih API & Services > Library di menu kiri.

Cari Google Calendar API, pilih, dan klik Enable.

1.2 Buat Kredensial untuk API Google Kalender

Pilih Credentials pada menu API & Services.

Klik Create Credentials > Pilih OAuth 2.0 Client ID.

Pilih Web Application, beri nama, dan klik Create.

Download file credentials.json yang berisi kredensial untuk akses API.

Simpan file credentials.json di direktori kerja skrip Python.

1.3 Buat Bot Telegram

Buka Telegram, cari BotFather dan mulai percakapan.

Gunakan perintah /newbot untuk membuat bot baru. Ikuti instruksi dan beri nama bot.

Setelah bot dibuat, salin API Token yang diberikan oleh BotFather.

Catat chat_id (ini adalah ID pengguna atau grup tempat bot akan mengirim pesan). Kamu bisa mendapatkannya dengan mengirim pesan ke bot dan mengunjungi URL https://api.telegram.org/bot<API_TOKEN>/getUpdates untuk melihat chat_id.

2. Instalasi Dependensi Python

Untuk menjalankan skrip, kamu perlu menginstal beberapa pustaka Python:

pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib requests apscheduler

3. Skrip Python untuk Integrasi Google Kalender dan Telegram Bot

Berikut adalah skrip Python yang lengkap, yang akan melakukan hal-hal berikut:

Mengakses Google Kalender untuk mendapatkan jadwal kuliah hari ini.

Menghitung waktu reminder berdasarkan jam kuliah.

Mengirim reminder ke Telegram Bot pada waktu yang sudah ditentukan.

3.1 Skrip Python
import os
import datetime
import pytz
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from apscheduler.schedulers.blocking import BlockingScheduler

# Konfigurasi bot Telegram
TELEGRAM_BOT_TOKEN = 'PASTE_TOKEN_BOT'
CHAT_ID = 'PASTE_CHAT_ID'

# Konfigurasi Google Kalender
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

# Autentikasi ke Google Kalender
def authenticate():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    return creds

# Mengambil event hari ini dari Google Kalender
def get_todays_events(service):
    tz = pytz.timezone('Asia/Jakarta')
    now = datetime.datetime.now(tz)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)

    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_of_day.isoformat(),
        timeMax=end_of_day.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    return events_result.get('items', [])

# Fungsi untuk mengirim pesan ke Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message
    }
    requests.post(url, data=payload)

# Fungsi untuk menjadwalkan pengingat beberapa jam sebelum kuliah
def schedule_reminders(events):
    tz = pytz.timezone('Asia/Jakarta')
    now = datetime.datetime.now(tz)

    for event in events:
        start_time = event['start'].get('dateTime', None)
        if not start_time:
            continue
        start_dt = datetime.datetime.fromisoformat(start_time)
        hours_before = [5, 3, 2, 1]  # jam sebelum kuliah
        for h in hours_before:
            reminder_time = start_dt - datetime.timedelta(hours=h)
            if reminder_time > now:
                delay = (reminder_time - now).total_seconds()
                sched.add_job(lambda: send_telegram_message(
                    f"Reminder: Kuliah '{event['summary']}' akan dimulai jam {start_dt.strftime('%H:%M')} di {event.get('location','')}"), 'date', run_date=reminder_time)

# Scheduler untuk pengecekan event
sched = BlockingScheduler(timezone='Asia/Jakarta')

@sched.scheduled_job('interval', minutes=30)
def check_events_and_remind():
    creds = authenticate()
    service = build('calendar', 'v3', credentials=creds)
    events = get_todays_events(service)
    schedule_reminders(events)

# Menjalankan scheduler
sched.start()

3.2 Penjelasan Skrip

Autentikasi: Skrip akan memeriksa apakah token akses Google Kalender ada di file token.json. Jika tidak ada atau kedaluwarsa, akan meminta autentikasi ulang menggunakan OAuth 2.0.

Google Kalender: Skrip ini membaca semua event pada hari tersebut dari Google Kalender dan memeriksa waktu mulai kuliah.

Reminder: Berdasarkan waktu kuliah, bot Telegram akan mengirim reminder pada interval yang sudah ditentukan (misalnya, 5 jam, 3 jam, 2 jam, dan 1 jam sebelum kuliah dimulai).

Scheduler: Menggunakan apscheduler untuk menjadwalkan pengecekan setiap 30 menit dan mengirim reminder sesuai waktu yang dihitung.

4. Menjalankan Skrip

Setelah kamu menyiapkan semua konfigurasi di atas (Google Kalender, Telegram Bot, dan skrip Python), jalankan skrip Python dengan perintah:

python nama_script.py


Setelah itu, bot akan mulai memonitor jadwal kuliah hari ini, menghitung waktu pengingat, dan mengirim pesan ke Telegram sesuai dengan pengaturan waktu reminder yang telah ditentukan.

5. Pengaturan Waktu dan Zona

Pastikan zona waktu yang digunakan pada Google Kalender dan Telegram Bot sudah disesuaikan dengan zona waktu lokalmu, yaitu Asia/Jakarta dalam hal ini. Anda bisa mengganti sesuai kebutuhan.

6. Integrasi Lebih Lanjut

Jika kamu ingin menambah pengingat lebih banyak atau menambahkan fitur lain, berikut adalah beberapa ide yang bisa diterapkan:

Notifikasi tambahan dengan format yang lebih personal.

Menambahkan integrasi dengan platform lain (misalnya, Slack, WhatsApp).

Menggunakan cron job untuk menjalankan skrip di server secara otomatis tanpa perlu manual.