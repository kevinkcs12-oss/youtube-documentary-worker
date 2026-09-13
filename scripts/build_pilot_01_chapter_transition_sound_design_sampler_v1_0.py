#!/usr/bin/env python3
"""Build a deterministic, non-musical chapter-transition sound-design sampler."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MASTER = ROOT / "Pilot_01_Animatic_Scratch_Voice_00m00_09m57.760_v1.2g_progressive_focus.mp4"
STEM = ROOT / "Pilot_01_Chapter_Transition_Procedural_Sound_Design_Stem_v1.0.wav"
REEL = ROOT / "Pilot_01_Chapter_Transition_Dry_vs_Designed_Sampler_v1.0.mp4"
MANIFEST = ROOT / "Pilot_01_Chapter_Transition_Sound_Design_Manifest_v1.0.json"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FPS = 25
RUNTIME = 597.760
WINDOW = 12.0
SLATE = 1.0
TRANSITIONS = [
    (142.0, "WHAT THE EVIDENCE CAN SHOW"),
    (210.0, "WHY FAMILIARITY FEELS EASIER"),
    (285.0, "INTERFACES AND IDENTITIES"),
    (364.0, "ARCHITECTURE AT SCALE"),
    (439.0, "THE FEEDBACK LOOP"),
    (515.0, "THE EXCEPTIONS THAT MATTER"),
]


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_stem() -> None:
    filters: list[str] = []
    labels: list[str] = []

    # Retain the already-tested 00:00-01:04 opening bed from fixed seeds.
    filters.extend([
        "anoisesrc=color=pink:amplitude=0.010:duration=64:sample_rate=48000:seed=1101,"
        "highpass=f=90,lowpass=f=5200,volume=5.12,pan=stereo|c0=c0|c1=c0[opening_amb]",
        "anoisesrc=color=white:amplitude=0.004:duration=64:sample_rate=48000:seed=2202,"
        "highpass=f=5500,lowpass=f=12500,volume=2.56,pan=stereo|c0=0.85*c0|c1=c0[opening_air]",
    ])
    labels.extend(["[opening_amb]", "[opening_air]"])
    for i, at in enumerate([7.0, 16.0, 30.0, 46.0, 54.0]):
        delay = int(at * 1000)
        label = f"opening_tr_{i}"
        filters.append(
            f"anoisesrc=color=white:amplitude=0.030:duration=0.38:sample_rate=48000:seed={3300+i},"
            f"highpass=f=500,lowpass=f=4200,afade=t=out:st=0:d=0.38,volume=2.40,"
            f"pan=stereo|c0=c0|c1=0.78*c0,adelay={delay}|{delay}[{label}]"
        )
        labels.append(f"[{label}]")

    # Each chapter handoff gets a three-second low bed and a short broadband accent.
    for i, (at, _) in enumerate(TRANSITIONS):
        bridge_start = at - 1.5
        bridge_delay = int(bridge_start * 1000)
        hit_delay = int(at * 1000)
        bridge = f"bridge_{i}"
        hit = f"hit_{i}"
        filters.append(
            f"anoisesrc=color=pink:amplitude=0.012:duration=3:sample_rate=48000:seed={5100+i},"
            "highpass=f=120,lowpass=f=2600,afade=t=in:st=0:d=1.2,afade=t=out:st=1.8:d=1.2,"
            f"volume=2.20,pan=stereo|c0=c0|c1=0.92*c0,adelay={bridge_delay}|{bridge_delay}[{bridge}]"
        )
        filters.append(
            f"anoisesrc=color=white:amplitude=0.026:duration=0.46:sample_rate=48000:seed={6100+i},"
            "highpass=f=420,lowpass=f=5200,afade=t=out:st=0:d=0.46,volume=2.15,"
            f"pan=stereo|c0=c0|c1=0.80*c0,adelay={hit_delay}|{hit_delay}[{hit}]"
        )
        labels.extend([f"[{bridge}]", f"[{hit}]"])

    filters.append(
        "anullsrc=r=48000:cl=stereo:d=597.760[silence]"
    )
    labels.append("[silence]")
    filters.append(
        "".join(labels)
        + f"amix=inputs={len(labels)}:normalize=0,atrim=duration={RUNTIME}[out]"
    )
    run([
        "ffmpeg", "-nostdin", "-y", "-v", "error", "-filter_complex", ";".join(filters),
        "-map", "[out]", "-c:a", "pcm_s24le", "-ar", "48000", "-ac", "2", str(STEM),
    ])


def build_segment(master: Path, stem: Path, output: Path, at: float, title: str) -> None:
    start = at - 5.0
    safe_title = title.replace("'", "")
    run([
        "ffmpeg", "-nostdin", "-y", "-v", "error",
        "-ss", f"{start:.3f}", "-t", f"{WINDOW:.3f}", "-i", str(master),
        "-ss", f"{start:.3f}", "-t", f"{WINDOW:.3f}", "-i", str(stem),
        "-filter_complex",
        f"color=c=0x0B1017:s=1280x720:r={FPS}:d={SLATE},"
        f"drawtext=fontfile={FONT}:text='A — DRY / {safe_title}':fontcolor=white:fontsize=38:"
        "x=(w-text_w)/2:y=(h-text_h)/2[sa];"
        f"anullsrc=r=48000:cl=stereo:d={SLATE}[saa];"
        f"[0:v]trim=duration={WINDOW},setpts=PTS-STARTPTS,scale=1280:720[va];"
        f"[0:a]atrim=duration={WINDOW},asetpts=PTS-STARTPTS,pan=stereo|c0=c0|c1=c0[aa];"
        f"color=c=0x0B1017:s=1280x720:r={FPS}:d={SLATE},"
        f"drawtext=fontfile={FONT}:text='B — PROCEDURAL / {safe_title}':fontcolor=white:fontsize=38:"
        "x=(w-text_w)/2:y=(h-text_h)/2[sb];"
        f"anullsrc=r=48000:cl=stereo:d={SLATE}[sba];"
        f"[0:v]trim=duration={WINDOW},setpts=PTS-STARTPTS,scale=1280:720[vb];"
        f"[0:a]atrim=duration={WINDOW},asetpts=PTS-STARTPTS,pan=stereo|c0=c0|c1=c0[n];"
        f"[1:a]atrim=duration={WINDOW},asetpts=PTS-STARTPTS[s];"
        "[n][s]amix=inputs=2:normalize=0,alimiter=limit=0.891[ab];"
        "[sa][saa][va][aa][sb][sba][vb][ab]concat=n=4:v=1:a=1[v][a]",
        "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "21",
        "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-ac", "2", "-t", "26.000", str(output),
    ])


def build_reel() -> None:
    with tempfile.TemporaryDirectory(prefix="pilot01_chapter_sound_") as tmp:
        temp = Path(tmp)
        pieces: list[Path] = []
        for i, (at, title) in enumerate(TRANSITIONS):
            piece = temp / f"segment_{i:02d}.mp4"
            build_segment(MASTER, STEM, piece, at, title)
            pieces.append(piece)
        concat = temp / "concat.txt"
        concat.write_text("".join(f"file '{p.as_posix()}'\n" for p in pieces), encoding="utf-8")
        run([
            "ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(concat),
            "-vf", f"fps={FPS}", "-af", "atrim=duration=156,asetpts=PTS-STARTPTS",
            "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-r", str(FPS),
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-t", "156.000",
            "-movflags", "+faststart", str(REEL),
        ])


def main() -> None:
    if not MASTER.is_file():
        raise SystemExit(f"missing master: {MASTER}")
    build_stem()
    build_reel()
    MANIFEST.write_text(json.dumps({
        "schema": "pilot-01-chapter-transition-sound-design-v1.0",
        "scope": "six chapter handoffs plus previously tested opening bed",
        "master_runtime_seconds": RUNTIME,
        "transition_seconds": [t for t, _ in TRANSITIONS],
        "sampler_windows": [
            {"start": t - 5.0, "end": t + 7.0, "title": title} for t, title in TRANSITIONS
        ],
        "sampler_expected_seconds": 156.0,
        "sampler_expected_frames": 3900,
        "music_present": False,
        "third_party_audio_present": False,
        "illustrative_only": True,
        "factual_evidence": False,
        "source_master_sha256": digest(MASTER),
        "stem_sha256": digest(STEM),
        "sampler_sha256": digest(REEL),
        "editorial_status": "REVERSIBLE_HUMAN_REVIEW_REQUIRED",
        "release_authorized": False,
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
