"""Integration-style smoke test for the /stats command output."""

from krs_reminder import config
from krs_reminder.bot import KRSReminderBotV2

def test_stats_command():
    """Test /stats command simulation"""
    print("🧪 Testing Stats Message Generation...\n")

    # Create bot instance
    bot = KRSReminderBotV2()

    # Generate stats
    stats_msg = bot.get_stats_message()

    print("📊 Generated Stats Message:")
    print("="*60)
    print(stats_msg)
    print("="*60)

    # Send to Telegram
    print("\n📱 Sending to Telegram...")
    if bot.send_telegram_message(stats_msg):
        print("✅ Stats message sent successfully!")
        return True
    else:
        print("❌ Failed to send stats")
        return False

if __name__ == "__main__":
    test_stats_command()
