#!/usr/bin/env python3
"""Build the reversible v1.2g progressive-focus motion pass.

The pass adds outline-only focus accents to five long graphic holds. It does
not change edit timing, audio, captions, claims, or the protected subtitle
zone (y=820..1040).
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ACCENTS = [
    # Axalta arithmetic: components, then the existing total.
    (111.04, 116.36, 90, 205, 335, 130, "F4C95D"),
    (116.36, 121.68, 690, 500, 520, 210, "F4C95D"),
    # Processing-fluency diagram: signal, route, recognition.
    (148.08, 152.74, 100, 420, 720, 390, "78B7CF"),
    (152.74, 157.40, 885, 560, 190, 115, "78B7CF"),
    (157.40, 162.08, 1095, 435, 690, 380, "78B7CF"),
    # Responsive identity: four existing lockups, left to right.
    (257.12, 260.62, 108, 455, 505, 330, "F4C95D"),
    (260.62, 264.12, 695, 495, 433, 250, "F4C95D"),
    (264.12, 267.62, 1205, 530, 312, 180, "F4C95D"),
    (267.62, 271.12, 1595, 560, 152, 120, "F4C95D"),
    # McDonald's chronology schematic: earlier state, transition, later state.
    (303.84, 308.84, 175, 495, 370, 210, "63C7BE"),
    (308.84, 313.84, 615, 585, 325, 115, "63C7BE"),
    (313.84, 318.84, 1045, 495, 370, 210, "63C7BE"),
    # Conclusion failure modes: one existing row at a time.
    (539.32, 544.54, 165, 305, 1590, 130, "FF7B68"),
    (544.54, 549.76, 165, 490, 1590, 125, "FF7B68"),
    (549.76, 555.00, 165, 670, 1590, 125, "FF7B68"),
]


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--crf", default="18")
    parser.add_argument("--preset", default="veryfast")
    args = parser.parse_args()

    if not args.input.is_file():
        raise SystemExit(f"Missing input: {args.input}")
    args.output.parent.mkdir(parents=True, exist_ok=True)

    filters: list[str] = []
    for start, end, x, y, width, height, color in ACCENTS:
        if y + height > 820:
            raise SystemExit(f"Accent crosses subtitle safe zone: {(x, y, width, height)}")
        filters.append(
            "drawbox="
            f"x={x}:y={y}:w={width}:h={height}:"
            f"color=0x{color}@0.58:t=4:enable='between(t,{start:.2f},{end:.2f})'"
        )

    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-y",
            "-i",
            str(args.input),
            "-map",
            "0:v:0",
            "-map",
            "0:a?",
            "-vf",
            ",".join(filters),
            "-c:v",
            "libx264",
            "-preset",
            args.preset,
            "-crf",
            args.crf,
            "-pix_fmt",
            "yuv420p",
            "-r",
            "25",
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            str(args.output),
        ]
    )


if __name__ == "__main__":
    main()
