"""Main entry point for running the bot via python -m krs_reminder.cli"""

from krs_reminder.bot import KRSReminderBotV2


def main():
    """Launch the bot runtime."""
    bot = KRSReminderBotV2()
    bot.start()


if __name__ == "__main__":
    main()

