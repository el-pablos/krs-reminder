"""Comprehensive test for all bot commands and functionality."""

import time
from krs_reminder import config
from krs_reminder.bot import KRSReminderBotV2


def test_start_command():
    """Test /start command handler"""
    print("🧪 Testing /start command handler...\n")
    
    bot = KRSReminderBotV2()
    
    # Simulate /start command
    print("📝 Simulating /start command...")
    
    # Create a mock welcome message
    welcome_msg = (
        "👋 <b>SELAMAT DATANG DI KRS REMINDER BOT!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎓 Bot ini akan mengirimkan reminder otomatis untuk jadwal kuliah kamu!\n\n"
        "<b>📋 Fitur Utama:</b>\n"
        "• 🔔 Reminder multi-jam (5h, 3h, 2h, 1h sebelum kuliah)\n"
        "• ⏰ Notifikasi tepat waktu saat kuliah dimulai\n"
        "• 📅 Integrasi dengan Google Calendar\n"
        "• 📊 Monitoring status bot real-time\n\n"
        "<b>🤖 Perintah yang Tersedia:</b>\n"
        "• /start - Tampilkan pesan selamat datang ini\n"
        "• /jadwal - Lihat jadwal 7 hari ke depan\n"
        "• /stats - Lihat statistik dan status bot\n\n"
        "<b>✨ Status Bot:</b>\n"
        f"✅ Bot aktif dan monitoring kalender\n"
        f"⏰ Auto-check setiap {config.CHECK_INTERVAL_MINUTES} menit\n"
        f"🌍 Timezone: {config.TIMEZONE}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <i>Bot akan otomatis mengirim reminder sesuai jadwal kuliah kamu!</i>\n\n"
        f"{bot._build_quick_command_footer()}"
    )
    
    print("📊 Generated /start Message:")
    print("="*60)
    print(welcome_msg)
    print("="*60)
    
    # Send to Telegram
    print("\n📱 Sending /start response to Telegram...")
    if bot.send_telegram_message(welcome_msg, count_as_reminder=False):
        print("✅ /start command test passed!")
        return True
    else:
        print("❌ Failed to send /start message")
        return False


def test_stats_command():
    """Test /stats command"""
    print("\n🧪 Testing /stats command...\n")
    
    bot = KRSReminderBotV2()
    
    # Generate stats
    stats_msg = bot.get_stats_message()
    
    print("📊 Generated Stats Message:")
    print("="*60)
    print(stats_msg)
    print("="*60)
    
    # Send to Telegram
    print("\n📱 Sending to Telegram...")
    if bot.send_telegram_message(stats_msg, count_as_reminder=False):
        print("✅ /stats command test passed!")
        return True
    else:
        print("❌ Failed to send stats")
        return False


def test_jadwal_command():
    """Test /jadwal command"""
    print("\n🧪 Testing /jadwal command...\n")
    
    bot = KRSReminderBotV2()
    
    try:
        service = bot._get_calendar_service()
        events, range_start, range_end = bot.get_weekly_events(service)
        schedule_sections = bot.format_weekly_schedule_message(events, range_start, range_end)
        
        print(f"📊 Generated {len(schedule_sections)} schedule section(s):")
        print("="*60)
        for i, section in enumerate(schedule_sections, 1):
            print(f"\n--- Section {i} ---")
            print(section)
        print("="*60)
        
        # Send to Telegram
        print("\n📱 Sending to Telegram...")
        success = True
        for section in schedule_sections:
            if not bot.send_telegram_message(section, count_as_reminder=False):
                success = False
                break
            time.sleep(0.5)  # Small delay between messages
        
        if success:
            print("✅ /jadwal command test passed!")
            return True
        else:
            print("❌ Failed to send jadwal")
            return False
    except Exception as e:
        print(f"❌ Error testing /jadwal: {e}")
        return False


def test_config():
    """Test configuration values"""
    print("\n🧪 Testing configuration...\n")
    
    print("📊 Current Configuration:")
    print("="*60)
    print(f"TELEGRAM_POLL_TIMEOUT: {config.TELEGRAM_POLL_TIMEOUT}s")
    print(f"TELEGRAM_REQUEST_TIMEOUT: {config.TELEGRAM_REQUEST_TIMEOUT}s")
    print(f"TELEGRAM_POLL_INTERVAL_SECONDS: {config.TELEGRAM_POLL_INTERVAL_SECONDS}s")
    print(f"CHECK_INTERVAL_MINUTES: {config.CHECK_INTERVAL_MINUTES} minutes")
    print(f"REMINDER_HOURS: {config.REMINDER_HOURS}")
    print(f"INCLUDE_EXACT_TIME_REMINDER: {config.INCLUDE_EXACT_TIME_REMINDER}")
    print(f"TIMEZONE: {config.TIMEZONE}")
    print("="*60)
    
    # Validate configuration
    issues = []
    
    if config.TELEGRAM_REQUEST_TIMEOUT <= config.TELEGRAM_POLL_TIMEOUT:
        issues.append("⚠️  TELEGRAM_REQUEST_TIMEOUT should be > TELEGRAM_POLL_TIMEOUT")
    
    if config.TELEGRAM_POLL_TIMEOUT < 10:
        issues.append("⚠️  TELEGRAM_POLL_TIMEOUT is very short, may cause excessive polling")
    
    if config.CHECK_INTERVAL_MINUTES < 1:
        issues.append("⚠️  CHECK_INTERVAL_MINUTES is too short")
    
    if issues:
        print("\n⚠️  Configuration Issues Found:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("\n✅ Configuration is valid!")
        return True


def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("🚀 RUNNING COMPREHENSIVE BOT TESTS")
    print("="*60)
    
    results = {
        "Configuration": test_config(),
        "/start command": test_start_command(),
        "/stats command": test_stats_command(),
        "/jadwal command": test_jadwal_command(),
    }
    
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    print("="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED")
    print("="*60)
    
    return all_passed


if __name__ == "__main__":
    run_all_tests()

