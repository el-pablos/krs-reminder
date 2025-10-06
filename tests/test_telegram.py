"""Smoke test to send a Telegram message via the configured bot."""

import requests

from krs_reminder import config

def test_telegram():
    message = """🧪 <b>TEST NOTIFIKASI BOT</b>

✅ Bot berhasil terkoneksi!
✅ Konfigurasi benar
✅ Siap mengirim reminder

<b>Konfigurasi Aktif:</b>
📱 Chat ID: {chat_id}
⏰ Reminder: {hours} jam sebelum
🔔 Exact Time: {exact}
🌍 Timezone: {tz}

Bot siap digunakan! 🚀
""".format(
        chat_id=config.CHAT_ID,
        hours=config.REMINDER_HOURS,
        exact='Aktif' if config.INCLUDE_EXACT_TIME_REMINDER else 'Nonaktif',
        tz=config.TIMEZONE
    )

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': config.CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }

    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("✅ Pesan test berhasil terkirim ke Telegram!")
            print(f"📱 Chat ID: {config.CHAT_ID}")
            return True
        else:
            print(f"❌ Gagal kirim: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_telegram()
