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
import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, QThread, pyqtSignal


# Default mirror — set whenever the user hasn't overridden it. Honoured
# by ``huggingface_hub.snapshot_download`` and by ``mlx_whisper`` since
# they both read ``HF_ENDPOINT`` at call time.
DEFAULT_HF_ENDPOINT = "https://hf-mirror.com"

# Endpoints the model downloader tries, in order, before giving up. The
# user's currently-active ``HF_ENDPOINT`` (which may be either of these,
# or their own custom value) is always tried first; entries listed here
# that match are skipped on subsequent attempts so we never retry the
# same URL twice.
FALLBACK_DOWNLOAD_ENDPOINTS: tuple[str, ...] = (
    "https://hf-mirror.com",
    "https://huggingface.co",
)


# huggingface_hub's snapshot_download does NOT have a built-in per-file
# transfer timeout. When the China mirror starts streaming a multi-GB
# weights file and then stalls part-way through (very common), the call
# hangs forever – no error, no progress. We force a 60-second timeout
# per HTTP transfer so a stall fails fast and the endpoint-chain
# fallback kicks in.
DEFAULT_DOWNLOAD_TIMEOUT_SECONDS = 60


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
def _repo_cache_dir(repo_id: str) -> Path:
    """``mlx-community/whisper-X`` -> ``~/.cache/.../models--mlx-community--whisper-X``."""
    from huggingface_hub.constants import HF_HUB_CACHE  # honours HF_HOME etc.
    safe = repo_id.replace("/", "--")
    return Path(HF_HUB_CACHE) / f"models--{safe}"


def has_incomplete_download(repo_id: str) -> bool:
    """True if the cache has any ``.incomplete`` blob for ``repo_id``.

    HuggingFace writes ``<sha>.incomplete`` files while a download is in
    flight; if the transfer is interrupted, the partial file stays on
    disk forever. We need to surface that as "still not installed" so
    the UI badge stays accurate AND the user can retry without seeing
    the model marked as ready.
    """
    blobs = _repo_cache_dir(repo_id) / "blobs"
    if not blobs.is_dir():
        return False
    try:
        return any(p.suffix == ".incomplete" for p in blobs.iterdir())
    except OSError:
        return False


def cleanup_incomplete_downloads(repo_id: str) -> int:
    """Delete any ``.incomplete`` blobs for ``repo_id``. Returns count removed."""
    blobs = _repo_cache_dir(repo_id) / "blobs"
    if not blobs.is_dir():
        return 0
    removed = 0
    try:
        for p in blobs.iterdir():
            if p.suffix == ".incomplete":
                try:
                    p.unlink()
                    removed += 1
                except OSError:
                    pass
    except OSError:
        pass
    return removed


_WEIGHTS_GLOBS: tuple[str, ...] = (
    "*.safetensors",
    "*.npz",
    "*.bin",
    "*.gguf",
)


def is_model_installed(repo_id: str) -> bool:
    """Return True iff ``repo_id`` is fully downloaded in the HF cache.

    "Fully" means **all three** of these are true:

    1. ``config.json`` is in the snapshot directory (cheap proxy for
       "the repo has been initialised at all");
    2. The same snapshot directory contains at least one weights file
       (``*.safetensors`` / ``*.npz`` / ``*.bin`` / ``*.gguf``);
    3. There are no ``.incomplete`` blobs in ``blobs/`` (otherwise a
       weights file is still mid-transfer).

    Checks (2) and (3) protect us from the very common scenario where
    metadata + a few KBs of the weights got fetched, then the
    connection stalled. Without them the UI would falsely show ``✓``
    for a model that can't actually be loaded.
    """
    try:
        from huggingface_hub import try_to_load_from_cache
    except Exception:  # pragma: no cover – huggingface_hub is a dep
        return False
    try:
        cfg_path = try_to_load_from_cache(repo_id=repo_id, filename="config.json")
    except Exception:
        return False
    if not cfg_path or not Path(str(cfg_path)).exists():
        return False
    if has_incomplete_download(repo_id):
        return False
    snapshot_dir = Path(str(cfg_path)).parent
    for pattern in _WEIGHTS_GLOBS:
        if any(snapshot_dir.glob(pattern)):
            return True
    return False


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


def ensure_default_download_timeout() -> int:
    """Default ``HF_HUB_DOWNLOAD_TIMEOUT`` so big-file transfers fail fast.

    Without this, snapshot_download will stall forever when a mirror
    starts streaming a large file and then closes the socket part-way.
    Idempotent – respects the user's explicit choice if already set.
    """
    if not os.environ.get("HF_HUB_DOWNLOAD_TIMEOUT"):
        os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = str(DEFAULT_DOWNLOAD_TIMEOUT_SECONDS)
    try:
        return int(os.environ["HF_HUB_DOWNLOAD_TIMEOUT"])
    except (ValueError, KeyError):
        return DEFAULT_DOWNLOAD_TIMEOUT_SECONDS


def active_hf_endpoint() -> str:
    return os.environ.get("HF_ENDPOINT", "https://huggingface.co")


# ---------------------------------------------------------------------------
# Background download worker
# ---------------------------------------------------------------------------
class ModelDownloadWorker(QThread):
    """QThread that downloads a single whisper model in the background.

    The worker tries every endpoint in :data:`FALLBACK_DOWNLOAD_ENDPOINTS`
    (with the user's current ``HF_ENDPOINT`` first) until one succeeds.
    Emits:

    - ``attempting(repo_id, endpoint)`` before each attempt, so the UI
      can tell the user which mirror is being tried right now;
    - ``downloaded(repo_id, success, message)`` once the worker
      decides – either after the first successful attempt or after all
      endpoints have failed.
    """

    attempting = pyqtSignal(str, str)               # repo_id, endpoint_url
    # repo_id, done_bytes, total_bytes, speed_bps, eta_seconds
    progress = pyqtSignal(str, int, int, float, int)
    downloaded = pyqtSignal(str, bool, str)         # repo_id, success, msg

    def __init__(self, repo_id: str, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.repo_id = repo_id

    def run(self) -> None:  # noqa: D401 – Qt signature
        ensure_default_hf_endpoint()
        ensure_default_download_timeout()

        from parrotsub.downloader import (
            DownloadAbortedError,
            DownloadFailedError,
            DownloadProgress,
            download_repo,
        )

        endpoints = self._build_endpoint_chain()
        print(
            f"[parrotsub.download] {self.repo_id}: chain={endpoints}, "
            f"connect_timeout=30s, inactivity_timeout=60s",
            file=sys.stderr,
            flush=True,
        )

        def _on_attempt(endpoint: str) -> None:
            self.attempting.emit(self.repo_id, endpoint)

        def _on_progress(prog: "DownloadProgress") -> None:
            self.progress.emit(
                prog.repo_id,
                int(prog.done_bytes),
                int(prog.total_bytes),
                float(prog.speed_bps),
                int(prog.eta_seconds),
            )

        endpoint_errors: list[str] = []

        def _on_endpoint_error(endpoint: str, msg: str) -> None:
            endpoint_errors.append(f"{endpoint}: {msg}")

        try:
            download_repo(
                repo_id=self.repo_id,
                endpoints=endpoints,
                abort_check=self.isInterruptionRequested,
                on_progress=_on_progress,
                on_attempt=_on_attempt,
                on_endpoint_error=_on_endpoint_error,
            )
        except DownloadAbortedError:
            print(
                f"[parrotsub.download] {self.repo_id}: aborted by user",
                file=sys.stderr,
                flush=True,
            )
            self.downloaded.emit(self.repo_id, False, "aborted")
            return
        except DownloadFailedError as exc:
            msg = str(exc)
            print(
                f"[parrotsub.download] {self.repo_id}: FAIL {msg}",
                file=sys.stderr,
                flush=True,
            )
            # Stash the most recent endpoint errors too – they're usually
            # the actually-useful information.
            detail = msg
            if endpoint_errors:
                detail = f"{msg} | last attempts: {endpoint_errors[-3:]}"
            self.downloaded.emit(self.repo_id, False, detail)
            return
        except Exception as exc:
            # Anything else (programming bug, disk full, etc.) – be loud.
            msg = f"{type(exc).__name__}: {exc}"
            print(
                f"[parrotsub.download] {self.repo_id}: UNEXPECTED {msg}",
                file=sys.stderr,
                flush=True,
            )
            self.downloaded.emit(self.repo_id, False, msg)
            return

        print(
            f"[parrotsub.download] {self.repo_id}: SUCCESS",
            file=sys.stderr,
            flush=True,
        )
        self.downloaded.emit(self.repo_id, True, self.repo_id)

    @staticmethod
    def _build_endpoint_chain() -> list[str]:
        """Return the ordered, deduplicated list of endpoints to try.

        The currently-active ``HF_ENDPOINT`` is always first so the user's
        explicit preference (or our China-mirror default) gets the first
        crack. Everything in ``FALLBACK_DOWNLOAD_ENDPOINTS`` is appended
        afterwards, with the active endpoint deduplicated out.
        """
        active = os.environ.get("HF_ENDPOINT") or DEFAULT_HF_ENDPOINT
        ordered = [active, *FALLBACK_DOWNLOAD_ENDPOINTS]
        seen: set[str] = set()
        chain: list[str] = []
        for url in ordered:
            normalised = (url or "").rstrip("/")
            if not normalised or normalised in seen:
                continue
            seen.add(normalised)
            chain.append(normalised)
        return chain
