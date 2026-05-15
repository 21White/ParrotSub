#!/usr/bin/env bash
# ParrotSub launcher (Apple Silicon Mac).
#
# Behaviour:
#   1. Activate ./.venv if it exists (recommended).
#   2. Otherwise fall back to ../realtime-subtitle/.venv – useful for
#      contributors who used to run the upstream project from the
#      sibling folder.
#   3. Otherwise refuse and tell the user how to bootstrap one.
#   4. Set HF_ENDPOINT so HuggingFace model downloads use the China
#      mirror by default (override by exporting your own value).
#   5. Make sure parrotsub itself is installed in the active env.
#   6. Hand off to the `parrotsub` CLI.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export PATH="/opt/homebrew/bin:$PATH"
export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"

if [[ -f "$SCRIPT_DIR/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$SCRIPT_DIR/.venv/bin/activate"
elif [[ -f "$SCRIPT_DIR/../realtime-subtitle/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$SCRIPT_DIR/../realtime-subtitle/.venv/bin/activate"
else
  cat >&2 <<'EOF'
[parrotsub] No virtualenv found.

Bootstrap one with:

  brew install portaudio
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  pip install -e .

Then re-run ./start.sh
EOF
  exit 1
fi

# Make sure parrotsub is installed in the active env (editable, in-place).
if ! python -c "import parrotsub" >/dev/null 2>&1; then
  echo "[parrotsub] installing parrotsub in editable mode..." >&2
  pip install -q -e "$SCRIPT_DIR"
fi

# Best-effort: install pyobjc on macOS so the floating subtitle window
# can sit above other apps' windows (NSStatusWindowLevel). Failure is
# non-fatal; ParrotSub still works, the overlay just behaves like a
# normal "stay on top" window within the active app.
if [[ "$(uname -s)" == "Darwin" ]] \
    && ! python -c "import objc, AppKit" >/dev/null 2>&1; then
  echo "[parrotsub] installing pyobjc for guaranteed always-on-top overlays..." >&2
  pip install -q 'pyobjc-core>=10.0' 'pyobjc-framework-Cocoa>=10.0' || \
    echo "[parrotsub] pyobjc install failed; overlay will fall back to Qt's StaysOnTopHint." >&2
fi

exec parrotsub "$@"
