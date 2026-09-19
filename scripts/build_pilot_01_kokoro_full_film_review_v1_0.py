#!/usr/bin/env python3
"""Build the single Pilot 01 Kokoro full-film review candidate.

This builder is intentionally review-only. It stream-copies the pinned v1.2g
picture and replaces its scratch audio with the validated 597.760-second Kokoro
narration conform. It never grants upload or release authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

PICTURE_SHA256 = "3d1643246c066f377e841edc0f8653fec3c1bd9910d15151fb53732039259d27"
NARRATION_SHA256 = "bceafeb4e4864fe0973788d10b5d81829b56ac3b41d17093f9240ddca8e4c186"
EXPECTED_SECONDS = 597.760
EXPECTED_FRAMES = 14944


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, text=True, capture_output=True)


def probe(path: Path, count_frames: bool = False) -> dict:
    cmd = ["ffprobe", "-v", "error"]
    if count_frames:
        cmd += ["-count_frames"]
    cmd += ["-show_streams", "-show_format", "-of", "json", str(path)]
    return json.loads(run(cmd).stdout)


def video_payload_md5(path: Path) -> str:
    out = run(["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:v:0", "-c", "copy", "-f", "md5", "-"]).stdout
    return out.strip().split("=", 1)[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--picture", required=True, type=Path)
    ap.add_argument("--narration", required=True, type=Path)
    ap.add_argument("--conform-result", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--result", required=True, type=Path)
    args = ap.parse_args()

    failures: list[str] = []
    if sha256(args.picture) != PICTURE_SHA256:
        failures.append("picture_sha256_mismatch")
    if sha256(args.narration) != NARRATION_SHA256:
        failures.append("narration_sha256_mismatch")

    conform = json.loads(args.conform_result.read_text())
    if conform.get("verdict") != "PASS_NARRATION_CONFORM_ONLY":
        failures.append("conform_verdict_not_authoritative")
    for key in ("publishable", "release_authorized"):
        if conform.get(key) is not False:
            failures.append(f"upstream_{key}_must_be_false")
    if failures:
        raise SystemExit("BLOCKED: " + ", ".join(failures))
    if args.output.exists():
        raise SystemExit(f"BLOCKED: output exists: {args.output}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Fixed two-pass measurement values came from the exact pinned narration.
    loudnorm = (
        "loudnorm=I=-16:LRA=11:TP=-1.5:"
        "measured_I=-27.22:measured_LRA=4.50:measured_TP=-3.33:"
        "measured_thresh=-37.64:offset=1.15:linear=true:print_format=summary"
    )
    run([
        "ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-y",
        "-i", str(args.picture), "-i", str(args.narration),
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
        "-af", loudnorm, "-ar", "48000", "-ac", "1", "-c:a", "aac", "-b:a", "192k",
        "-t", "597.760", "-shortest",
        "-map_metadata", "-1", "-map_chapters", "-1",
        "-metadata", "title=Pilot 01 — Kokoro Full-Film Review — DO NOT UPLOAD",
        "-metadata", "comment=REVIEW ONLY; HUMAN NATURALNESS AND PRONUNCIATION OPEN; NOT RELEASE AUTHORIZED",
        "-metadata", "artist=Business 01 internal review",
        "-movflags", "+faststart", str(args.output),
    ])

    media = probe(args.output, count_frames=True)
    streams = media["streams"]
    video = next(s for s in streams if s["codec_type"] == "video")
    audio = next(s for s in streams if s["codec_type"] == "audio")
    container_duration = float(media["format"]["duration"])
    video_duration = float(video["duration"])
    frames = int(video.get("nb_read_frames", 0))
    if abs(video_duration - EXPECTED_SECONDS) > 0.001:
        failures.append(f"video_duration={video_duration}")
    # AAC is packetized in 1024-sample access units. The mux must not exceed one
    # such unit beyond the exact picture duration, and the decoded tail is silence.
    if container_duration - EXPECTED_SECONDS > (1024 / 48000) + 0.001:
        failures.append(f"container_duration={container_duration}")
    if frames != EXPECTED_FRAMES:
        failures.append(f"frames={frames}")
    if (video.get("width"), video.get("height"), video.get("r_frame_rate")) != (1920, 1080, "25/1"):
        failures.append("video_format_mismatch")
    if audio.get("sample_rate") != "48000" or audio.get("channels") != 1:
        failures.append("audio_format_mismatch")
    if video_payload_md5(args.output) != video_payload_md5(args.picture):
        failures.append("video_payload_changed")

    # A full decode is part of the retained success verdict.
    run(["ffmpeg", "-v", "error", "-i", str(args.output), "-f", "null", "-"])
    result = {
        "schema": "pilot-01-kokoro-full-film-review-v1.0",
        "verdict": "PASS_FULL_FILM_REVIEW_ONLY" if not failures else "BLOCKED",
        "failures": failures,
        "picture_sha256": sha256(args.picture),
        "narration_sha256": sha256(args.narration),
        "output_sha256": sha256(args.output),
        "video_payload_md5": video_payload_md5(args.output),
        "video_duration_seconds": video_duration,
        "container_duration_seconds": container_duration,
        "aac_packet_padding_limit_seconds": 1024 / 48000,
        "frames": frames,
        "width": video.get("width"),
        "height": video.get("height"),
        "frame_rate": video.get("r_frame_rate"),
        "audio_codec": audio.get("codec_name"),
        "audio_sample_rate": int(audio.get("sample_rate", 0)),
        "audio_channels": audio.get("channels"),
        "normalization": {
            "target_i_lufs": -16.0,
            "target_true_peak_dbtp": -1.5,
            "measured_input_i_lufs": -27.22,
            "measured_input_true_peak_dbtp": -3.33,
            "measured_input_lra_lu": 4.50,
        },
        "human_naturalness_review": "OPEN",
        "pronunciation_review": "OPEN",
        "review_only": True,
        "final_master_present": False,
        "upload_authorized": False,
        "publishable": False,
        "release_authorized": False,
    }
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
