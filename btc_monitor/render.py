from __future__ import annotations

import html
from pathlib import Path


def render_index(template: Path, destination: Path, title: str) -> None:
    content = template.read_text(encoding="utf-8")
    content = content.replace("{{PAGE_TITLE}}", html.escape(title))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
