from __future__ import annotations

from pathlib import Path
import re

from app import config
from app.ui_tokens import build_tokens


def test_brand_pressed_token_defined_for_light_and_dark_themes() -> None:
    light_tokens = build_tokens(config.DEFAULT_THEME, dark_mode=False)
    dark_tokens = build_tokens(config.DEFAULT_THEME, dark_mode=True)

    assert light_tokens.action_brand_pressed == "#1D4ED8"
    assert dark_tokens.action_brand_pressed == "#2563EB"


def test_all_stylesheet_token_references_exist_on_tokens() -> None:
    ui_source = Path("app/ui.py").read_text(encoding="utf-8")
    stylesheet_block = re.search(r"def _stylesheet\(self\) -> str:\n.*?return f\"\"\"(.*?)\"\"\"", ui_source, re.S)
    assert stylesheet_block is not None
    referenced_tokens = set(re.findall(r"t\.([a-zA-Z_][a-zA-Z0-9_]*)", stylesheet_block.group(1)))

    light_tokens = build_tokens(config.DEFAULT_THEME, dark_mode=False)
    missing = [name for name in sorted(referenced_tokens) if not hasattr(light_tokens, name)]

    assert missing == []
