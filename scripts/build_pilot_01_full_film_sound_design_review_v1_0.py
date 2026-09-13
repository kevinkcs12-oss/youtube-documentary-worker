#!/usr/bin/env python3
"""Build the deterministic full-film procedural sound-design review candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PICTURE = ROOT / "Pilot_01_v1.2g_Continuous_Caption_Review_720p.mp4"
STEM = ROOT / "Pilot_01_Chapter_Transition_Procedural_Sound_Design_Stem_v1.0.wav"
DEFAULT_OUTPUT = ROOT / "Pilot_01_Full_Film_Procedural_Sound_Design_Review_DO_NOT_PUBLISH_v1.0.mp4"
MANIFEST = ROOT / "Pilot_01_Full_Film_Procedural_Sound_Design_Review_Manifest_v1.0.json"
RUNTIME = 597.760
FRAMES = 14944


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build(output: Path) -> None:
    if not PICTURE.is_file() or not STEM.is_file():
        raise SystemExit("missing canonical picture proxy or procedural stem")
    subprocess.run([
        "ffmpeg", "-nostdin", "-y", "-v", "error",
        "-fflags", "+bitexact",
        "-i", str(PICTURE),
        "-i", str(STEM),
        "-filter_complex",
        # Equal-power mono-to-stereo upmix prevents a +3 dB loudness bias.
        "[0:a]pan=stereo|c0=0.70710678*c0|c1=0.70710678*c0,asetpts=PTS-STARTPTS[n];"
        f"[1:a]atrim=duration={RUNTIME:.3f},asetpts=PTS-STARTPTS[s];"
        "[n][s]amix=inputs=2:duration=first:normalize=0,"
        "alimiter=limit=0.891:level=disabled[a]",
        "-map", "0:v:0", "-map", "[a]",
        "-map_metadata", "-1",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-metadata", "title=Pilot 01 full-film procedural sound-design review",
        "-metadata", "comment=REVIEW ONLY - SCRATCH VOICE - DO NOT PUBLISH",
        "-metadata:s:a:0", "title=Scratch narration plus illustrative procedural sound",
        "-t", f"{RUNTIME:.3f}",
        "-movflags", "+faststart",
        str(output),
    ], check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--no-manifest", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    build(output)
    if not args.no_manifest:
        MANIFEST.write_text(json.dumps({
            "schema": "pilot-01-full-film-procedural-sound-design-review-v1.0",
            "editorial_status": "REVERSIBLE_HUMAN_REVIEW_REQUIRED",
            "release_authorized": False,
            "do_not_publish": True,
            "runtime_seconds": RUNTIME,
            "expected_frames": FRAMES,
            "picture_timing_authority": "v1.2f",
            "picture_review_candidate": "v1.2g progressive-focus",
            "captions_burned_in": True,
            "voice_status": "SCRATCH_ONLY",
            "music_present": False,
            "procedural_sound_classification": "ILLUSTRATIVE_NOT_EVIDENCE",
            "sound_decisions_included": {
                "opening": "PROCEDURAL_V1",
                "chapter_transitions": [
                    "C02_02m22", "C03_03m30", "C04_04m45",
                    "C05_06m04", "C06_07m19", "C07_08m35"
                ]
            },
            "source_picture_sha256": digest(PICTURE),
            "source_stem_sha256": digest(STEM),
            "output_sha256": digest(output),
        }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
