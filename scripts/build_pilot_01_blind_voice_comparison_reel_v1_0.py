#!/usr/bin/env python3
"""Build an excerpt-interleaved A/B/C/D blind voice comparison reel."""

from __future__ import annotations

import csv
import json
import math
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "voice_decision_reel_sources_v1" / "pilot_01_free_voice_audition_review_pack_v1_0"
OUTPUT = ROOT / "Pilot_01_Blind_Voice_Interleaved_Comparison_Reel_v1.0.mp4"
TIMING = ROOT / "Pilot_01_Blind_Voice_Interleaved_Comparison_Timing_v1.0.csv"
MANIFEST = ROOT / "Pilot_01_Blind_Voice_Interleaved_Comparison_Manifest_v1.0.json"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FPS = 25
SLATE = 2.0
TAIL = 1.0

FILES = {
    "A": SOURCE_DIR / "Candidate_A_Blind_Audition_v1.0.mp3",
    "B": SOURCE_DIR / "Candidate_B_Blind_Audition_v1.0.mp3",
    "C": SOURCE_DIR / "Candidate_C_Blind_Audition_v1.0.mp3",
    "D": SOURCE_DIR / "Candidate_D_Blind_Audition_v1.0.mp3",
}

# Boundaries come from -38 dB / 0.4 s silence detection on the sealed review MP3s.
BOUNDS = {
    "A": [(0.0, 23.9279), (25.9112, 53.8532), (55.7857, 76.3815), (78.3620, 102.2470)],
    "B": [(0.0, 24.4151), (26.2615, 52.6058), (54.4165, 76.3765), (78.2487, 102.2100)],
    "C": [(0.0, 24.0538), (25.9143, 55.1023), (56.9622, 77.4907), (79.3469, 102.4110)],
    "D": [(0.0, 24.5571), (26.4061, 55.1593), (57.0356, 77.5786), (79.4284, 102.4120)],
}

EXCERPTS = [
    ("HOOK + SCOPE", "Curiosity  |  list rhythm  |  scope restraint"),
    ("NUMBERS + LIMIT", "Number clarity  |  emphasis  |  causal restraint"),
    ("MODEL BOUNDARY", "Spotify pronunciation  |  conceptual precision"),
    ("FINAL LANDING", "Warmth  |  silence discipline  |  no slogan voice"),
]

# Latin-square rotation: each candidate occupies each ordinal position once.
ORDERS = ["ABCD", "BCDA", "CDAB", "DABC"]


def q(text: str) -> str:
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’")


def main() -> None:
    for path in FILES.values():
        if not path.is_file():
            raise SystemExit(f"missing source: {path}")

    cmd = ["ffmpeg", "-y", "-hide_banner"]
    for letter in "ABCD":
        cmd += ["-i", str(FILES[letter])]

    filters: list[str] = []
    concat_inputs: list[str] = []
    timing_rows: list[dict[str, object]] = []
    timeline = 0.0
    clip_index = 0

    for excerpt_index, (title, criterion) in enumerate(EXCERPTS, start=1):
        s = f"s{excerpt_index}"
        filters.append(
            f"color=c=0x0B1017:s=1280x720:r={FPS}:d={SLATE}[{s}b];"
            f"[{s}b]drawtext=fontfile={FONT}:text='{q(f'EXCERPT {excerpt_index} OF 4')}':"
            "fontcolor=0x7ED6DF:fontsize=34:x=(w-text_w)/2:y=235,"
            f"drawtext=fontfile={FONT}:text='{q(title)}':fontcolor=white:fontsize=54:x=(w-text_w)/2:y=300,"
            f"drawtext=fontfile={FONT}:text='{q(criterion)}':fontcolor=0xB8C4D1:fontsize=25:x=(w-text_w)/2:y=390[{s}v]"
        )
        filters.append(f"anullsrc=r=48000:cl=mono:d={SLATE}[{s}a]")
        concat_inputs.extend([f"[{s}v]", f"[{s}a]"])
        timeline += SLATE

        order = ORDERS[excerpt_index - 1]
        for letter in order:
            input_index = "ABCD".index(letter)
            start, end = BOUNDS[letter][excerpt_index - 1]
            speech = end - start
            duration = math.ceil((speech + TAIL) * FPS) / FPS
            fade_out = max(0.0, speech - 0.03)
            a = f"a{clip_index}"
            w = f"w{clip_index}"
            v = f"v{clip_index}"
            base = f"b{clip_index}"
            filters.append(
                f"[{input_index}:a]atrim=start={start:.4f}:end={end:.4f},asetpts=PTS-STARTPTS,"
                f"aresample=48000,afade=t=in:st=0:d=0.02,afade=t=out:st={fade_out:.4f}:d=0.03,"
                f"apad=pad_dur={TAIL},atrim=duration={duration:.3f},asplit=2[{a}][{w}]"
            )
            filters.append(
                f"[{w}]showwaves=s=980x150:mode=line:rate={FPS}:colors=0x7ED6DF,format=rgba[wv{clip_index}]"
            )
            filters.append(
                f"color=c=0x0B1017:s=1280x720:r={FPS}:d={duration:.3f}[{base}];"
                f"[{base}]drawtext=fontfile={FONT}:text='{q(f'EXCERPT {excerpt_index} OF 4  —  {title}')}':"
                "fontcolor=0xB8C4D1:fontsize=27:x=(w-text_w)/2:y=95,"
                f"drawtext=fontfile={FONT}:text='{q(f'CANDIDATE {letter}')}':fontcolor=white:fontsize=74:"
                "x=(w-text_w)/2:y=245,"
                f"drawtext=fontfile={FONT}:text='{q(criterion)}':fontcolor=0x7ED6DF:fontsize=24:"
                f"x=(w-text_w)/2:y=585[pre{clip_index}];"
                f"[pre{clip_index}][wv{clip_index}]overlay=x=150:y=410:shortest=1[{v}]"
            )
            concat_inputs.extend([f"[{v}]", f"[{a}]"])
            timing_rows.append({
                "excerpt": excerpt_index,
                "title": title,
                "candidate": letter,
                "source_start": f"{start:.4f}",
                "source_end": f"{end:.4f}",
                "speech_seconds": f"{speech:.4f}",
                "reel_start": f"{timeline:.3f}",
                "reel_end": f"{timeline + duration:.3f}",
            })
            timeline += duration
            clip_index += 1

    filters.append("".join(concat_inputs) + f"concat=n={4 + clip_index}:v=1:a=1[outv][outa]")
    cmd += [
        "-filter_complex", ";".join(filters),
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "1",
        "-r", str(FPS), "-movflags", "+faststart", str(OUTPUT),
    ]
    subprocess.run(cmd, check=True)

    with TIMING.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=timing_rows[0].keys())
        writer.writeheader()
        writer.writerows(timing_rows)

    MANIFEST.write_text(json.dumps({
        "schema": "pilot-01-blind-voice-interleaved-comparison-v1.0",
        "candidate_labels": ["A", "B", "C", "D"],
        "excerpt_count": 4,
        "comparison_count": 16,
        "candidate_orders": ORDERS,
        "order_design": "Latin-square rotation; each candidate occupies each ordinal position once",
        "video": {"width": 1280, "height": 720, "fps": FPS},
        "audio": {"sample_rate_hz": 48000, "channels": 1},
        "expected_timeline_seconds": round(timeline, 3),
        "editorial_status": "BLIND_HUMAN_REVIEW_REQUIRED",
        "release_voice_selected": False,
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "timeline_seconds": round(timeline, 3), "clips": clip_index}, indent=2))


if __name__ == "__main__":
    main()
