#!/usr/bin/env python3
"""Build the fail-closed Pilot 01 executive human-review reel.

The reel concatenates already validated review surfaces. It never records a
decision and is explicitly marked as scratch-voice, review-only media.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WORK = ROOT / "pilot_01_executive_review_reel_v1_0_work"
OUT = ROOT / "Pilot_01_Executive_Human_Review_Reel_DO_NOT_PUBLISH_v1.0.mp4"
MANIFEST = ROOT / "Pilot_01_Executive_Human_Review_Reel_Manifest_v1.0.json"
CUES = ROOT / "Pilot_01_Executive_Human_Review_Reel_Cue_Sheet_v1.0.csv"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

SOURCES = [
    {
        "id": "MOTION",
        "path": ROOT / "Pilot_01_v1.2f_vs_v1.2g_Progressive_Focus_Comparison.mp4",
        "duration": 89.0,
        "audio": "mono",
        "title": "1 / 3 — MOTION PASS",
        "subtitle": "Compare v1.2f with v1.2g • retain or revoke",
        "decision": "MOTION = RETAIN_V1_2G or REVERT_V1_2F",
    },
    {
        "id": "VOICE",
        "path": ROOT / "Pilot_01_Blind_Voice_Interleaved_Comparison_Reel_v1.0.mp4",
        "duration": 411.0,
        "audio": "mono",
        "title": "2 / 3 — BLIND VOICE AUDITION",
        "subtitle": "Score A–D independently • REJECT_ALL remains valid",
        "decision": "VOICE = A, B, C, D, or REJECT_ALL",
    },
    {
        "id": "SOUND",
        "path": ROOT / "Pilot_01_Full_Film_Procedural_Sound_Design_Review_DO_NOT_PUBLISH_v1.0.mp4",
        "duration": 597.76,
        "audio": "stereo",
        "title": "3 / 3 — FULL-FILM SOUND DESIGN",
        "subtitle": "Opening + six chapter cues • judge fatigue continuously",
        "decision": "Seven independent choices = DRY or PROCEDURAL_V1",
    },
]


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def common_output() -> list[str]:
    return [
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-r", "25", "-g", "50", "-keyint_min", "50",
        "-sc_threshold", "0", "-threads", "1", "-c:a", "aac", "-b:a", "192k",
        "-ar", "48000", "-ac", "2", "-map_metadata", "-1", "-movflags", "+faststart",
    ]


def escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def make_slate(path: Path, duration: float, title: str, subtitle: str) -> None:
    vf = (
        f"drawtext=fontfile={FONT_BOLD}:text='{escape(title)}':"
        "fontcolor=white:fontsize=50:x=(w-text_w)/2:y=270,"
        f"drawtext=fontfile={FONT}:text='{escape(subtitle)}':"
        "fontcolor=0xB8C1CC:fontsize=28:x=(w-text_w)/2:y=355,"
        "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
        "text='REVIEW ONLY • SCRATCH VOICE • DO NOT PUBLISH':"
        "fontcolor=0xD8A25E:fontsize=22:x=(w-text_w)/2:y=640"
    )
    run(
        "ffmpeg", "-y", "-nostdin", "-v", "error",
        "-f", "lavfi", "-i", f"color=c=0x111820:s=1280x720:r=25:d={duration:.3f}",
        "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo:d={duration:.3f}",
        "-vf", vf, "-t", f"{duration:.3f}", *common_output(), str(path),
    )


def normalize_source(source: dict, path: Path) -> None:
    af = "aresample=48000"
    if source["audio"] == "mono":
        af = "pan=stereo|c0=0.70710678*c0|c1=0.70710678*c0,aresample=48000"
    run(
        "ffmpeg", "-y", "-nostdin", "-v", "error", "-i", str(source["path"]),
        "-map", "0:v:0", "-map", "0:a:0",
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=0x111820,setsar=1,fps=25",
        "-af", af, "-t", f"{source['duration']:.3f}", *common_output(), str(path),
    )


def main() -> None:
    for source in SOURCES:
        if not source["path"].is_file():
            raise SystemExit(f"Missing source: {source['path']}")
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir()

    entries: list[tuple[Path, float, str, str]] = []
    intro = WORK / "00_intro.mp4"
    make_slate(intro, 6.0, "PILOT 01 — EXECUTIVE REVIEW", "One reel • three human review surfaces")
    entries.append((intro, 6.0, "INTRO", "No decision"))

    for index, source in enumerate(SOURCES, start=1):
        slate = WORK / f"{index * 2 - 1:02d}_{source['id'].lower()}_slate.mp4"
        media = WORK / f"{index * 2:02d}_{source['id'].lower()}.mp4"
        make_slate(slate, 5.0, source["title"], source["subtitle"])
        normalize_source(source, media)
        entries.append((slate, 5.0, f"{source['id']}_BRIEF", source["decision"]))
        entries.append((media, source["duration"], source["id"], source["decision"]))

    outro = WORK / "07_outro.mp4"
    make_slate(outro, 8.0, "REVIEW COMPLETE", "Record decisions only in the v1.1 form • silence means HOLD")
    entries.append((outro, 8.0, "OUTRO", "All release gates remain closed"))

    concat_list = WORK / "concat.txt"
    concat_list.write_text("".join(f"file '{p.as_posix()}'\n" for p, _, _, _ in entries), encoding="utf-8")
    joined = WORK / "joined.mp4"
    run("ffmpeg", "-y", "-nostdin", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", "-map_metadata", "-1", str(joined))

    cursor_ms = 0
    chapters = [";FFMETADATA1"]
    cue_rows = []
    for path, duration, section, decision in entries:
        start = cursor_ms
        end = start + round(duration * 1000)
        chapters.extend(["[CHAPTER]", "TIMEBASE=1/1000", f"START={start}", f"END={end}", f"title={section}"])
        cue_rows.append([section, f"{start / 1000:.3f}", f"{end / 1000:.3f}", f"{duration:.3f}", decision])
        cursor_ms = end
    metadata = WORK / "chapters.ffmeta"
    metadata.write_text("\n".join(chapters) + "\n", encoding="utf-8")
    run(
        "ffmpeg", "-y", "-nostdin", "-v", "error", "-i", str(joined), "-i", str(metadata),
        "-map", "0:v:0", "-map", "0:a:0", "-map_metadata", "1", "-map_chapters", "1",
        "-metadata", "title=Pilot 01 executive human-review reel",
        "-metadata", "comment=REVIEW ONLY - SCRATCH VOICE - DO NOT PUBLISH",
        "-c", "copy", "-movflags", "+faststart", str(OUT),
    )

    with CUES.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["section", "start_seconds", "end_seconds", "duration_seconds", "decision_boundary"])
        writer.writerows(cue_rows)

    manifest = {
        "artifact": OUT.name,
        "status": "REVIEW_ONLY_SCRATCH_VOICE_DO_NOT_PUBLISH",
        "duration_seconds": cursor_ms / 1000,
        "expected_frames": round(cursor_ms / 1000 * 25),
        "video": "1280x720/25fps H.264 yuv420p",
        "audio": "AAC-LC stereo 48kHz 192kb/s target",
        "source_sha256": {s["id"]: sha256(s["path"]) for s in SOURCES},
        "output_sha256": sha256(OUT),
        "decision_policy": "No decision is inferred; silence and incomplete forms remain HOLD.",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
