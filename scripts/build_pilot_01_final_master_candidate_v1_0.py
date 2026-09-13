#!/usr/bin/env python3
"""Build a stream-preserving, non-publishable Pilot 01 master candidate."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

from validate_pilot_01_release_preflight_v1_0 import sha256
from validate_pilot_01_release_preflight_v1_1 import decode_media, measure_loudness, probe_media


PREFLIGHT_SCHEMA = "pilot-01-chained-release-preflight-v1.1"
SCHEMA = "pilot-01-final-master-candidate-validation-v1.0"
CANDIDATE_LABEL = "PILOT 01 FINAL MASTER CANDIDATE — DO NOT UPLOAD"


def validate_preflight(preflight: dict[str, object], input_sha256: str) -> list[str]:
    failures: list[str] = []
    if preflight.get("schema") != PREFLIGHT_SCHEMA:
        failures.append("preflight_schema")
    if preflight.get("verdict") != "PASS_MEDIA_VERIFIED_PREFLIGHT_ONLY":
        failures.append("preflight_verdict")
    if preflight.get("failures") != []:
        failures.append("preflight_failures")
    if preflight.get("media_observed_directly") is not True:
        failures.append("media_not_observed")
    if preflight.get("full_decode_passed") is not True:
        failures.append("preflight_decode")
    if preflight.get("preflight_only") is not True:
        failures.append("preflight_scope")
    if preflight.get("audio_conform_sha256") != input_sha256:
        failures.append("audio_conform_sha256")
    for key in ("final_master_present", "upload_authorized", "publishable", "release_authorized"):
        if preflight.get(key) is not False:
            failures.append(f"preflight_{key}")
    return failures


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, capture_output=True, text=True)


def stream_hashes(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, selector in (("video", "0:v:0"), ("audio", "0:a:0")):
        output = run([
            "ffmpeg", "-v", "error", "-i", str(path), "-map", selector,
            "-c", "copy", "-f", "streamhash", "-hash", "sha256", "-",
        ]).stdout.strip()
        marker = "SHA256="
        if marker not in output:
            raise RuntimeError(f"missing {key} stream hash")
        result[key] = output.rsplit(marker, 1)[1].strip().lower()
    return result


def remux_candidate(source: Path, output: Path) -> None:
    run([
        "ffmpeg", "-n", "-v", "error", "-i", str(source),
        "-map", "0:v:0", "-map", "0:a:0", "-c", "copy",
        "-map_metadata", "-1", "-map_chapters", "-1",
        "-metadata", f"title={CANDIDATE_LABEL}",
        "-metadata", f"comment={CANDIDATE_LABEL}",
        "-movflags", "+faststart", str(output),
    ])


def verify_candidate(source: Path, output: Path) -> tuple[list[str], dict[str, object]]:
    failures: list[str] = []
    before = stream_hashes(source)
    after = stream_hashes(output)
    if before != after:
        failures.append("stream_payload_changed")
    facts = probe_media(output)
    facts.update(measure_loudness(output))
    facts["decode_ok"] = decode_media(output)
    if facts["decode_ok"] is not True:
        failures.append("full_decode")
    if facts.get("video_stream_count") != 1 or facts.get("audio_stream_count") != 1:
        failures.append("stream_topology")
    try:
        duration = float(facts.get("duration_seconds"))
        loudness = float(facts.get("integrated_lufs"))
        peak = float(facts.get("true_peak_dbtp"))
    except (TypeError, ValueError):
        duration = loudness = peak = math.nan
    if not math.isfinite(duration) or abs(duration - 597.760) > 0.001:
        failures.append("duration")
    if facts.get("video_frames") not in {14944, "14944"}:
        failures.append("frames")
    if facts.get("geometry") != "1920x1080" or facts.get("fps") != "25/1":
        failures.append("picture_format")
    if facts.get("audio_sample_rate") not in {48000, "48000"} or facts.get("audio_channels") != 1:
        failures.append("audio_format")
    if not math.isfinite(loudness) or not (-16.6 <= loudness <= -15.4):
        failures.append("integrated_loudness")
    if not math.isfinite(peak) or peak > -1.0:
        failures.append("true_peak")
    if facts.get("title") != CANDIDATE_LABEL or facts.get("comment") != CANDIDATE_LABEL:
        failures.append("candidate_identity_metadata")
    return failures, {"input_stream_sha256": before, "output_stream_sha256": after, "observed": facts}


def blocked_result(failures: list[str]) -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "verdict": "BLOCKED",
        "failures": failures,
        "master_candidate_present": False,
        "final_master_present": False,
        "upload_authorized": False,
        "publishable": False,
        "release_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio-conform", type=Path, required=True)
    parser.add_argument("--preflight-validation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--validation-output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError("output already exists")
        preflight = json.loads(args.preflight_validation.read_text(encoding="utf-8"))
        source_sha = sha256(args.audio_conform)
        failures = validate_preflight(preflight, source_sha)
        if failures:
            result = blocked_result(failures)
        else:
            remux_candidate(args.audio_conform, args.output)
            failures, details = verify_candidate(args.audio_conform, args.output)
            if failures:
                result = blocked_result(failures)
                result["rejected_output_sha256"] = sha256(args.output)
            else:
                result = {
                    "schema": SCHEMA,
                    "verdict": "PASS_MASTER_CANDIDATE_ONLY",
                    "failures": [],
                    "input_audio_conform_sha256": source_sha,
                    "preflight_validation_sha256": sha256(args.preflight_validation),
                    "candidate_sha256": sha256(args.output),
                    **details,
                    "master_candidate_present": True,
                    "final_master_present": False,
                    "upload_authorized": False,
                    "publishable": False,
                    "release_authorized": False,
                }
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        result = blocked_result([f"input_or_remux_error:{type(exc).__name__}"])
    args.validation_output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["verdict"] == "PASS_MASTER_CANDIDATE_ONLY" else 2


if __name__ == "__main__":
    sys.exit(main())
