"""Utilities to make project modules importable from standalone scripts."""

from __future__ import annotations

import sys
from pathlib import Path


def bootstrap() -> Path:
    """Ensure the src directory is on ``sys.path`` and return the project root."""
    project_root = Path(__file__).resolve().parents[1]
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    return project_root
