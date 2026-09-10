#!/usr/bin/env python3
"""Add caption-safe evidence boundaries to the locked v1.2c picture.

The operation is reversible: it duplicates only indispensable source/scope
labels into the upper safe band and leaves narration, timing and subtitles
unchanged. Existing lower-third text remains in the picture as provenance but
is no longer the sole carrier of an evidentiary qualification.
"""
from __future__ import annotations

import csv
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "Pilot_01_Animatic_Scratch_Voice_00m00_10m02_v1.2c_caption_conform.mp4"
SRT = ROOT / "Pilot_01_Animatic_00m00_10m02_v1.2c_caption_conform.srt"
MASTER = ROOT / "Pilot_01_Animatic_Scratch_Voice_00m00_10m02_v1.2d_evidence_safezone.mp4"
PROXY = ROOT / "Pilot_01_v1.2d_Evidence_Safezone_Caption_Review_720p.mp4"
CSV = ROOT / "Pilot_01_v1.2d_Evidence_Safezone_Overlay_Map.csv"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

ROWS = [
    (64.0, 96.0, "LIMITED MUSEUM COLLECTION  /  NOT A RANDOM SAMPLE", "scope"),
    (96.0, 142.0, "SOURCE  /  AXALTA 2025 GLOBAL NEW-VEHICLE COLOR REPORT", "source"),
    (162.0, 174.0, "REVIEW EVIDENCE  /  PROPOSED RELATIONSHIP - NOT A UNIVERSAL LAW", "boundary"),
    (218.0, 231.0, "SOURCE  /  NIELSEN NORMAN GROUP  /  JAKOBS LAW", "source"),
    (241.0, 247.0, "BOUNDARY  /  FUNCTION DOES NOT REQUIRE ONE AESTHETIC", "boundary"),
    (247.0, 259.0, "ILLUSTRATION  /  VOCABULARY - NOT PREVALENCE DATA", "illustration"),
    (259.0, 273.0, "SOURCE  /  SINTEZA 2016  /  INVENTED IDENTITY", "source"),
    (294.0, 323.0, "SOURCE  /  McDONALDS CORPORATE HISTORY  /  COMPANY-AUTHORED", "source"),
    (323.0, 334.0, "BOUNDARY  /  VARIATION EXISTS - FREQUENCY NOT MEASURED", "boundary"),
    (364.0, 369.0, "MODEL  /  ONE CHRONOLOGY DOES NOT PROVE THE RULE", "boundary"),
    (397.0, 413.0, "SOURCE  /  SPOTIFY RESEARCH (2021)  /  MUSIC RECOMMENDATIONS ONLY", "source"),
    (413.0, 430.0, "EXPLANATORY MODEL  /  NOT A SPOTIFY FINDING", "boundary"),
    (437.0, 444.0, "MODEL  /  NOT A MEASURED UNIVERSAL LAW", "boundary"),
    (449.0, 460.0, "FIRST-PARTY CASE  /  VARIATION EXISTS - PREVALENCE NOT MEASURED", "boundary"),
    (460.0, 471.0, "PRIMARY DESIGN-SYSTEM DOCUMENTATION  /  DISTINCT USABLE SYSTEMS", "source"),
    (471.0, 482.0, "FIRST-PARTY NICHE CASE  /  NOT THE WHOLE CAR MARKET", "boundary"),
    (496.0, 507.0, "MECHANISM ILLUSTRATION  /  NOT PREVALENCE EVIDENCE", "illustration"),
    (527.0, 535.0, "BOUNDED SYNTHESIS  /  CASE-LINKED - NOT A GLOBAL ESTIMATE", "boundary"),
    (574.0, 589.5, "BOUNDARY  /  DISTINCTIVENESS HAS RISK - NO AUTOMATIC PREMIUM", "boundary"),
    (595.0, 601.0, "DEFENSIBLE  =  USEFUL - SPECIFIC - WORTH ITS TRADE-OFFS", "definition"),
]

COLORS = {
    "source": "7FB7C9",
    "scope": "E7C45A",
    "boundary": "D88770",
    "illustration": "E7C45A",
    "definition": "5BC6AB",
}


def esc(value: str) -> str:
    return value.replace("\\", r"\\").replace(":", r"\:")


def video_filter() -> str:
    chain = []
    for start, end, label, kind in ROWS:
        enabled = f"between(t,{start:.3f},{end:.3f})"
        chain.append(
            "drawbox=x=70:y=132:w=1780:h=58:color=0x121C29@0.94:t=fill:"
            f"enable='{enabled}'"
        )
        chain.append(
            f"drawtext=fontfile='{FONT}':text='{esc(label)}':fontcolor=0x{COLORS[kind]}:"
            f"fontsize=29:x=(w-text_w)/2:y=146:enable='{enabled}'"
        )
    return ",".join(chain)


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> None:
    if not SOURCE.exists() or not SRT.exists():
        raise SystemExit("Missing locked v1.2c source or caption file")

    with CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["start_s", "end_s", "kind", "upper_safe_band_label"])
        for start, end, label, kind in ROWS:
            writer.writerow([f"{start:.3f}", f"{end:.3f}", kind, label])

    run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(SOURCE),
        "-vf", video_filter(), "-map", "0:v:0", "-map", "0:a:0",
        "-frames:v", "15050", "-r", "25", "-c:v", "libx264", "-preset", "fast",
        "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(MASTER),
    ])

    subtitle_path = esc(str(SRT))
    run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(MASTER),
        "-vf", f"scale=1280:720,subtitles='{subtitle_path}':force_style='FontName=DejaVu Sans,FontSize=18,Outline=2,Shadow=0,MarginV=36'",
        "-map", "0:v:0", "-map", "0:a:0", "-frames:v", "15050", "-r", "25",
        "-c:v", "libx264", "-preset", "fast", "-crf", "24", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(PROXY),
    ])

    for path in (MASTER, PROXY):
        duration = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "stream=duration",
            "-select_streams", "v:0", "-of", "default=nw=1:nk=1", str(path),
        ], text=True).strip()
        frames = subprocess.check_output([
            "ffprobe", "-v", "error", "-count_frames", "-show_entries", "stream=nb_read_frames",
            "-select_streams", "v:0", "-of", "default=nw=1:nk=1", str(path),
        ], text=True).strip()
        if duration != "602.000000" or frames != "15050":
            raise SystemExit(f"{path.name}: expected 602.000000/15050, got {duration}/{frames}")
        run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"])


if __name__ == "__main__":
    main()
