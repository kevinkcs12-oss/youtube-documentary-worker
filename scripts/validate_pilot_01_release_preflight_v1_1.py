#!/usr/bin/env python3
"""Media-verified, fail-closed chained release preflight for Pilot 01 v1.1."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

from validate_pilot_01_release_preflight_v1_0 import sha256, validate_chain as validate_v1_0


SCHEMA = "pilot-01-chained-release-preflight-v1.1"
EXPECTED_LABEL = "PILOT 01 AUTHORIZATION-BOUND AUDIO CONFORM — NOT FINAL MASTER"


def probe_media(path: Path) -> dict[str, object]:
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-count_frames",
        "-show_entries", "format=duration:format_tags=title,comment",
        "-show_entries", "stream=codec_type,width,height,r_frame_rate,sample_rate,channels,nb_read_frames",
        "-of", "json", str(path),
    ], check=True, capture_output=True, text=True)
    payload = json.loads(probe.stdout)
    streams = payload.get("streams", [])
    videos = [stream for stream in streams if stream.get("codec_type") == "video"]
    audios = [stream for stream in streams if stream.get("codec_type") == "audio"]
    video = videos[0] if len(videos) == 1 else {}
    audio = audios[0] if len(audios) == 1 else {}
    tags = payload.get("format", {}).get("tags", {})
    return {
        "video_stream_count": len(videos),
        "audio_stream_count": len(audios),
        "duration_seconds": payload.get("format", {}).get("duration"),
        "video_frames": video.get("nb_read_frames"),
        "geometry": f"{video.get('width')}x{video.get('height')}",
        "fps": video.get("r_frame_rate"),
        "audio_sample_rate": audio.get("sample_rate"),
        "audio_channels": audio.get("channels"),
        "title": tags.get("title"),
        "comment": tags.get("comment"),
    }


def measure_loudness(path: Path) -> dict[str, object]:
    measurement = subprocess.run([
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
        "-af", "loudnorm=I=-16:LRA=11:TP=-1.2:print_format=json",
        "-f", "null", "-",
    ], capture_output=True, text=True)
    if measurement.returncode != 0:
        raise RuntimeError("loudness measurement failed")
    start, end = measurement.stderr.rfind("{"), measurement.stderr.rfind("}")
    if start < 0 or end < start:
        raise RuntimeError("loudness measurement returned no JSON")
    values = json.loads(measurement.stderr[start:end + 1])
    return {"integrated_lufs": values.get("input_i"), "true_peak_dbtp": values.get("input_tp")}


def decode_media(path: Path) -> bool:
    result = subprocess.run([
        "ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-",
    ], capture_output=True, text=True)
    return result.returncode == 0


def validate_chain(
    technical_baseline: dict[str, object],
    audio_validation: dict[str, object],
    decision_manifest: dict[str, object],
    audio_media_sha256: str,
    decision_manifest_sha256: str,
    media_facts: dict[str, object],
) -> dict[str, object]:
    prior = validate_v1_0(
        technical_baseline, audio_validation, decision_manifest,
        audio_media_sha256, decision_manifest_sha256,
    )
    failures = list(prior.get("failures", []))

    def numeric(name: str, expected: float, tolerance: float = 0.0) -> None:
        try:
            value = float(media_facts.get(name))
        except (TypeError, ValueError):
            value = math.nan
        if not math.isfinite(value) or abs(value - expected) > tolerance:
            failures.append(f"observed_{name}")

    if media_facts.get("decode_ok") is not True:
        failures.append("full_decode")
    if media_facts.get("video_stream_count") != 1:
        failures.append("video_stream_count")
    if media_facts.get("audio_stream_count") != 1:
        failures.append("audio_stream_count")
    numeric("duration_seconds", 597.760, 0.001)
    numeric("video_frames", 14944)
    if media_facts.get("geometry") != "1920x1080":
        failures.append("observed_geometry")
    if media_facts.get("fps") != "25/1":
        failures.append("observed_fps")
    numeric("audio_sample_rate", 48000)
    numeric("audio_channels", 1)
    if media_facts.get("title") != EXPECTED_LABEL or media_facts.get("comment") != EXPECTED_LABEL:
        failures.append("conform_identity_metadata")

    try:
        loudness = float(media_facts.get("integrated_lufs"))
        peak = float(media_facts.get("true_peak_dbtp"))
    except (TypeError, ValueError):
        loudness = peak = math.nan
    if not math.isfinite(loudness) or not (-16.6 <= loudness <= -15.4):
        failures.append("observed_integrated_loudness")
    if not math.isfinite(peak) or peak > -1.0:
        failures.append("observed_true_peak")

    declared_pairs = {
        "duration_seconds": 0.001,
        "video_frames": 0.0,
        "geometry": None,
        "fps": None,
        "audio_sample_rate": 0.0,
        "audio_channels": 0.0,
    }
    for key, tolerance in declared_pairs.items():
        observed = media_facts.get(key)
        declared = audio_validation.get(key)
        if tolerance is None:
            matches = observed == declared
        else:
            try:
                left, right = float(observed), float(declared)
                matches = math.isfinite(left) and math.isfinite(right) and abs(left - right) <= tolerance
            except (TypeError, ValueError):
                matches = False
        if not matches:
            failures.append(f"declared_observed_{key}")

    failures = list(dict.fromkeys(failures))
    passed = not failures
    return {
        **prior,
        "schema": SCHEMA,
        "verdict": "PASS_MEDIA_VERIFIED_PREFLIGHT_ONLY" if passed else "BLOCKED",
        "failures": failures,
        "media_observed_directly": True,
        "full_decode_passed": media_facts.get("decode_ok") is True,
        "observed_integrated_lufs": loudness if math.isfinite(loudness) else None,
        "observed_true_peak_dbtp": peak if math.isfinite(peak) else None,
        "final_master_present": False,
        "upload_authorized": False,
        "publishable": False,
        "release_authorized": False,
        "preflight_only": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--technical-baseline", type=Path, required=True)
    parser.add_argument("--audio-conform", type=Path, required=True)
    parser.add_argument("--audio-validation", type=Path, required=True)
    parser.add_argument("--decision-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        baseline = json.loads(args.technical_baseline.read_text(encoding="utf-8"))
        audio = json.loads(args.audio_validation.read_text(encoding="utf-8"))
        decision = json.loads(args.decision_manifest.read_text(encoding="utf-8"))
        facts = probe_media(args.audio_conform)
        facts.update(measure_loudness(args.audio_conform))
        facts["decode_ok"] = decode_media(args.audio_conform)
        result = validate_chain(
            baseline, audio, decision, sha256(args.audio_conform),
            sha256(args.decision_manifest), facts,
        )
    except (OSError, ValueError, TypeError, RuntimeError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        result = {
            "schema": SCHEMA,
            "verdict": "BLOCKED",
            "failures": [f"input_or_media_error:{type(exc).__name__}"],
            "media_observed_directly": False,
            "final_master_present": False,
            "upload_authorized": False,
            "publishable": False,
            "release_authorized": False,
            "preflight_only": True,
        }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["verdict"] == "PASS_MEDIA_VERIFIED_PREFLIGHT_ONLY" else 2


if __name__ == "__main__":
    sys.exit(main())
