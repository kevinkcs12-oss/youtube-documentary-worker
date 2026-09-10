#!/usr/bin/env python3
"""Build reversible v1.2f by shortening two proven overlong static breaths."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "Pilot_01_Animatic_Scratch_Voice_00m00_10m02_v1.2e_motion_accent.mp4"
SOURCE_SRT = ROOT / "Pilot_01_Animatic_00m00_10m02_v1.2c_caption_conform.srt"
MASTER = ROOT / "Pilot_01_Animatic_Scratch_Voice_00m00_09m57.760_v1.2f_pacing_trim.mp4"
SRT = ROOT / "Pilot_01_Animatic_00m00_09m57.760_v1.2f_pacing_trim.srt"
PROXY = ROOT / "Pilot_01_v1.2f_Pacing_Trim_Caption_Review_720p.mp4"

# Original-timeline cuts, aligned to 25 fps. Exactly 2.00 seconds of each
# detected silence is retained. Total removal: 4.24 s / 106 frames.
CUTS = [(210.64, 212.60), (287.76, 290.04)]


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def build_master() -> None:
    # Single-stream select/aselect avoids retaining three decoded 1080p branches.
    # Half-open intervals remove exactly 49 + 57 = 106 frames. Using
    # between() would include both endpoints and silently remove two extras.
    remove = "gte(t,210.64)*lt(t,212.60)+gte(t,287.76)*lt(t,290.04)"
    keep = f"not({remove})"
    filters = (
        f"[0:v]select='{keep}',setpts=N/(25*TB)[v];"
        f"[0:a]aselect='{keep}',asetpts=N/SR/TB[a]"
    )
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(SOURCE),
        "-filter_complex", filters, "-map", "[v]", "-map", "[a]",
        "-frames:v", "14944", "-r", "25", "-c:v", "libx264", "-preset", "fast",
        "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
        "-ar", "48000", "-movflags", "+faststart", str(MASTER),
    ])


def parse_time(value: str) -> float:
    h, m, tail = value.replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(tail)


def fmt_time(value: float) -> str:
    value = max(0.0, value)
    ms = round(value * 1000)
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def map_time(t: float) -> float:
    shift = 0.0
    for start, end in CUTS:
        if t < start:
            return t - shift
        if t <= end:
            return start - shift
        shift += end - start
    return t - shift


def build_srt() -> None:
    blocks = []
    pattern = re.compile(r"^(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})$")
    for raw in SOURCE_SRT.read_text(encoding="utf-8").strip().split("\n\n"):
        lines = raw.splitlines()
        match = pattern.match(lines[1])
        if not match:
            raise ValueError(f"Invalid SRT timing: {lines[1]}")
        start = map_time(parse_time(match.group(1)))
        end = map_time(parse_time(match.group(2)))
        if end <= start:
            end = start + 0.040
        lines[1] = f"{fmt_time(start)} --> {fmt_time(end)}"
        blocks.append("\n".join(lines))
    SRT.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def build_proxy() -> None:
    subtitle_filter = f"subtitles='{SRT.as_posix()}':force_style='FontName=DejaVu Sans,FontSize=17,Outline=2,Shadow=0,MarginV=42'"
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(MASTER),
        "-vf", f"scale=1280:720,{subtitle_filter}", "-c:v", "libx264", "-preset", "ultrafast",
        "-crf", "24", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart", str(PROXY),
    ])


def main() -> None:
    if not SOURCE.exists() or not SOURCE_SRT.exists():
        raise FileNotFoundError("v1.2e master and canonical SRT are required")
    build_srt()
    build_master()
    build_proxy()


if __name__ == "__main__":
    main()
