"""Application entry point."""

from __future__ import annotations

import sys

from app import config
from app.ui import run_app
from app.utils import ensure_cache_files, load_json_file, resource_path


def main() -> int:
    cache_dir = ensure_cache_files()
    theme = load_json_file(resource_path("assets", "theme.json")) or config.DEFAULT_THEME
    return run_app(cache_dir, theme)


if __name__ == "__main__":
    sys.exit(main())
