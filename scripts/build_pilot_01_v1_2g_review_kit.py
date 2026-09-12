#!/usr/bin/env python3
"""Build captioned continuous review and focused v1.2f/v1.2g comparison."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


WINDOWS = [
    (109.0, 123.0, "S2_AXALTA"),
    (146.0, 164.0, "S3_FLUENCY"),
    (255.0, 273.0, "S4_IDENTITY"),
    (302.0, 321.0, "S5_CHRONOLOGY"),
    (537.0, 557.0, "S8_FAILURE_MODE"),
]

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--srt", type=Path, required=True)
    parser.add_argument("--proxy", type=Path, required=True)
    parser.add_argument("--comparison", type=Path, required=True)
    args = parser.parse_args()

    for path in (args.baseline, args.candidate, args.srt):
        if not path.is_file():
            raise SystemExit(f"Missing input: {path}")
    args.proxy.parent.mkdir(parents=True, exist_ok=True)
    args.comparison.parent.mkdir(parents=True, exist_ok=True)

    subtitle_filter = (
        f"subtitles={args.srt.resolve()}:"
        "force_style='FontName=Nimbus Sans,FontSize=15,"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H00101010,"
        "BorderStyle=1,Outline=1,Shadow=0,Alignment=2,MarginV=18'"
    )
    if not args.proxy.is_file():
        run([
            "ffmpeg", "-hide_banner", "-y", "-i", str(args.candidate),
            "-vf", f"{subtitle_filter},scale=1280:720:flags=lanczos",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-r", "25", "-c:a", "aac", "-b:a", "160k",
            "-movflags", "+faststart", str(args.proxy),
        ])

    # Render one window at a time. This keeps peak memory bounded and makes a
    # failed comparison retry independent from the already-validated proxy.
    with tempfile.TemporaryDirectory(prefix="pilot_01_v12g_review_") as tmp:
        temp_dir = Path(tmp)
        clips: list[Path] = []
        for index, (start, end, chapter) in enumerate(WINDOWS):
            duration = end - start
            clip = temp_dir / f"clip_{index:02d}.mp4"
            filters = (
                f"[0:v]scale=960:540:flags=lanczos,"
                "pad=960:600:0:60:color=0x101216,"
                f"drawtext=fontfile={FONT}:text='v1.2f  |  {chapter}':"
                f"fontcolor=white:fontsize=25:x=24:y=17[lv];"
                f"[1:v]scale=960:540:flags=lanczos,"
                "pad=960:600:0:60:color=0x101216,"
                f"drawtext=fontfile={FONT}:text='v1.2g  |  {chapter}':"
                f"fontcolor=0xF4C95D:fontsize=25:x=24:y=17[rv];"
                "[lv][rv]hstack=inputs=2[vout]"
            )
            run([
                "ffmpeg", "-hide_banner", "-y", "-ss", str(start),
                "-i", str(args.baseline), "-ss", str(start),
                "-i", str(args.candidate), "-t", str(duration),
                "-filter_complex", filters, "-map", "[vout]", "-map", "1:a:0",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                "-pix_fmt", "yuv420p", "-r", "25", "-c:a", "aac", "-b:a", "160k",
                "-movflags", "+faststart", str(clip),
            ])
            clips.append(clip)
        concat_inputs: list[str] = []
        concat_graph: list[str] = []
        for index, clip in enumerate(clips):
            concat_inputs.extend(["-i", str(clip)])
            concat_graph.extend([f"[{index}:v]", f"[{index}:a]"])
        run([
            "ffmpeg", "-hide_banner", "-y", *concat_inputs,
            "-filter_complex",
            "".join(concat_graph)
            + f"concat=n={len(clips)}:v=1:a=1[vout][aout]",
            "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264",
            "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p",
            "-r", "25", "-frames:v", "2225", "-t", "89.0",
            "-c:a", "aac", "-b:a", "160k",
            "-movflags", "+faststart", str(args.comparison),
        ])


if __name__ == "__main__":
    main()
