#!/usr/bin/env python3
"""Deterministic, fail-closed final-narration timeline conformer for Pilot 01.

This tool never time-stretches audio and never grants release authorization. It
accepts only a delivery that first passes the canonical intake validator, places
each take at the frozen cue-sheet sample boundary, pads unused cue time with
digital silence, and emits an exact 597.760-second PCM24 mono/48 kHz WAV.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import wave
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

RATE = 48000
WIDTH = 3
TARGET_SECONDS = Decimal("597.760")
TARGET_SAMPLES = int(TARGET_SECONDS * RATE)
EXPECTED_TAKES = 91
EXPECTED_CUE_SHA256 = "226747fb55ac45941997230d3e35f331e40c94f248385e68a1e3ebd22b74cccf"
EXPECTED_VALIDATOR_SHA256 = "62193b4e16a4453c766d07a70a028105bbeca6c7f24904c41a764c6b353fb7ec"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def samples(timestamp: str) -> int:
    hh, mm, ss = timestamp.split(":")
    total = Decimal(hh) * 3600 + Decimal(mm) * 60 + Decimal(ss)
    return int((total * RATE).to_integral_value(rounding=ROUND_HALF_UP))


def load_cues(path: Path) -> list[dict[str, str]]:
    if sha256(path) != EXPECTED_CUE_SHA256:
        raise ValueError("canonical cue-sheet SHA-256 mismatch")
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    expected = [f"T{i:03d}" for i in range(1, EXPECTED_TAKES + 1)]
    if len(rows) != EXPECTED_TAKES or [r["take_id"] for r in rows] != expected:
        raise ValueError("cue sheet must contain ordered T001-T091")
    previous_end = 0
    for row in rows:
        start, end = samples(row["start"]), samples(row["end"])
        if start < previous_end or end <= start or end > TARGET_SAMPLES:
            raise ValueError(f'{row["take_id"]}: invalid or overlapping cue window')
        previous_end = end
    return rows


def decode_raw(path: Path) -> bytes:
    return subprocess.check_output([
        "ffmpeg", "-nostdin", "-v", "error", "-i", str(path),
        "-f", "s24le", "-ac", "1", "-ar", str(RATE), "-",
    ])


def run_intake(validator: Path, delivery: Path, manifest: Path) -> tuple[dict, Path]:
    if sha256(validator) != EXPECTED_VALIDATOR_SHA256:
        raise ValueError("canonical intake-validator SHA-256 mismatch")
    result_path = validator.parent / "Pilot_01_Final_Voice_Delivery_Validation_v1.0.json"
    subprocess.run([
        sys.executable, str(validator), "--delivery-dir", str(delivery),
        "--manifest", str(manifest),
    ], cwd=validator.parent, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("verdict") != "PASS_INTAKE_ONLY":
        raise ValueError("delivery did not pass canonical intake validation")
    if result.get("takes_validated") != EXPECTED_TAKES or result.get("failures"):
        raise ValueError("intake validation is incomplete")
    if result.get("release_authorized") is not False:
        raise ValueError("intake result improperly claims release authorization")
    return result, result_path


def conform(delivery: Path, manifest: Path, cue_sheet: Path, validator: Path,
            output: Path, placements: Path, result_path: Path, fixture_mode: bool) -> dict:
    rows = load_cues(cue_sheet)
    intake, intake_path = run_intake(validator, delivery, manifest)
    intake_sha = sha256(intake_path)
    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    by_id = {x["take_id"]: x for x in manifest_data["takes"]}
    placement_rows = []
    zero_chunk = b"\0" * (RATE * WIDTH)

    output.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(WIDTH)
        wav.setframerate(RATE)
        cursor = 0
        for row in rows:
            take_id = row["take_id"]
            start, end = samples(row["start"]), samples(row["end"])
            if start < cursor:
                raise ValueError(f"{take_id}: cue starts before timeline cursor")
            gap = start - cursor
            while gap:
                n = min(gap, RATE)
                wav.writeframesraw(zero_chunk[: n * WIDTH])
                gap -= n
            take_path = delivery / f"{take_id}.wav"
            raw = decode_raw(take_path)
            if len(raw) % WIDTH:
                raise ValueError(f"{take_id}: decoded byte count is not sample-aligned")
            take_samples = len(raw) // WIDTH
            capacity = end - start
            if take_samples > capacity:
                raise ValueError(f"{take_id}: take exceeds cue window by {take_samples-capacity} samples")
            if sha256(take_path) != by_id[take_id]["sha256"]:
                raise ValueError(f"{take_id}: hash changed after intake validation")
            wav.writeframesraw(raw)
            pad = capacity - take_samples
            while pad:
                n = min(pad, RATE)
                wav.writeframesraw(zero_chunk[: n * WIDTH])
                pad -= n
            cursor = end
            placement_rows.append({
                "take_id": take_id, "start_sample": start, "end_sample": end,
                "window_samples": capacity, "take_samples": take_samples,
                "silence_pad_samples": capacity - take_samples,
                "take_sha256": by_id[take_id]["sha256"], "time_stretch": "NONE",
            })
        tail = TARGET_SAMPLES - cursor
        while tail:
            n = min(tail, RATE)
            wav.writeframesraw(zero_chunk[: n * WIDTH])
            tail -= n

    with wave.open(str(output), "rb") as wav:
        if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getnframes()) != (1, 3, RATE, TARGET_SAMPLES):
            raise ValueError("output WAV format or exact sample count mismatch")

    with placements.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(placement_rows[0]))
        writer.writeheader()
        writer.writerows(placement_rows)

    result = {
        "schema": "pilot-01-final-narration-timeline-conform-v1.0",
        "verdict": "PASS_FIXTURE_CONFORM_ONLY" if fixture_mode else "PASS_NARRATION_CONFORM_ONLY",
        "fixture_mode": fixture_mode,
        "publishable": False,
        "release_authorized": False,
        "time_stretch_applied": False,
        "music_present": False,
        "sample_rate_hz": RATE,
        "bit_depth": 24,
        "channels": 1,
        "duration_seconds": float(TARGET_SECONDS),
        "samples": TARGET_SAMPLES,
        "takes_placed": len(placement_rows),
        "cue_sheet_sha256": sha256(cue_sheet),
        "validator_sha256": sha256(validator),
        "intake_validation_sha256": intake_sha,
        "delivery_manifest_sha256": sha256(manifest),
        "output_sha256": sha256(output),
        "placements_sha256": sha256(placements),
        "intake_warnings": intake.get("warnings", []),
    }
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--delivery-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--cue-sheet", type=Path, default=root / "Pilot_01_Final_Voice_Cue_Sheet_v1.0.csv")
    parser.add_argument("--validator", type=Path, default=root / "validate_pilot_01_final_voice_delivery.py")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--placements", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--fixture-mode", action="store_true")
    args = parser.parse_args()
    try:
        result = conform(args.delivery_dir, args.manifest, args.cue_sheet, args.validator,
                         args.output, args.placements, args.result, args.fixture_mode)
        print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:
        blocked = {
            "schema": "pilot-01-final-narration-timeline-conform-v1.0",
            "verdict": "BLOCKED", "publishable": False, "release_authorized": False,
            "error": str(exc),
        }
        args.result.write_text(json.dumps(blocked, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(blocked, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
