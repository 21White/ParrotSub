"""Whisper model presence detection + background downloader.

ParrotSub bundles a fixed list of mlx-whisper models in ``AppConfig.
AllModelName``. Users start out with only the tiny English model on
disk (downloaded automatically the first time the backend loads), so
the Settings page needs to:

1. Show which models are already in the HuggingFace cache;
2. Let the user click a button to pull a missing model;
3. Pull from the China mirror (``https://hf-mirror.com``) by default.

This module owns the "model state" half of that feature so the Qt
layer can stay focused on widgets and signals.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, QThread, pyqtSignal


# Default mirror — set whenever the user hasn't overridden it. Honoured
# by ``huggingface_hub.snapshot_download`` and by ``mlx_whisper`` since
# they both read ``HF_ENDPOINT`` at call time.
DEFAULT_HF_ENDPOINT = "https://hf-mirror.com"


# ---------------------------------------------------------------------------
# Approximate on-disk sizes (HuggingFace cache totals, rounded). Used in the
# dropdown labels so the user knows how big the download will be.
# ---------------------------------------------------------------------------
_MODEL_SIZES: dict[str, str] = {
    "mlx-community/whisper-tiny.en-mlx": "~75 MB",
    "mlx-community/whisper-small-mlx": "~470 MB",
    "mlx-community/whisper-medium-mlx": "~1.5 GB",
    "mlx-community/whisper-turbo": "~1.6 GB",
    "mlx-community/whisper-large-v3-mlx": "~3.1 GB",
    "mlx-community/whisper-large-v3-turbo": "~1.6 GB",
}


def model_size_label(repo_id: str) -> str:
    """Return a human-readable approximate size, or ``""`` if unknown."""
    return _MODEL_SIZES.get(repo_id, "")


# ---------------------------------------------------------------------------
# Presence check
# ---------------------------------------------------------------------------
def is_model_installed(repo_id: str) -> bool:
    """Return True if ``repo_id`` looks fully downloaded in the HF cache.

    We rely on ``huggingface_hub.try_to_load_from_cache`` looking up the
    ``config.json`` file. If that returns a real path then the snapshot
    directory exists and the model has at least its metadata file – good
    enough for our UI badge. (A partial download would have config.json
    too, but mlx-whisper would re-fetch the missing weights on load, so
    we don't need to be stricter than this.)
    """
    try:
        from huggingface_hub import try_to_load_from_cache
    except Exception:  # pragma: no cover – huggingface_hub is a dep
        return False
    try:
        p = try_to_load_from_cache(repo_id=repo_id, filename="config.json")
    except Exception:
        return False
    return bool(p) and Path(str(p)).exists()


# ---------------------------------------------------------------------------
# Fallback picker — for the boot-time "the saved model isn't downloaded
# yet" case so we never trigger a silent network download.
# ---------------------------------------------------------------------------
def find_installed_model(cfg) -> Optional[str]:
    """Return the first model in ``cfg.AllModelName`` that's already on disk.

    Search order:

    1. ``cfg.ModelName`` itself (sanity check – callers typically only
       hit this function after already deciding it isn't installed, but
       the check costs nothing).
    2. Every entry in ``cfg.AllModelName`` in order.
    3. ``mlx-community/whisper-tiny.en-mlx`` as a last resort because
       it's the upstream realtime-subtitle default and the model the
       backend's first launch tends to fetch.

    Returns ``None`` when no whisper model is downloaded at all.
    """
    candidates = [
        getattr(cfg, "ModelName", ""),
        *list(getattr(cfg, "AllModelName", []) or []),
        "mlx-community/whisper-tiny.en-mlx",
    ]
    seen: set[str] = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        if is_model_installed(candidate):
            return candidate
    return None


# ---------------------------------------------------------------------------
# HuggingFace endpoint helper
# ---------------------------------------------------------------------------
def ensure_default_hf_endpoint() -> str:
    """Default ``HF_ENDPOINT`` to the China mirror if it isn't set yet.

    Idempotent. Returns the active endpoint. Users outside CN can set
    ``HF_ENDPOINT=https://huggingface.co`` in their shell before
    launching to override.
    """
    return os.environ.setdefault("HF_ENDPOINT", DEFAULT_HF_ENDPOINT)


def active_hf_endpoint() -> str:
    return os.environ.get("HF_ENDPOINT", "https://huggingface.co")


# ---------------------------------------------------------------------------
# Background download worker
# ---------------------------------------------------------------------------
class ModelDownloadWorker(QThread):
    """QThread that downloads a single whisper model in the background.

    Emits ``downloaded`` with ``(success: bool, message: str)`` so the
    caller can update the status pill and the dropdown badges.
    """

    downloaded = pyqtSignal(str, bool, str)  # repo_id, success, message_or_error

    def __init__(self, repo_id: str, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.repo_id = repo_id

    def run(self) -> None:  # noqa: D401 – Qt signature
        # Make sure the mirror is in effect for this thread too. Env vars
        # are process-global so this is just defensive.
        ensure_default_hf_endpoint()

        try:
            from huggingface_hub import snapshot_download
        except Exception as exc:
            self.downloaded.emit(self.repo_id, False, f"huggingface_hub missing: {exc}")
            return

        try:
            snapshot_download(repo_id=self.repo_id, repo_type="model")
        except Exception as exc:  # network errors, gated repos, etc.
            self.downloaded.emit(self.repo_id, False, str(exc))
            return

        self.downloaded.emit(self.repo_id, True, self.repo_id)
