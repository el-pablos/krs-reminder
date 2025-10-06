"""Test complete reminder flow dengan mock event."""

import datetime

import pytz

from krs_reminder.bot import KRSReminderBotV2

def test_reminder_flow():
    print("🧪 TESTING REMINDER FLOW")
    print("="*60)

    # Create bot
    bot = KRSReminderBotV2()

    # Create mock event yang akan kuliah 2 jam dari sekarang
    tz = pytz.timezone('Asia/Jakarta')
    now = datetime.datetime.now(tz)
    kuliah_time = now + datetime.timedelta(hours=2)

    mock_event = {
        'id': 'test_event_123',
        'summary': '🧪 TEST: Cloud Computing',
        'location': 'Lab. Artificial Intelligen',
        'description': 'Mata kuliah Cloud Computing dengan Ibu Erina Rahmazani',
        'start': {
            'dateTime': kuliah_time.isoformat()
        },
        'end': {
            'dateTime': (kuliah_time + datetime.timedelta(hours=1, minutes=40)).isoformat()
        }
    }

    print(f"\n📅 Mock Event Created:")
    print(f"   Nama: {mock_event['summary']}")
    print(f"   Waktu: {kuliah_time.strftime('%H:%M')} WIB")
    print(f"   (2 jam dari sekarang)")
    print()

    # Test format untuk berbagai reminder
    print("📱 Testing Reminder Messages:\n")

    for hours in [5, 3, 2, 1]:
        print(f"--- {hours} JAM SEBELUM ---")
        msg = bot.format_reminder_message(mock_event, hours)
        print(f"Preview: {msg[:100]}...")
        print()

    print("--- TEPAT WAKTU ---")
    msg = bot.format_reminder_message(mock_event, None)
    print(f"Preview: {msg[:100]}...")
    print()

    # Test kirim 1 reminder
    print("="*60)
    print("📤 Testing Send Reminder (1 jam sebelum)...")
    msg_1h = bot.format_reminder_message(mock_event, 1)

    if bot.send_telegram_message(msg_1h):
        print("✅ Reminder sent successfully!")
        print("📱 Check your Telegram for the message")
    else:
        print("❌ Failed to send reminder")

    print("\n" + "="*60)
    print("🧪 TEST COMPLETED!")
    print("="*60)

if __name__ == "__main__":
    test_reminder_flow()
