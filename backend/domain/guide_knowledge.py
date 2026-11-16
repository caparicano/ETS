"""Base de conhecimento do Guia: carrega o manual (docs/guia) como texto único e estável.

O texto tem de ser determinístico (ordem fixa, sem datas) para o prompt caching funcionar.
"""
from functools import lru_cache
from pathlib import Path
import os

DEFAULT_GUIDE_DIR = Path(__file__).resolve().parents[2] / "docs" / "guia"


@lru_cache(maxsize=4)
def load_knowledge(guide_dir: str | None = None) -> str:
    base = Path(guide_dir or os.getenv("GUIDE_DOCS_DIR") or DEFAULT_GUIDE_DIR)
    if not base.is_dir():
        return ""
    parts = []
    for path in sorted(base.rglob("*.md")):
        rel = path.relative_to(base).as_posix()
        parts.append(f"<documento ficheiro=\"{rel}\">\n{path.read_text(encoding='utf-8').strip()}\n</documento>")
    return "\n\n".join(parts)
