"""Command-line entrypoint for ParrotSub."""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="parrotsub",
        description="Modern desktop UI for realtime speech-to-subtitle (Apple Silicon Mac).",
    )
    subparsers = parser.add_subparsers(dest="command")

    ui_parser = subparsers.add_parser("ui", help="Launch the desktop UI (default).")
    ui_parser.set_defaults(func=_run_ui)

    parse_parser = subparsers.add_parser(
        "parse", help="Parse a wav file using realtime-subtitle's offline pipeline."
    )
    parse_parser.add_argument("-f", "--file", required=True, help="Path to a wav file.")
    parse_parser.add_argument(
        "-n", "--speakers", required=False, help="How many speakers are in the audio."
    )
    parse_parser.set_defaults(func=_run_parse)

    args = parser.parse_args()

    if not getattr(args, "command", None):
        _run_ui(args)
        return

    args.func(args)


def _run_ui(_args: argparse.Namespace) -> None:
    print(
        "[parrotsub] Booting UI. The first run downloads the whisper model, "
        "this may take a while...",
        flush=True,
    )
    from parrotsub.app import launch

    sys.exit(launch())


def _run_parse(args: argparse.Namespace) -> None:
    from realtime_subtitle.parse_audio import parse_audio

    speaker_num = int(args.speakers) if args.speakers else -1
    print(f"[parrotsub] Parsing file: {args.file}", flush=True)
    parse_audio(args.file, speaker_num=speaker_num)


if __name__ == "__main__":
    main()
