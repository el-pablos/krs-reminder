"""Test that button JSON is correctly formatted for Telegram API"""

import json
from krs_reminder.bot import KRSReminderBotV2


def test_button_json_format():
    """Test that keyboard JSON is valid and correctly formatted"""
    print("🧪 Testing Button JSON Format\n")
    print("="*60)
    
    bot = KRSReminderBotV2()
    
    # Test main menu keyboard
    main_menu = bot._create_main_menu_keyboard()
    
    print("\n📱 Main Menu Keyboard JSON:")
    print("-" * 60)
    print(json.dumps(main_menu, indent=2, ensure_ascii=False))
    print("-" * 60)
    
    # Verify structure
    assert 'inline_keyboard' in main_menu, "Should have inline_keyboard key"
    assert isinstance(main_menu['inline_keyboard'], list), "inline_keyboard should be a list"
    assert len(main_menu['inline_keyboard']) == 3, "Should have 3 button rows"
    
    # Verify each button has required fields
    for row in main_menu['inline_keyboard']:
        assert isinstance(row, list), "Each row should be a list"
        for button in row:
            assert 'text' in button, "Button should have text"
            assert 'callback_data' in button, "Button should have callback_data"
            assert isinstance(button['text'], str), "Button text should be string"
            assert isinstance(button['callback_data'], str), "Button callback_data should be string"
    
    print("\n✅ Main menu keyboard JSON is valid")
    
    # Test daily menu keyboard
    daily_menu = bot._create_daily_menu_keyboard()
    
    print("\n📆 Daily Menu Keyboard JSON:")
    print("-" * 60)
    print(json.dumps(daily_menu, indent=2, ensure_ascii=False))
    print("-" * 60)
    
    # Verify structure
    assert 'inline_keyboard' in daily_menu, "Should have inline_keyboard key"
    assert isinstance(daily_menu['inline_keyboard'], list), "inline_keyboard should be a list"
    
    # Count total buttons
    button_count = sum(len(row) for row in daily_menu['inline_keyboard'])
    assert button_count == 8, f"Should have 8 buttons (7 days + back), got {button_count}"
    
    print("\n✅ Daily menu keyboard JSON is valid")
    
    # Test JSON serialization (what gets sent to Telegram)
    main_menu_json = json.dumps(main_menu)
    daily_menu_json = json.dumps(daily_menu)
    
    print("\n📤 Serialized JSON (what gets sent to Telegram):")
    print("-" * 60)
    print(f"Main menu length: {len(main_menu_json)} chars")
    print(f"Daily menu length: {len(daily_menu_json)} chars")
    print("-" * 60)
    
    # Verify it can be deserialized
    json.loads(main_menu_json)
    json.loads(daily_menu_json)
    
    print("\n✅ JSON serialization/deserialization works")
    print("\n✅ All button JSON tests: PASSED")
    
    return True


if __name__ == "__main__":
    try:
        success = test_button_json_format()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

