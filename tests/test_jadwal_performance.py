"""Test /jadwal command performance and identify bottlenecks."""

import time
from krs_reminder.bot import KRSReminderBotV2


def test_jadwal_performance():
    """Test the performance of /jadwal command"""
    print("🧪 Testing /jadwal Command Performance\n")
    print("="*60)
    
    bot = KRSReminderBotV2()
    
    # Test 1: Calendar API call
    print("\n📊 Test 1: Calendar API Call")
    start = time.time()
    try:
        service = bot._get_calendar_service()
        api_time = time.time() - start
        print(f"✅ Calendar service initialized: {api_time:.3f}s")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 2: Get weekly events
    print("\n📊 Test 2: Fetch Weekly Events")
    start = time.time()
    try:
        events, range_start, range_end = bot.get_weekly_events(service)
        fetch_time = time.time() - start
        print(f"✅ Events fetched: {fetch_time:.3f}s ({len(events)} events)")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 3: Format schedule message
    print("\n📊 Test 3: Format Schedule Message")
    start = time.time()
    try:
        schedule_sections = bot.format_weekly_schedule_message(events, range_start, range_end)
        format_time = time.time() - start
        print(f"✅ Message formatted: {format_time:.3f}s ({len(schedule_sections)} sections)")
        
        # Show message size
        total_chars = sum(len(section) for section in schedule_sections)
        print(f"   Total characters: {total_chars}")
        print(f"   Sections: {len(schedule_sections)}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 4: Send to Telegram (simulate)
    print("\n📊 Test 4: Send to Telegram")
    start = time.time()
    try:
        for i, section in enumerate(schedule_sections, 1):
            success = bot.send_telegram_message(section, count_as_reminder=False)
            if not success:
                print(f"❌ Failed to send section {i}")
                return False
            time.sleep(0.1)  # Small delay between messages
        send_time = time.time() - start
        print(f"✅ Messages sent: {send_time:.3f}s ({len(schedule_sections)} messages)")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Calculate total time
    total_time = api_time + fetch_time + format_time + send_time
    
    print("\n" + "="*60)
    print("📊 PERFORMANCE SUMMARY")
    print("="*60)
    print(f"Calendar API:     {api_time:.3f}s ({api_time/total_time*100:.1f}%)")
    print(f"Fetch Events:     {fetch_time:.3f}s ({fetch_time/total_time*100:.1f}%)")
    print(f"Format Message:   {format_time:.3f}s ({format_time/total_time*100:.1f}%)")
    print(f"Send to Telegram: {send_time:.3f}s ({send_time/total_time*100:.1f}%)")
    print("-"*60)
    print(f"TOTAL TIME:       {total_time:.3f}s")
    print("="*60)
    
    # Performance evaluation
    if total_time < 3.0:
        print("\n✅ EXCELLENT: Response time under 3 seconds")
        return True
    elif total_time < 5.0:
        print("\n⚠️  ACCEPTABLE: Response time under 5 seconds")
        return True
    else:
        print("\n❌ SLOW: Response time over 5 seconds - needs optimization")
        return False


if __name__ == "__main__":
    test_jadwal_performance()

