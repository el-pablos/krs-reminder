"""Centralised configuration for the KRS Reminder system."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple


# ---------------------------------------------------------------------------
# Path configuration
# ---------------------------------------------------------------------------

BASE_DIR: Path = Path(__file__).resolve().parents[2]
CONFIG_DIR: Path = BASE_DIR / "configs"
CREDENTIALS_DIR: Path = CONFIG_DIR / "credentials"
TELEGRAM_DIR: Path = CONFIG_DIR / "telegram"


def _load_telegram_credentials(path: Path) -> Tuple[str, str]:
    """Load Telegram bot credentials from the given path.

    The file is expected to contain lines such as `TOKEN: <value>` and
    `CHAT_ID: <value>`. Both upper- or mixed-case keys are accepted.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Telegram credential file not found: {path}. "
            "Ensure configs/telegram/tele.txt exists."
        )

    token = None
    chat_id = None

    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or ":" not in line:
                continue
            key, value = [segment.strip() for segment in line.split(":", 1)]
            key_upper = key.upper()
            if key_upper in {"TOKEN", "TELEGRAM_TOKEN", "BOT_TOKEN", "TOKEN BOT TELEGRAM"} and not token:
                token = value
            elif key_upper in {"CHAT_ID", "CHATID", "ID OWNER"} and not chat_id:
                chat_id = value

    if not token or not chat_id:
        raise ValueError(
            f"Unable to parse bot token/chat ID from {path}. "
            "Expected lines like 'TOKEN: <value>' and 'CHAT_ID: <value>'."
        )

    return token, chat_id


TELEGRAM_FILE: Path = TELEGRAM_DIR / "tele.txt"
TELEGRAM_BOT_TOKEN, CHAT_ID = _load_telegram_credentials(TELEGRAM_FILE)

# Telegram polling & networking ------------------------------------------------
# Long polling timeout: how long Telegram server should wait for updates before returning
TELEGRAM_POLL_TIMEOUT = int(os.getenv("KRS_TELEGRAM_POLL_TIMEOUT", "30"))
# Request timeout: must be longer than poll timeout + network overhead
TELEGRAM_REQUEST_TIMEOUT = float(os.getenv("KRS_TELEGRAM_TIMEOUT", str(TELEGRAM_POLL_TIMEOUT + 10)))
# Interval between polling cycles (only used if polling returns early)
TELEGRAM_POLL_INTERVAL_SECONDS = float(os.getenv("KRS_TELEGRAM_POLL_INTERVAL", "1.0"))

# Google Calendar configuration -------------------------------------------------
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CREDENTIALS_FILE: Path = CREDENTIALS_DIR / "credentials.json"
TOKEN_FILE: Path = CREDENTIALS_DIR / "token.json"

# Optional write-enabled token (legacy compatibility)
TOKEN_WRITE_FILE: Path = CREDENTIALS_DIR / "token_write.json"

# Calendar service reuse --------------------------------------------------------
CALENDAR_SERVICE_TTL_SECONDS = int(os.getenv("KRS_CALENDAR_SERVICE_TTL", "600"))


# Timezone configuration --------------------------------------------------------
TIMEZONE = os.getenv("KRS_TIMEZONE", "Asia/Jakarta")


# Reminder configuration (hours before class) ----------------------------------
REMINDER_HOURS = [5, 3, 2, 1]  # Default: 5h, 3h, 2h, 1h before class starts
INCLUDE_EXACT_TIME_REMINDER = True


# Scheduler configuration ------------------------------------------------------
CHECK_INTERVAL_MINUTES = int(os.getenv("KRS_CHECK_INTERVAL_MINUTES", "30"))
