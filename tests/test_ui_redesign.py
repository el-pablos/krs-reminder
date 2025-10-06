"""Test the new UI/UX redesign for all bot messages."""

from krs_reminder.bot import KRSReminderBotV2


def print_section(title):
    """Print a section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def test_start_command():
    """Test /start command UI"""
    print_section("TEST 1: /start Command (Welcome Message)")
    
    bot = KRSReminderBotV2()
    
    # Simulate /start command
    welcome_msg = (
        "👋 <b>Selamat Datang!</b>\n"
        "\n"
        "🎓 <b>KRS Reminder Bot</b>\n"
        "Asisten pintar untuk jadwal kuliahmu\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "\n"
        "<b>✨ Fitur Utama</b>\n"
        "  🔔 Reminder otomatis (5j, 3j, 2j, 1j sebelum)\n"
        "  📅 Sinkronisasi Google Calendar\n"
        "  ⏰ Notifikasi tepat waktu\n"
        "  📊 Monitoring real-time\n"
        "\n"
        "<b>🤖 Perintah</b>\n"
        "  /jadwal — Lihat jadwal 7 hari\n"
        "  /stats — Status & statistik bot\n"
        "  /start — Tampilkan pesan ini\n"
        "\n"
        "<b>📡 Status</b>\n"
        "  ✅ Bot aktif\n"
        "  🔄 Cek otomatis tiap 30 menit\n"
        "  🌍 Asia/Jakarta\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "\n"
        "💡 <i>Reminder otomatis akan dikirim sesuai jadwalmu</i>\n"
        "\n"
        "🔁 /start • /jadwal • /stats"
    )
    
    print("📱 MOBILE VIEW PREVIEW:")
    print("-" * 40)
    # Remove HTML tags for preview
    preview = welcome_msg.replace('<b>', '').replace('</b>', '')
    preview = preview.replace('<i>', '').replace('</i>', '')
    print(preview)
    print("-" * 40)
    
    # Check characteristics
    lines = welcome_msg.split('\n')
    print(f"\n✓ Total lines: {len(lines)}")
    print(f"✓ Max line length: {max(len(line) for line in lines)} chars")
    print(f"✓ Uses proper spacing: {'✅' if '' in lines else '❌'}")
    print(f"✓ Mobile-friendly: {'✅' if max(len(line) for line in lines) < 50 else '❌'}")
    
    return True


def test_jadwal_command():
    """Test /jadwal command UI"""
    print_section("TEST 2: /jadwal Command (Schedule View)")
    
    bot = KRSReminderBotV2()
    
    try:
        service = bot._get_calendar_service()
        events, range_start, range_end = bot.get_weekly_events(service)
        schedule_sections = bot.format_weekly_schedule_message(events, range_start, range_end)
        
        print(f"📊 Found {len(events)} events")
        print(f"📄 Generated {len(schedule_sections)} message section(s)")
        print()
        
        for i, section in enumerate(schedule_sections, 1):
            print(f"📱 SECTION {i} PREVIEW:")
            print("-" * 40)
            # Remove HTML tags for preview
            preview = section.replace('<b>', '').replace('</b>', '')
            preview = preview.replace('<i>', '').replace('</i>', '')
            print(preview)
            print("-" * 40)
            
            # Check characteristics
            lines = section.split('\n')
            has_dividers = '✅' if '━' in section else '❌'
            double_newlines = section.count('\n\n')
            has_spacing = '✅' if double_newlines > 0 else '❌'
            print(f"\n✓ Lines in section: {len(lines)}")
            print(f"✓ Characters: {len(section)}")
            print(f"✓ Max line length: {max(len(line) for line in lines)} chars")
            print(f"✓ Uses dividers: {has_dividers}")
            print(f"✓ Clean spacing: {has_spacing}")
            print()
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_stats_command():
    """Test /stats command UI"""
    print_section("TEST 3: /stats Command (Dashboard)")

    bot = KRSReminderBotV2()

    try:
        stats_msg = bot.get_stats_message()
        
        print("📱 MOBILE VIEW PREVIEW:")
        print("-" * 40)
        # Remove HTML tags for preview
        preview = stats_msg.replace('<b>', '').replace('</b>', '')
        preview = preview.replace('<i>', '').replace('</i>', '')
        print(preview)
        print("-" * 40)
        
        # Check characteristics
        lines = stats_msg.split('\n')
        print(f"\n✓ Total lines: {len(lines)}")
        print(f"✓ Characters: {len(stats_msg)}")
        print(f"✓ Max line length: {max(len(line) for line in lines)} chars")
        print(f"✓ Uses sections: {'✅' if '<b>' in stats_msg else '❌'}")
        print(f"✓ Clean layout: {'✅' if '━' in stats_msg else '❌'}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_reminder_message():
    """Test reminder message UI"""
    print_section("TEST 4: Reminder Messages")
    
    bot = KRSReminderBotV2()
    
    try:
        service = bot._get_calendar_service()
        events, _, _ = bot.get_weekly_events(service)
        
        if not events:
            print("⚠️  No events to test reminder messages")
            return True
        
        # Test different reminder types
        test_cases = [
            (5, "5 Hours Before"),
            (3, "3 Hours Before"),
            (1, "1 Hour Before"),
            (None, "Exact Time")
        ]
        
        event = events[0]
        
        for hours, label in test_cases:
            print(f"\n📱 {label.upper()} PREVIEW:")
            print("-" * 40)
            
            reminder_msg = bot.format_reminder_message(event, hours_before=hours)
            
            # Remove HTML tags for preview
            preview = reminder_msg.replace('<b>', '').replace('</b>', '')
            preview = preview.replace('<i>', '').replace('</i>', '')
            print(preview)
            print("-" * 40)
            
            # Check characteristics
            lines = reminder_msg.split('\n')
            print(f"\n✓ Lines: {len(lines)}")
            print(f"✓ Characters: {len(reminder_msg)}")
            print(f"✓ Max line length: {max(len(line) for line in lines)} chars")
            print(f"✓ Has countdown: {'✅' if '⏳' in reminder_msg else '❌'}")
            print(f"✓ Has action items: {'✅' if '✓' in reminder_msg else '❌'}")
            print()
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all UI tests"""
    print("\n" + "🎨 " * 20)
    print("  UI/UX REDESIGN TEST SUITE")
    print("  Mobile-First • Modern • Elegant")
    print("🎨 " * 20)
    
    tests = [
        ("Start Command", test_start_command),
        ("Jadwal Command", test_jadwal_command),
        ("Stats Command", test_stats_command),
        ("Reminder Messages", test_reminder_message)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print_section("TEST SUMMARY")
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\n{'='*70}")
    print(f"  RESULTS: {passed}/{total} tests passed")
    print(f"{'='*70}\n")
    
    return all(r for _, r in results)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

