# 🦜 ParrotSub

> Offline realtime speech-to-subtitle for Apple Silicon Macs, with a
> clean, shadcn-inspired desktop UI.

[中文 README](./README-zh.md)

ParrotSub turns whatever your microphone hears into live subtitles
**and** an optional translation, fully on-device. It bundles two pieces:

1. **`parrotsub`** – a modern PyQt6 desktop UI with a sidebar / header
   shell, light & dark themes, a teal "parrot feather" accent colour,
   draggable always-on-top floating overlays and an exports browser.
2. **`realtime_subtitle`** – the underlying offline pipeline (vendored
   from [@caoqiming](https://github.com/caoqiming/realtime-subtitle)
   under MIT). It does microphone capture (PyAudio), speech recognition
   (`mlx-whisper`), translation (`argos-translate` or online), speaker
   clustering (`speechbrain`) and exports to `audio.wav`,
   `subtitles.srt`, `subtitles.lrc` and an interactive
   `transcription.html`.

GitHub: <https://github.com/21White/ParrotSub>

## Highlights

- **Sidebar + header app shell** – 56 px icon rail (Tasks / Settings /
  Exports), 57 px header with title, version and a live status pill.
- **English / Chinese UI** – auto-detects the OS language on first
  launch; toggle anytime with the *languages* button in the sidebar.
  Choice persists across runs in
  `~/.config/parrotsub/parrotsub.config`.
- **shadcn-style theming** – design tokens, light & dark palettes, a
  teal brand accent (`#0d9488` light / `#14b8a6` dark) leading every
  primary action and active state. Light/dark choice also persisted.
- **Tasks page** – Start / Stop recording, dual *Original* and
  *Translation* cards that update live, on/off switches for two
  always-on-top floating overlays, one-click export.
- **Settings page** – every backend config field surfaced in 6 cards
  (Audio Input · Whisper Model · Translation · Subtitle Layout ·
  Floating Window · Speaker Recognition & Storage). Save / Reset
  buttons, type-aware inputs (combo, switch, text).
- **Floating overlays** – frameless, translucent, draggable, on-top,
  outline text rendering for readability over any background.
- **Exports page** – browse every saved session, see what artefacts
  exist, double-click to open in Finder.
- **Self-contained** – no external Python package required at
  install-time; both the UI and the backend ship together in this
  repository.

## Requirements

- macOS on **Apple Silicon** (mlx-whisper requirement)
- Python ≥ 3.9
- `portaudio` (`brew install portaudio`)

## Install

```bash
git clone https://github.com/21White/ParrotSub.git
cd ParrotSub

brew install portaudio

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .
```

> **Note** – the upstream backend pinned `speechbrain==1.0.3`, which is
> broken on `torchaudio>=2.9`. ParrotSub overrides this and installs
> `speechbrain>=1.1.0` for you.

## Run

```bash
parrotsub
# explicit form
parrotsub ui
# or
python -m parrotsub
```

Or just use the launcher script (auto-activates `./.venv`, sets
`HF_ENDPOINT=https://hf-mirror.com` for faster downloads in mainland
China, and re-installs the package in-place if needed):

```bash
./start.sh
```

You can also drive the offline parser straight from the CLI:

```bash
parrotsub parse -f my-audio.wav
# or, the legacy entry point:
realtime-subtitle parse -f my-audio.wav
```

## Repository layout

```
ParrotSub/
├── README.md                # this file
├── README-zh.md
├── LICENSE                  # Apache-2.0 (ParrotSub)
├── NOTICE                   # third-party attributions
├── THIRD_PARTY_LICENSES/
│   └── realtime-subtitle.LICENSE   # MIT, vendored backend
├── pyproject.toml
├── requirements.txt
├── environment.yml
├── start.sh
├── .gitignore
└── src/
    ├── parrotsub/           # UI shell
    │   ├── __init__.py
    │   ├── __main__.py
    │   ├── cli.py
    │   ├── theme.py         # shadcn-style design tokens + Qt stylesheet
    │   ├── icons.py         # Lucide-style SVG icon factory
    │   ├── app.py           # MainWindow shell (sidebar + header + stack)
    │   ├── widgets/
    │   │   ├── card.py
    │   │   ├── icon_button.py
    │   │   ├── sidebar.py
    │   │   ├── header.py
    │   │   ├── status_pill.py
    │   │   ├── switch.py
    │   │   ├── subtitle_view.py
    │   │   └── floating.py
    │   └── pages/
    │       ├── home.py
    │       ├── settings.py
    │       └── exports.py
    └── realtime_subtitle/    # vendored offline backend (MIT, glimmer)
        ├── __init__.py
        ├── app_config.py
        ├── cli.py
        ├── common.py
        ├── glimmer_speech_recognition.py
        ├── parse_audio.py
        ├── subtitle.py
        ├── template.html
        └── ui.py            # original PyQt6 UI (kept for parity)
```

## Configuration

Settings persist to `~/.config/glimmer/realtime-subtitle.config` so
existing configs from the upstream `realtime-subtitle` are picked up
unchanged. Use the **Settings** page in the UI, or edit the JSON file
manually.

Exports default to `~/Desktop/realtime-subtitle/<timestamp>/`; open them
from the **Exports** page.

## Credits

- Speech recognition pipeline: vendored from
  [`realtime-subtitle`](https://github.com/caoqiming/realtime-subtitle)
  by [@caoqiming](https://github.com/caoqiming) (MIT). Original
  copyright preserved in `THIRD_PARTY_LICENSES/`.
- Whisper inference: [`mlx-whisper`](https://github.com/ml-explore/mlx-examples)
- Offline translation: [`argos-translate`](https://github.com/argosopentech/argos-translate)
- Speaker recognition: [`speechbrain`](https://github.com/speechbrain/speechbrain)
- Icon set: [`lucide`](https://lucide.dev) (re-rendered as Qt icons)
- Design tokens: [`shadcn/ui`](https://ui.shadcn.com) HSL palette,
  reinterpreted in QSS

## License

ParrotSub is released under the **Apache License 2.0** —
see [`LICENSE`](./LICENSE) and [`NOTICE`](./NOTICE).

The vendored offline backend in `src/realtime_subtitle/` remains under
its original **MIT License** (Copyright (c) 2025 glimmer). Its license
text is preserved in
[`THIRD_PARTY_LICENSES/realtime-subtitle.LICENSE`](./THIRD_PARTY_LICENSES/realtime-subtitle.LICENSE)
as required.
