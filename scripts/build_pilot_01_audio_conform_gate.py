#!/usr/bin/env python3
"""Build a frame-locked narration-only conform after explicit gate checks.

This script intentionally does not select a voice, authorize publication, or mix
music. It accepts only a provenance-bound full-timeline narration file and refuses
release mode unless both the narration conform and decision gates are satisfied.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from validate_pilot_01_executive_release_decision_v1_1 import validate_data

TARGET_SECONDS = 597.760
TARGET_FRAMES = 14944
NARRATION_CONFORM_SCHEMA = "pilot-01-final-narration-timeline-conform-v1.0"
EXECUTIVE_DECISION_SCHEMA = "pilot-01-executive-release-decision-v1.1"
AUDIO_CONFORM_SCHEMA = "pilot-01-audio-conform-validation-v1.3"
PICTURE_BY_MOTION = {
    "RETAIN_V1_2G": {
        "variant": "v1.2g-progressive-focus",
        "sha256": "3d1643246c066f377e841edc0f8653fec3c1bd9910d15151fb53732039259d27",
    },
    "REVERT_V1_2F": {
        "variant": "v1.2f-pacing-trim",
        "sha256": "038b9eb7a638b07be70fe61d8c037c1332d41c5eb40d63862ea7d31717685c7a",
    },
}


def run(cmd: list[str], capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, text=True, capture_output=capture)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def probe(path: Path, count_frames: bool = False) -> dict:
    cmd = ["ffprobe", "-v", "error"]
    if count_frames:
        cmd += ["-count_frames"]
    cmd += ["-show_entries", "format=duration", "-show_entries",
            "stream=index,codec_type,width,height,r_frame_rate,sample_rate,channels,nb_read_frames",
            "-of", "json", str(path)]
    return json.loads(run(cmd, capture=True).stdout)


def audio_stats(path: Path) -> dict:
    p = subprocess.run([
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
        "-af", "loudnorm=I=-16:LRA=11:TP=-1.2:print_format=json", "-f", "null", "-"
    ], text=True, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr[-2000:])
    start, end = p.stderr.rfind("{"), p.stderr.rfind("}")
    if start < 0 or end < start:
        raise RuntimeError("loudnorm did not return JSON")
    return json.loads(p.stderr[start:end + 1])


def validate_narration_provenance(narration: Path, conform_result_path: Path,
                                  dry_run: bool) -> dict:
    """Bind narration bytes to the upstream fail-closed conform verdict."""
    result = json.loads(conform_result_path.read_text(encoding="utf-8"))
    if result.get("schema") != NARRATION_CONFORM_SCHEMA:
        raise ValueError("Narration conform schema mismatch")
    if result.get("publishable") is not False or result.get("release_authorized") is not False:
        raise ValueError("Upstream narration conform must not claim publication or release authority")
    if result.get("time_stretch_applied") is not False or result.get("music_present") is not False:
        raise ValueError("Upstream narration conform used forbidden time-stretch or music")
    if result.get("samples") != 28692480 or result.get("takes_placed") != 91:
        raise ValueError("Narration conform sample or take count mismatch")
    if (result.get("sample_rate_hz"), result.get("bit_depth"), result.get("channels")) != (48000, 24, 1):
        raise ValueError("Narration conform format contract mismatch")
    if result.get("output_sha256") != sha256(narration):
        raise ValueError("Narration bytes do not match upstream conform SHA-256")

    lineage_fields = ["cue_sheet_sha256", "validator_sha256", "intake_validation_sha256",
                      "delivery_manifest_sha256", "placements_sha256"]
    missing_lineage = [name for name in lineage_fields
                       if not isinstance(result.get(name), str)
                       or len(result[name]) != 64
                       or any(c not in "0123456789abcdef" for c in result[name])]
    if missing_lineage:
        raise ValueError("Narration conform lineage is incomplete: " + ", ".join(missing_lineage))

    verdict = result.get("verdict")
    fixture_mode = result.get("fixture_mode")
    if dry_run:
        if verdict not in {"PASS_FIXTURE_CONFORM_ONLY", "PASS_NARRATION_CONFORM_ONLY"}:
            raise ValueError("Dry-run narration lacks an accepted conform verdict")
        if verdict == "PASS_FIXTURE_CONFORM_ONLY" and fixture_mode is not True:
            raise ValueError("Fixture verdict is missing fixture_mode=true")
    else:
        if verdict != "PASS_NARRATION_CONFORM_ONLY" or fixture_mode is not False:
            raise ValueError("Release mode requires a non-fixture PASS_NARRATION_CONFORM_ONLY result")
    return result


def validate_executive_decision(decision: dict, dry_run: bool) -> dict:
    """Use the canonical v1.1 validator; never translate legacy booleans."""
    if decision.get("schema") != EXECUTIVE_DECISION_SCHEMA:
        raise ValueError("Canonical executive decision schema v1.1 is required")
    result = validate_data(decision, release=not dry_run)
    if result.get("release_authorized") is not False:
        raise ValueError("Executive validator improperly claims release authority")
    if dry_run:
        if result.get("status") != "PASS_CLOSED_GATES" or result.get("publication_scope") != "HOLD":
            raise ValueError("Dry run requires canonical HOLD / PASS_CLOSED_GATES")
    elif result.get("status") != "DECISION_MANIFEST_COMPLETE_FOR_DOWNSTREAM_PREFLIGHT":
        detail = "; ".join(result.get("errors", [])) or str(result.get("status"))
        raise ValueError("Executive release gate closed: " + detail)
    return result


def resolve_picture_authority(decision: dict, dry_run: bool) -> tuple[str, dict]:
    """Resolve exact picture bytes from the explicit motion decision.

    The closed-gate dry-run manifest has motion=PENDING, so it may use only its
    declared review candidate. Authorization-bound mode always requires an
    explicit RETAIN/REVERT decision through the executive validator.
    """
    motion = decision.get("decisions", {}).get("motion")
    if dry_run and motion == "PENDING":
        candidate = decision.get("picture_candidate")
        matches = [(key, value) for key, value in PICTURE_BY_MOTION.items()
                   if value["variant"] == candidate]
        if len(matches) != 1:
            raise ValueError("Dry-run picture_candidate is not a pinned picture authority")
        return matches[0]
    if motion not in PICTURE_BY_MOTION:
        raise ValueError("Explicit RETAIN_V1_2G or REVERT_V1_2F motion decision required")
    return motion, PICTURE_BY_MOTION[motion]


def validate_picture_sha(actual_sha: str, authority: dict) -> None:
    if actual_sha != authority["sha256"]:
        raise ValueError(
            f"Picture identity contradicts selected {authority['variant']} authority"
        )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--picture", type=Path, required=True)
    ap.add_argument("--narration", type=Path, required=True)
    ap.add_argument("--narration-conform-result", type=Path, required=True)
    ap.add_argument("--decision-manifest", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    try:
        narration_conform = validate_narration_provenance(
            args.narration, args.narration_conform_result, args.dry_run
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Narration provenance gate closed: {exc}")

    decision = json.loads(args.decision_manifest.read_text(encoding="utf-8"))
    try:
        decision_validation = validate_executive_decision(decision, args.dry_run)
        motion_decision, picture_authority = resolve_picture_authority(decision, args.dry_run)
    except ValueError as exc:
        raise SystemExit(f"Executive decision gate closed: {exc}")

    picture_sha = sha256(args.picture)
    try:
        validate_picture_sha(picture_sha, picture_authority)
    except ValueError as exc:
        raise SystemExit(f"Picture decision gate closed: {exc}")
    nprobe = probe(args.narration)
    nduration = float(nprobe["format"]["duration"])
    if abs(nduration - TARGET_SECONDS) > 0.021:
        raise SystemExit(f"Narration timeline mismatch: {nduration:.3f}s")

    first_pass = audio_stats(args.narration)
    loudnorm = (
        "loudnorm=I=-16:LRA=11:TP=-1.2:linear=true:"
        f"measured_I={first_pass['input_i']}:"
        f"measured_LRA={first_pass['input_lra']}:"
        f"measured_TP={first_pass['input_tp']}:"
        f"measured_thresh={first_pass['input_thresh']}:"
        f"offset={first_pass['target_offset']}"
    )
    metadata = ("PILOT 01 DRY-RUN CONTROL — DO NOT PUBLISH" if args.dry_run
                else "PILOT 01 AUTHORIZATION-BOUND AUDIO CONFORM — NOT FINAL MASTER")
    run([
        "ffmpeg", "-y", "-v", "error", "-i", str(args.picture), "-i", str(args.narration),
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
        "-af", f"{loudnorm},apad=whole_dur=597.760,atrim=0:597.760",
        "-ar", "48000", "-ac", "1", "-c:a", "aac", "-b:a", "192k",
        "-metadata", f"title={metadata}", "-metadata", f"comment={metadata}",
        "-movflags", "+faststart", "-t", "597.760", str(args.output)
    ])

    run(["ffmpeg", "-v", "error", "-i", str(args.output), "-f", "null", "-"])
    outprobe = probe(args.output, count_frames=True)
    video = next(s for s in outprobe["streams"] if s["codec_type"] == "video")
    audio = next(s for s in outprobe["streams"] if s["codec_type"] == "audio")
    duration = float(outprobe["format"]["duration"])
    result = {
        "schema": AUDIO_CONFORM_SCHEMA,
        "mode": "dry_run_control" if args.dry_run else "authorization_bound_audio_conform",
        "publishable": False,
        "release_authorized": False,
        "audio_conform_only": True,
        "executive_decision_status": decision_validation["status"],
        "publication_scope": decision_validation["publication_scope"],
        "motion_decision": motion_decision,
        "picture_variant": picture_authority["variant"],
        "duration_seconds": duration,
        "video_frames": int(video["nb_read_frames"]),
        "geometry": f"{video['width']}x{video['height']}",
        "fps": video["r_frame_rate"],
        "audio_sample_rate": int(audio["sample_rate"]),
        "audio_channels": int(audio["channels"]),
        "audio_measurement": audio_stats(args.output),
        "first_pass_measurement": first_pass,
        "picture_sha256": picture_sha,
        "decision_manifest_sha256": sha256(args.decision_manifest),
        "narration_sha256": sha256(args.narration),
        "narration_conform_result_sha256": sha256(args.narration_conform_result),
        "narration_conform_verdict": narration_conform["verdict"],
        "narration_fixture_mode": narration_conform["fixture_mode"],
        "output_sha256": sha256(args.output),
    }
    failures = []
    if abs(duration - TARGET_SECONDS) > 0.001: failures.append("duration")
    if result["video_frames"] != TARGET_FRAMES: failures.append("frames")
    if result["geometry"] != "1920x1080": failures.append("geometry")
    if result["fps"] != "25/1": failures.append("fps")
    if result["audio_sample_rate"] != 48000 or result["audio_channels"] != 1: failures.append("audio_format")
    # When measuring an already-rendered file, loudnorm's input_* values are
    # the observed file metrics; output_* describes a hypothetical new pass.
    measured_i = float(result["audio_measurement"]["input_i"])
    measured_tp = float(result["audio_measurement"]["input_tp"])
    if not (-16.6 <= measured_i <= -15.4): failures.append("integrated_loudness")
    if measured_tp > -1.0: failures.append("true_peak")
    result["status"] = "PASS" if not failures else "FAIL"
    result["failures"] = failures
    result_path = args.output.with_suffix(".validation.json")
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
