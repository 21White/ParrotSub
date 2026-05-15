"""ParrotSub UI preferences (theme, language) – persisted separately from
the upstream realtime_subtitle backend config.
"""

from __future__ import annotations

import dataclasses
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict


CONFIG_PATH = "~/.config/parrotsub/parrotsub.config"


@dataclass
class UIConfig:
    theme: str = "light"   # "light" | "dark"
    locale: str = ""       # "" means "auto-detect from OS"

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


def _expand(path: str) -> str:
    return os.path.expanduser(path)


def get() -> UIConfig:
    path = _expand(CONFIG_PATH)
    if not os.path.exists(path):
        return UIConfig()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
    except Exception:
        return UIConfig()

    fields = UIConfig.__dataclass_fields__
    filtered = {k: v for k, v in data.items() if k in fields}
    try:
        return UIConfig(**filtered)
    except TypeError:
        return UIConfig()


def save(cfg: UIConfig) -> None:
    path = _expand(CONFIG_PATH)
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg.to_dict(), f, ensure_ascii=False, indent=2)
