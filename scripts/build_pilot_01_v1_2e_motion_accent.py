#!/usr/bin/env python3
"""Build the reversible v1.2e qualitative motion-accent candidate.

The only editorial change is a restrained, non-quantitative pulse/travel accent
over the explanatory loop from 06:53 to 07:10. Runtime, narration, captions,
and the evidence safe-zone copy remain unchanged.
"""

from __future__ import annotations

import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "Pilot_01_Animatic_Scratch_Voice_00m00_10m02_v1.2d_evidence_safezone.mp4"
SRT = ROOT / "Pilot_01_Animatic_00m00_10m02_v1.2c_caption_conform.srt"
OVERLAY = ROOT / "Pilot_01_v1.2e_Motion_Accent_Overlay.mov"
MASTER = ROOT / "Pilot_01_Animatic_Scratch_Voice_00m00_10m02_v1.2e_motion_accent.mp4"
PROXY = ROOT / "Pilot_01_v1.2e_Motion_Accent_Caption_Review_720p.mp4"
COMPARE = ROOT / "Pilot_01_v1.2d_vs_v1.2e_Loop_Comparison_06m53_07m10.mp4"

FPS = 25
WIDTH, HEIGHT = 1920, 1080
START, END = 413.0, 430.0
DURATION = END - START
FRAMES = int(DURATION * FPS)

# Centers sampled from the canonical v1.2d loop frame. The order follows the
# arrows already drawn in the picture. Motion contains no values or counters.
NODES = [
    (960, 390),   # familiar
    (1320, 520),  # recognized
    (1185, 825),  # chosen
    (735, 825),   # measured
    (600, 520),   # imitated
]
COLORS = [
    (244, 190, 83),
    (92, 150, 238),
    (84, 197, 188),
    (244, 111, 82),
    (244, 190, 83),
]


def run(cmd: list[str], *, stdin=None) -> None:
    subprocess.run(cmd, check=True, stdin=stdin)


def make_overlay() -> None:
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{WIDTH}x{HEIGHT}",
        "-r", str(FPS), "-i", "-", "-an", "-c:v", "qtrle",
        "-pix_fmt", "argb", str(OVERLAY),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    step_duration = DURATION / len(NODES)
    try:
        for frame in range(FRAMES):
            t = frame / FPS
            phase_index = min(int(t / step_duration), len(NODES) - 1)
            local = (t - phase_index * step_duration) / step_duration
            eased = 0.5 - 0.5 * math.cos(math.pi * min(max(local, 0.0), 1.0))

            canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
            draw = ImageDraw.Draw(canvas, "RGBA")
            x0, y0 = NODES[phase_index]
            x1, y1 = NODES[(phase_index + 1) % len(NODES)]
            color = COLORS[phase_index]

            # Slow halo pulse: one active stage at a time, deliberately subtle.
            pulse = 0.5 + 0.5 * math.sin(2 * math.pi * local)
            radius = 94 + 8 * pulse
            alpha = int(88 + 62 * pulse)
            # Clip the lower-node halo before the reserved caption band at y=820.
            bbox = (x0 - radius, y0 - radius, x0 + radius, min(y0 + radius, 810))
            draw.arc(bbox, 195, 345, fill=(*color, alpha), width=8)
            draw.arc(bbox, 15, 165, fill=(*color, alpha), width=8)

            # A single traveling bead communicates sequence, not magnitude.
            px = x0 + (x1 - x0) * eased
            py = y0 + (y1 - y0) * eased
            if py < 808:
                bead_r = 8
                draw.ellipse(
                    (px - bead_r, py - bead_r, px + bead_r, py + bead_r),
                    fill=(*color, 205),
                    outline=(246, 248, 250, 180),
                    width=2,
                )

            proc.stdin.write(canvas.tobytes())
    finally:
        proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg overlay encoder failed")


def build_master() -> None:
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(SOURCE), "-i", str(OVERLAY),
        "-filter_complex",
        f"[1:v]setpts=PTS+{START}/TB[accent];"
        f"[0:v][accent]overlay=eof_action=pass:enable='between(t,{START},{END})'[v]",
        "-map", "[v]", "-map", "0:a:0", "-frames:v", "15050", "-r", "25",
        "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p",
        "-c:a", "copy", "-movflags", "+faststart", str(MASTER),
    ])


def build_proxy() -> None:
    subtitle_filter = f"subtitles='{SRT.as_posix()}':force_style='FontName=DejaVu Sans,FontSize=17,Outline=2,Shadow=0,MarginV=42'"
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(MASTER),
        "-vf", f"scale=1280:720,{subtitle_filter}", "-c:v", "libx264", "-preset", "ultrafast",
        "-crf", "24", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart", str(PROXY),
    ])


def build_comparison() -> None:
    # Two captioned 640x360 panels; audio is taken from the motion candidate.
    left = (
        f"[0:v]trim=start={START}:end={END},setpts=PTS-STARTPTS,scale=640:360,"
        "drawbox=x=0:y=0:w=640:h=42:color=black@0.72:t=fill,"
        "drawtext=text='v1.2d  STATIC':x=20:y=10:fontsize=24:fontcolor=white[l]"
    )
    right = (
        f"[1:v]trim=start={START}:end={END},setpts=PTS-STARTPTS,scale=640:360,"
        "drawbox=x=0:y=0:w=640:h=42:color=black@0.72:t=fill,"
        "drawtext=text='v1.2e  MOTION ACCENT':x=20:y=10:fontsize=24:fontcolor=white[r]"
    )
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(SOURCE), "-i", str(MASTER),
        "-filter_complex", f"{left};{right};[l][r]hstack=inputs=2[v];"
        f"[1:a]atrim=start={START}:end={END},asetpts=PTS-STARTPTS[a]",
        "-map", "[v]", "-map", "[a]", "-t", f"{DURATION:.3f}", "-r", "25",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(COMPARE),
    ])


def main() -> None:
    if not SOURCE.exists() or not SRT.exists():
        raise FileNotFoundError("v1.2d master and canonical SRT are required")
    make_overlay()
    build_master()
    build_proxy()
    build_comparison()


if __name__ == "__main__":
    main()
