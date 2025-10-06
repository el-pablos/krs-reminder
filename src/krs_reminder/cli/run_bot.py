"""Command-line entrypoint to launch the KRS Reminder bot."""

from __future__ import annotations

from krs_reminder.bot import KRSReminderBotV2


def main() -> None:
    """Launch the bot runtime."""
    bot = KRSReminderBotV2()
    bot.start()


if __name__ == "__main__":
    main()
