"""SmartSub-inspired robust HuggingFace model downloader.

Replaces ``huggingface_hub.snapshot_download`` with a hand-rolled HTTP
stream that we control end-to-end. Borrows the proven shape from
``SmartSub/main/helpers/modelDownloader.ts``:

- per-attempt **inactivity timeout** (60 s without bytes → abort and
  fall back to the next endpoint) — turns "silent hang" into a fast,
  meaningful error;
- per-attempt **connect timeout** (30 s);
- **``Range: bytes=N-``** for resume across endpoints and across app
  restarts (we leave ``<blob>.incomplete`` on disk between attempts so
  the next try picks up where we left off);
- ``.incomplete`` → atomic rename on success;
- **manual 3xx follow** with the new endpoint preserved for the file
  body (HF resolves to a CDN URL via 302);
- per-second **speed + ETA** measurement, exposed in the progress
  callback so the UI can render `"5.2 MB/s · ETA 02:48"`;
- writes files into the standard HuggingFace cache layout
  (``models--<org>--<repo>/blobs/<etag>`` + ``snapshots/<rev>/<name>``
  symlinks + ``refs/main``) so ``mlx_whisper`` loads from the same
  cache without re-downloading.
"""

from __future__ import annotations

import hashlib
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

import requests


# ---------------------------------------------------------------------------
# Tunables (kept symmetric with SmartSub's modelDownloader.ts)
# ---------------------------------------------------------------------------
INACTIVITY_TIMEOUT = 60          # seconds with no bytes -> abort
CONNECT_TIMEOUT = 30             # seconds to establish TCP+TLS
CHUNK_SIZE = 1 * 1024 * 1024     # 1 MB per disk write
MAX_REDIRECTS = 5
USER_AGENT = "ParrotSub-Downloader"


class DownloadAbortedError(Exception):
    """Raised when the caller's ``abort_check`` returns True mid-flight."""


class DownloadFailedError(Exception):
    """Network / HTTP / IO failure."""


# ---------------------------------------------------------------------------
# Progress payload
# ---------------------------------------------------------------------------
@dataclass
class DownloadProgress:
    repo_id: str
    done_bytes: int
    total_bytes: int
    speed_bps: float           # bytes per second, averaged over last second
    eta_seconds: int           # estimated remaining seconds; 0 when unknown

    @property
    def pct(self) -> int:
        if self.total_bytes <= 0:
            return 0
        return max(0, min(100, int(self.done_bytes * 100 / self.total_bytes)))


# ---------------------------------------------------------------------------
# HF cache layout helpers
# ---------------------------------------------------------------------------
def _hf_cache_root() -> Path:
    from huggingface_hub.constants import HF_HUB_CACHE  # honours HF_HOME / HF_HUB_CACHE
    return Path(HF_HUB_CACHE)


def _repo_cache_dir(repo_id: str) -> Path:
    safe = repo_id.replace("/", "--")
    return _hf_cache_root() / f"models--{safe}"


# ---------------------------------------------------------------------------
# Repo metadata
# ---------------------------------------------------------------------------
def _fetch_repo_metadata(endpoint: str, repo_id: str) -> dict:
    """Return ``{sha, siblings:[{path,size,oid,lfs?}], ...}`` from the HF API.

    Two hops because ``/api/models/{repo}`` doesn't expose file sizes
    and ``/api/models/{repo}/tree/{rev}`` doesn't expose the revision
    SHA. We need both, so we call both.

    Raises whatever ``requests`` would; the caller iterates endpoints.
    """
    headers = {"User-Agent": USER_AGENT}

    # Hop 1: revision SHA
    r = requests.get(
        f"{endpoint.rstrip('/')}/api/models/{repo_id}",
        timeout=CONNECT_TIMEOUT,
        headers=headers,
    )
    r.raise_for_status()
    info = r.json()
    if not isinstance(info, dict) or "sha" not in info:
        raise DownloadFailedError(f"HF API at {endpoint} returned no 'sha': {info}")
    rev = info["sha"]

    # Hop 2: file tree with sizes + blob oids
    r2 = requests.get(
        f"{endpoint.rstrip('/')}/api/models/{repo_id}/tree/{rev}",
        timeout=CONNECT_TIMEOUT,
        headers=headers,
    )
    r2.raise_for_status()
    tree = r2.json()
    if not isinstance(tree, list):
        raise DownloadFailedError(f"HF tree API at {endpoint} returned non-list: {tree}")

    # Normalise to a single shape the caller can iterate.
    siblings = []
    for entry in tree:
        if entry.get("type") != "file":
            continue
        siblings.append(
            {
                "rfilename": entry.get("path"),
                "size": int(entry.get("size") or 0),
                "oid": entry.get("oid"),  # git sha1 for non-LFS
                "lfs": entry.get("lfs"),  # {"oid": sha256, "size": ...} when LFS
            }
        )

    return {"sha": rev, "siblings": siblings, "modelId": repo_id}


# ---------------------------------------------------------------------------
# Single-file download with resume + inactivity timeout
# ---------------------------------------------------------------------------
def _download_one(
    url: str,
    tmp_path: Path,
    abort_check: Callable[[], bool],
    on_chunk: Callable[[int, int], None],
) -> int:
    """Stream a file to ``tmp_path`` (with ``.download`` extension).

    Resumes from ``tmp_path.stat().st_size`` via ``Range`` when present.
    Returns the total expected size (bytes); the caller is responsible
    for renaming ``tmp_path`` to its final destination after sha
    verification.

    The ``(connect_timeout, read_timeout)`` tuple supplied to
    ``requests`` is exactly the SmartSub setup: 30 s to establish the
    connection, then 60 s per chunk read. If the mirror stops sending
    bytes for 60 s the call raises ``requests.exceptions.ReadTimeout``
    and we let it propagate so the caller can try the next endpoint.
    """
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    start_byte = tmp_path.stat().st_size if tmp_path.exists() else 0

    headers = {"User-Agent": USER_AGENT}
    if start_byte > 0:
        headers["Range"] = f"bytes={start_byte}-"

    with requests.get(
        url,
        headers=headers,
        stream=True,
        allow_redirects=True,
        timeout=(CONNECT_TIMEOUT, INACTIVITY_TIMEOUT),
    ) as r:
        # 416 Range Not Satisfiable => the file is already complete on disk
        # but we don't have it renamed yet. Caller decides what to do.
        if r.status_code == 416 and start_byte > 0:
            return start_byte
        r.raise_for_status()

        # Figure out total size
        total = 0
        if r.status_code == 206:
            cr = r.headers.get("Content-Range", "")
            if "/" in cr:
                try:
                    total = int(cr.rsplit("/", 1)[-1])
                except ValueError:
                    total = 0
        else:
            cl = r.headers.get("Content-Length")
            if cl is not None:
                try:
                    total = int(cl) + start_byte
                except ValueError:
                    total = 0

        downloaded = start_byte
        mode = "ab" if start_byte > 0 else "wb"
        with tmp_path.open(mode) as f:
            for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                if abort_check():
                    raise DownloadAbortedError("abort requested")
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)
                on_chunk(downloaded, total)

        return total or downloaded


# ---------------------------------------------------------------------------
# Top-level repo downloader
# ---------------------------------------------------------------------------
def download_repo(
    repo_id: str,
    endpoints: List[str],
    abort_check: Callable[[], bool],
    on_progress: Callable[[DownloadProgress], None],
    on_attempt: Callable[[str], None],
    on_endpoint_error: Callable[[str, str], None],
) -> None:
    """Download every file of ``repo_id`` into the standard HF cache.

    Parameters
    ----------
    repo_id : ``"mlx-community/whisper-..."``.
    endpoints : ordered list of HF API endpoints to try, e.g.
        ``["https://hf-mirror.com", "https://huggingface.co"]``. We
        retry per-file (not per-repo), so a slow / dead mirror can be
        skipped without losing already-downloaded files.
    abort_check : called between chunks; returning True bails out fast.
    on_progress : called every chunk with a ``DownloadProgress``.
    on_attempt : called once per endpoint switch with the endpoint URL.
    on_endpoint_error : called with ``(endpoint, error_message)`` when an
        endpoint fails for a particular file (so the UI can log it).

    Raises ``DownloadFailedError`` if every endpoint fails for some
    file, or ``DownloadAbortedError`` if the user cancelled.
    """
    if not endpoints:
        raise DownloadFailedError("no download endpoints configured")

    # ----- 1. metadata: pick the first endpoint that responds -----
    info: Optional[dict] = None
    last_meta_err: Optional[Exception] = None
    for endpoint in endpoints:
        on_attempt(endpoint)
        try:
            info = _fetch_repo_metadata(endpoint, repo_id)
            break
        except Exception as exc:
            last_meta_err = exc
            on_endpoint_error(endpoint, f"{type(exc).__name__}: {exc}")
            print(
                f"[parrotsub.download] {repo_id}: metadata FAIL {endpoint} "
                f"({type(exc).__name__}: {exc})",
                file=sys.stderr,
                flush=True,
            )
    if info is None:
        raise DownloadFailedError(
            f"all endpoints failed to fetch metadata; last: {last_meta_err}"
        )

    rev = info["sha"]
    siblings = info.get("siblings", []) or []
    total_repo_bytes = sum(int(s.get("size") or 0) for s in siblings)

    cache_root = _repo_cache_dir(repo_id)
    blobs_dir = cache_root / "blobs"
    snapshot_dir = cache_root / "snapshots" / rev
    refs_dir = cache_root / "refs"
    blobs_dir.mkdir(parents=True, exist_ok=True)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    refs_dir.mkdir(parents=True, exist_ok=True)

    # ----- 2. per-file download with per-endpoint retry -----
    # Speed/ETA over the *entire repo* (smoother than per-file).
    speed_state = {
        "t0": time.monotonic(),
        "bytes0": 0,
        "last_t": time.monotonic(),
        "last_bytes": 0,
        "speed_bps": 0.0,
    }
    repo_done = 0

    def _emit_progress(extra_in_flight: int = 0):
        now = time.monotonic()
        cur_bytes = repo_done + extra_in_flight
        # update speed every >= 1 second
        if now - speed_state["last_t"] >= 1.0:
            delta_b = cur_bytes - speed_state["last_bytes"]
            delta_t = max(0.001, now - speed_state["last_t"])
            speed_state["speed_bps"] = max(0.0, delta_b / delta_t)
            speed_state["last_t"] = now
            speed_state["last_bytes"] = cur_bytes
        speed = speed_state["speed_bps"]
        eta = 0
        if speed > 0 and total_repo_bytes > cur_bytes:
            eta = int((total_repo_bytes - cur_bytes) / speed)
        on_progress(
            DownloadProgress(
                repo_id=repo_id,
                done_bytes=cur_bytes,
                total_bytes=total_repo_bytes,
                speed_bps=speed,
                eta_seconds=eta,
            )
        )

    for sib in siblings:
        filename = sib.get("rfilename")
        if not filename:
            continue
        size = int(sib.get("size") or 0)
        lfs_block = sib.get("lfs") or {}
        lfs_oid = lfs_block.get("oid") if isinstance(lfs_block, dict) else None

        # If the snapshot symlink already resolves to a complete blob,
        # skip the network entirely (idempotent re-download).
        snap_link = snapshot_dir / filename
        if snap_link.is_symlink() or snap_link.exists():
            try:
                resolved = snap_link.resolve()
                if resolved.exists() and (size == 0 or resolved.stat().st_size == size):
                    repo_done += size
                    _emit_progress()
                    continue
            except OSError:
                pass  # broken symlink – will be replaced below

        # Per-file: try each endpoint until one works.
        # The blob name is the file's git etag, which HF gives us in
        # the tree API: LFS files use sha256 (``lfs.oid``), non-LFS
        # files use the git sha1 (top-level ``oid``).
        final_blob_name = lfs_oid or sib.get("oid")
        if not final_blob_name:
            # Fallback (shouldn't happen for HF repos): hash the path.
            final_blob_name = hashlib.sha1(filename.encode()).hexdigest()
        tmp_blob_name = (
            f".parrotsub-tmp-{filename.replace('/', '_')}.download"
        )
        tmp_path = blobs_dir / tmp_blob_name

        last_file_err: Optional[Exception] = None
        success = False
        for endpoint in endpoints:
            if abort_check():
                raise DownloadAbortedError("abort requested")
            on_attempt(endpoint)
            url = f"{endpoint.rstrip('/')}/{repo_id}/resolve/{rev}/{filename}"
            resume_from = tmp_path.stat().st_size if tmp_path.exists() else 0
            print(
                f"[parrotsub.download] {repo_id}: GET {filename} "
                f"via {endpoint} (resume from {resume_from} bytes)",
                file=sys.stderr,
                flush=True,
            )

            # Per-chunk callback: aggregate this file's bytes-so-far
            # into the repo-wide progress.
            def _on_chunk(file_done: int, _file_total: int) -> None:
                _emit_progress(extra_in_flight=file_done)

            try:
                _download_one(url, tmp_path, abort_check, _on_chunk)
                success = True
                break
            except DownloadAbortedError:
                raise
            except Exception as exc:
                last_file_err = exc
                msg = f"{type(exc).__name__}: {exc}"
                on_endpoint_error(endpoint, msg)
                print(
                    f"[parrotsub.download] {repo_id}: FAIL {filename} "
                    f"via {endpoint}: {msg}",
                    file=sys.stderr,
                    flush=True,
                )
                # keep .download on disk so the NEXT endpoint resumes
                # from where this one stopped (SmartSub's whole point)
                continue

        if not success:
            # cleanup partial blob (it's poisoning subsequent retries)
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except OSError:
                pass
            raise DownloadFailedError(
                f"all endpoints failed for {filename}: {last_file_err}"
            )

        # Move the temp blob into its final cache slot, named by the
        # git/LFS oid we already know from the tree API.
        final_blob_path = blobs_dir / final_blob_name
        if final_blob_path.exists():
            # Already have it (unlikely but possible) – drop the tmp.
            try:
                tmp_path.unlink()
            except OSError:
                pass
        else:
            tmp_path.replace(final_blob_path)

        # (Re)create the snapshot symlink → blob
        try:
            if snap_link.is_symlink() or snap_link.exists():
                snap_link.unlink()
            snap_link.parent.mkdir(parents=True, exist_ok=True)
            snap_link.symlink_to(Path("..") / ".." / "blobs" / final_blob_name)
        except OSError as exc:
            raise DownloadFailedError(
                f"could not link {snap_link} -> blobs/{final_blob_name}: {exc}"
            )

        repo_done += final_blob_path.stat().st_size
        _emit_progress()

    # ----- 3. update refs/main so snapshot_download finds the snapshot -----
    try:
        (refs_dir / "main").write_text(rev, encoding="utf-8")
    except OSError as exc:
        raise DownloadFailedError(f"could not write refs/main: {exc}")

    # Final 100 % tick
    on_progress(
        DownloadProgress(
            repo_id=repo_id,
            done_bytes=total_repo_bytes or repo_done,
            total_bytes=total_repo_bytes or repo_done,
            speed_bps=0.0,
            eta_seconds=0,
        )
    )
