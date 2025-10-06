"""Test VA/VB system and inline keyboard buttons."""

import datetime
from krs_reminder.bot import KRSReminderBotV2


def test_va_vb_detection():
    """Test VA/VB week detection logic"""
    print("🧪 Testing VA/VB Week Detection\n")
    print("="*60)

    bot = KRSReminderBotV2()

    # Test current week (October 7, 2025 should be Week 2 = VB)
    now = datetime.datetime.now(bot.tz)
    week_num = bot._get_week_number(now)
    is_va = bot._is_va_week(now)
    status = bot._get_va_vb_status(now)

    print(f"\n📅 Current Date: {now.strftime('%Y-%m-%d %A')}")
    print(f"📊 Week Number: {week_num} (relative to Sept 29, 2025)")
    print(f"🔍 Is VA Week: {is_va}")
    print(f"📌 Week Type: {status['week_type']}")
    print(f"{status['icon']} {status['detailed_header']}")
    for info in status['detailed_info']:
        print(f"   {info}")

    # Test logic
    if week_num % 2 == 1:
        assert is_va == True, "Odd week should be VA"
        assert status['week_type'] == 'VA', "Should be VA week"
        assert status['icon'] == '🏠', "Should have home icon"
        print("\n✅ VA week detection: PASSED")
    else:
        assert is_va == False, "Even week should be VB"
        assert status['week_type'] == 'VB', "Should be VB week"
        assert status['icon'] == '🏫', "Should have school icon"
        print("\n✅ VB week detection: PASSED")

    # Test specific dates relative to semester start (Sept 29, 2025)
    print("\n" + "="*60)
    print("📊 Testing Specific Weeks (Semester Start: Sept 29, 2025):")
    print("="*60)

    test_dates = [
        (datetime.datetime(2025, 9, 29, 12, 0, tzinfo=bot.tz), 1, 'VA'),  # Week 1 (VA)
        (datetime.datetime(2025, 10, 6, 12, 0, tzinfo=bot.tz), 2, 'VB'),  # Week 2 (VB)
        (datetime.datetime(2025, 10, 7, 12, 0, tzinfo=bot.tz), 2, 'VB'),  # Week 2 (VB)
        (datetime.datetime(2025, 10, 13, 12, 0, tzinfo=bot.tz), 3, 'VA'), # Week 3 (VA)
        (datetime.datetime(2025, 10, 20, 12, 0, tzinfo=bot.tz), 4, 'VB'), # Week 4 (VB)
    ]

    for test_date, expected_week, expected_type in test_dates:
        week = bot._get_week_number(test_date)
        status = bot._get_va_vb_status(test_date)

        print(f"\n{test_date.strftime('%Y-%m-%d')} (Week {week})")
        print(f"  Expected: Week {expected_week} = {expected_type}")
        print(f"  Got: {status['icon']} {status['week_type']}")

        assert week == expected_week, f"Should be Week {expected_week}, got Week {week}"
        assert status['week_type'] == expected_type, f"Week {week} should be {expected_type}"

    print("\n✅ All VA/VB detection tests: PASSED")
    return True


def test_keyboard_creation():
    """Test inline keyboard creation"""
    print("\n\n🧪 Testing Inline Keyboard Creation\n")
    print("="*60)
    
    bot = KRSReminderBotV2()
    
    # Test main menu keyboard
    main_menu = bot._create_main_menu_keyboard()
    print("\n📱 Main Menu Keyboard:")
    print(f"   Buttons: {len(main_menu['inline_keyboard'])} rows")
    
    assert 'inline_keyboard' in main_menu, "Should have inline_keyboard"
    assert len(main_menu['inline_keyboard']) == 3, "Should have 3 button rows"
    
    for i, row in enumerate(main_menu['inline_keyboard'], 1):
        button = row[0]
        print(f"   {i}. {button['text']} → {button['callback_data']}")
    
    print("✅ Main menu keyboard: PASSED")
    
    # Test daily menu keyboard
    daily_menu = bot._create_daily_menu_keyboard()
    print("\n📆 Daily Menu Keyboard:")
    print(f"   Buttons: {len(daily_menu['inline_keyboard'])} rows")
    
    assert 'inline_keyboard' in daily_menu, "Should have inline_keyboard"
    assert len(daily_menu['inline_keyboard']) == 5, "Should have 5 rows (3 day rows + 1 extra + back)"
    
    button_count = 0
    for row in daily_menu['inline_keyboard']:
        for button in row:
            button_count += 1
            print(f"   • {button['text']} → {button['callback_data']}")
    
    assert button_count == 8, "Should have 8 buttons (7 days + back)"
    print("✅ Daily menu keyboard: PASSED")
    
    return True


def test_weekly_schedule_with_va_vb():
    """Test weekly schedule message includes VA/VB status"""
    print("\n\n🧪 Testing Weekly Schedule with VA/VB Status\n")
    print("="*60)

    bot = KRSReminderBotV2()

    try:
        service = bot._get_calendar_service()
        events, range_start, range_end = bot.get_weekly_events(service)
        schedule_sections = bot.format_weekly_schedule_message(events, range_start, range_end)

        print(f"\n📊 Generated {len(schedule_sections)} section(s)")

        # Check first section for VA/VB status
        first_section = schedule_sections[0]

        # Should contain detailed VA/VB header
        has_va_header = ('MINGGU VA - KELAS ONLINE' in first_section)
        has_vb_header = ('MINGGU VB - TATAP MUKA' in first_section)
        assert (has_va_header or has_vb_header), "Schedule should include detailed VA/VB header"

        # Should contain week number
        has_week_num = ('Minggu ke-' in first_section)
        assert has_week_num, "Schedule should include week number"

        # Should contain icon
        has_icon = ('🏠' in first_section or '🏫' in first_section)
        assert has_icon, "Schedule should include VA/VB icon"

        print("\n📱 Schedule Preview (first 600 chars):")
        print("-" * 60)
        print(first_section[:600])
        print("-" * 60)

        if has_va_header:
            print("\n✅ VA week detailed header found in schedule")
        else:
            print("\n✅ VB week detailed header found in schedule")

        print("✅ Weekly schedule with VA/VB: PASSED")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_daily_schedule_with_va_vb():
    """Test daily schedule message includes VA/VB status"""
    print("\n\n🧪 Testing Daily Schedule with VA/VB Status\n")
    print("="*60)

    bot = KRSReminderBotV2()

    try:
        service = bot._get_calendar_service()
        events, _, _ = bot.get_weekly_events(service)

        # Test for today
        now = datetime.datetime.now(bot.tz)
        daily_msg = bot.format_daily_schedule_message(events, now)

        # Should contain detailed VA/VB header
        has_va_header = ('MINGGU VA - KELAS ONLINE' in daily_msg)
        has_vb_header = ('MINGGU VB - TATAP MUKA' in daily_msg)
        assert (has_va_header or has_vb_header), "Daily schedule should include detailed VA/VB header"

        # Should contain week number
        has_week_num = ('Minggu ke-' in daily_msg)
        assert has_week_num, "Daily schedule should include week number"

        # Should contain icon
        has_icon = ('🏠' in daily_msg or '🏫' in daily_msg)
        assert has_icon, "Daily schedule should include VA/VB icon"

        print(f"\n📅 Daily Schedule for {now.strftime('%A, %d %B %Y')}")
        print("\n📱 Schedule Preview (first 600 chars):")
        print("-" * 60)
        print(daily_msg[:600])
        print("-" * 60)

        if has_va_header:
            print("\n✅ VA week detailed header found in daily schedule")
        else:
            print("\n✅ VB week detailed header found in daily schedule")

        print("✅ Daily schedule with VA/VB: PASSED")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "🎨 " * 20)
    print("  VA/VB SYSTEM & INLINE BUTTONS TEST SUITE")
    print("🎨 " * 20)
    
    tests = [
        ("VA/VB Detection", test_va_vb_detection),
        ("Keyboard Creation", test_keyboard_creation),
        ("Weekly Schedule with VA/VB", test_weekly_schedule_with_va_vb),
        ("Daily Schedule with VA/VB", test_daily_schedule_with_va_vb)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\n{'='*60}")
    print(f"  RESULTS: {passed}/{total} tests passed")
    print(f"{'='*60}\n")
    
    return all(r for _, r in results)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

