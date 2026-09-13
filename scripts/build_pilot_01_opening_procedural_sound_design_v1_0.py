#!/usr/bin/env python3
"""Build a rights-safe, non-musical procedural sound-design test for 00:00-01:04."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MASTER = ROOT / "Pilot_01_Animatic_Scratch_Voice_00m00_09m57.760_v1.2g_progressive_focus.mp4"
SFX = ROOT / "Pilot_01_Opening_Procedural_Sound_Design_Stem_v1.0.wav"
CANDIDATE = ROOT / "Pilot_01_Opening_Procedural_Sound_Design_Candidate_00m00_01m04_v1.0.mp4"
COMPARISON = ROOT / "Pilot_01_Opening_Dry_vs_Procedural_Sound_Design_Comparison_v1.0.mp4"
MANIFEST = ROOT / "Pilot_01_Opening_Procedural_Sound_Design_Manifest_v1.0.json"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
DURATION = 64.0
FPS = 25


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    if not MASTER.is_file():
        raise SystemExit(f"missing master: {MASTER}")

    # Fixed seeds make every noise source reproducible. No samples or third-party media are used.
    transitions = [7.0, 16.0, 30.0, 46.0, 54.0]
    filters = [
        f"anoisesrc=color=pink:amplitude=0.010:duration={DURATION}:sample_rate=48000:seed=1101,"
        "highpass=f=90,lowpass=f=5200,volume=5.12,pan=stereo|c0=c0|c1=c0[amb]",
        f"anoisesrc=color=white:amplitude=0.004:duration={DURATION}:sample_rate=48000:seed=2202,"
        "highpass=f=5500,lowpass=f=12500,volume=2.56,pan=stereo|c0=0.85*c0|c1=c0[air]",
    ]
    accent_labels = []
    for i, at in enumerate(transitions):
        delay = int(at * 1000)
        label = f"tr{i}"
        filters.append(
            f"anoisesrc=color=white:amplitude=0.030:duration=0.38:sample_rate=48000:seed={3300+i},"
            f"highpass=f=500,lowpass=f=4200,afade=t=out:st=0:d=0.38,volume=2.40,"
            f"pan=stereo|c0=c0|c1=0.78*c0,adelay={delay}|{delay}[{label}]"
        )
        accent_labels.append(f"[{label}]")
    filters.append("[amb][air]" + "".join(accent_labels) + f"amix=inputs={2+len(accent_labels)}:normalize=0,atrim=duration={DURATION}[out]")
    run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-filter_complex", ";".join(filters),
         "-map", "[out]", "-c:a", "pcm_s24le", "-ar", "48000", "-ac", "2", str(SFX)])

    run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(MASTER), "-i", str(SFX),
         "-filter_complex",
         f"[0:v]trim=duration={DURATION},setpts=PTS-STARTPTS,"
         f"drawtext=fontfile={FONT}:text='ORIGINAL PROCEDURAL SOUND DESIGN — ILLUSTRATIVE ONLY':"
         "fontcolor=white@0.72:fontsize=24:box=1:boxcolor=black@0.45:boxborderw=10:x=48:y=48:"
         "enable='between(t,0,4)'[v];"
         f"[0:a]atrim=duration={DURATION},asetpts=PTS-STARTPTS,pan=stereo|c0=c0|c1=c0[n];"
         f"[1:a]atrim=duration={DURATION},asetpts=PTS-STARTPTS[s];"
         "[n][s]amix=inputs=2:weights='1 1':normalize=0,alimiter=limit=0.891[a]",
         "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
         "-t", str(DURATION), "-movflags", "+faststart", str(CANDIDATE)])

    slate = 2.0
    run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(MASTER), "-i", str(CANDIDATE),
         "-filter_complex",
         f"color=c=0x0B1017:s=1280x720:r={FPS}:d={slate},"
         f"drawtext=fontfile={FONT}:text='A — DRY SCRATCH NARRATION':fontcolor=white:fontsize=50:x=(w-text_w)/2:y=(h-text_h)/2[sa];"
         f"anullsrc=r=48000:cl=stereo:d={slate}[saa];"
         f"[0:v]trim=duration={DURATION},setpts=PTS-STARTPTS,scale=1280:720,"
         f"drawtext=fontfile={FONT}:text='A — DRY':fontcolor=white@0.75:fontsize=24:box=1:boxcolor=black@0.45:boxborderw=8:x=38:y=38[va];"
         f"[0:a]atrim=duration={DURATION},asetpts=PTS-STARTPTS,pan=stereo|c0=c0|c1=c0[aa];"
         f"color=c=0x0B1017:s=1280x720:r={FPS}:d={slate},"
         f"drawtext=fontfile={FONT}:text='B — ORIGINAL PROCEDURAL SOUND DESIGN':fontcolor=white:fontsize=45:x=(w-text_w)/2:y=(h-text_h)/2[sb];"
         f"anullsrc=r=48000:cl=stereo:d={slate}[sba];"
         f"[1:v]trim=duration={DURATION},setpts=PTS-STARTPTS,scale=1280:720,"
         f"drawtext=fontfile={FONT}:text='B — SOUND DESIGN':fontcolor=white@0.75:fontsize=24:box=1:boxcolor=black@0.45:boxborderw=8:x=38:y=38[vb];"
         f"[1:a]atrim=duration={DURATION},asetpts=PTS-STARTPTS[ab];"
         "[sa][saa][va][aa][sb][sba][vb][ab]concat=n=4:v=1:a=1[v][a]",
         "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "21",
         "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
         "-movflags", "+faststart", str(COMPARISON)])

    MANIFEST.write_text(json.dumps({
        "schema": "pilot-01-opening-procedural-sound-design-v1.0",
        "scope": "00:00-01:04 reversible review candidate",
        "sound_class": "original deterministic procedural ambience and transition texture",
        "music_present": False,
        "third_party_audio_present": False,
        "factual_evidence": False,
        "illustrative_only": True,
        "transition_seconds": transitions,
        "expected_candidate_seconds": DURATION,
        "expected_candidate_frames": int(DURATION * FPS),
        "source_master_sha256": digest(MASTER),
        "stem_sha256": digest(SFX),
        "candidate_sha256": digest(CANDIDATE),
        "comparison_sha256": digest(COMPARISON),
        "editorial_status": "REVERSIBLE_HUMAN_REVIEW_REQUIRED",
        "release_authorized": False,
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
