#!/usr/bin/env python3
"""Adversarial unit tests for the Pilot 01 audio-conform provenance gate v1.1."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from build_pilot_01_audio_conform_gate import validate_narration_provenance


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def payload(narration: Path, verdict: str, fixture: bool) -> dict:
    return {
        "schema": "pilot-01-final-narration-timeline-conform-v1.0",
        "verdict": verdict,
        "fixture_mode": fixture,
        "publishable": False,
        "release_authorized": False,
        "time_stretch_applied": False,
        "music_present": False,
        "sample_rate_hz": 48000,
        "bit_depth": 24,
        "channels": 1,
        "samples": 28692480,
        "takes_placed": 91,
        "output_sha256": digest(narration),
        "cue_sheet_sha256": "1" * 64,
        "validator_sha256": "2" * 64,
        "intake_validation_sha256": "3" * 64,
        "delivery_manifest_sha256": "4" * 64,
        "placements_sha256": "5" * 64,
    }


def expect_blocked(label: str, narration: Path, result: Path, dry_run: bool) -> dict:
    try:
        validate_narration_provenance(narration, result, dry_run)
    except ValueError as exc:
        return {"test": label, "expected": "BLOCKED", "observed": "BLOCKED", "detail": str(exc), "result": "PASS"}
    raise AssertionError(f"{label}: provenance gate unexpectedly passed")


def main() -> int:
    matrix = []
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        narration = root / "narration.wav"
        narration.write_bytes(b"synthetic fixture bytes only")
        result = root / "result.json"

        result.write_text(json.dumps(payload(narration, "PASS_FIXTURE_CONFORM_ONLY", True)), encoding="utf-8")
        validate_narration_provenance(narration, result, True)
        matrix.append({"test": "fixture in dry-run", "expected": "PASS", "observed": "PASS", "detail": "review-only fixture accepted", "result": "PASS"})
        matrix.append(expect_blocked("fixture in release mode", narration, result, False))

        result.write_text(json.dumps(payload(narration, "PASS_NARRATION_CONFORM_ONLY", False)), encoding="utf-8")
        validate_narration_provenance(narration, result, False)
        matrix.append({"test": "production conform in release mode", "expected": "PASS", "observed": "PASS", "detail": "non-fixture provenance accepted", "result": "PASS"})

        bad = payload(narration, "PASS_NARRATION_CONFORM_ONLY", False)
        bad["output_sha256"] = "0" * 64
        result.write_text(json.dumps(bad), encoding="utf-8")
        matrix.append(expect_blocked("narration hash substitution", narration, result, False))

        bad = payload(narration, "PASS_NARRATION_CONFORM_ONLY", False)
        bad["publishable"] = True
        result.write_text(json.dumps(bad), encoding="utf-8")
        matrix.append(expect_blocked("upstream publishable claim", narration, result, False))

        bad = payload(narration, "PASS_NARRATION_CONFORM_ONLY", False)
        bad["samples"] -= 1
        result.write_text(json.dumps(bad), encoding="utf-8")
        matrix.append(expect_blocked("sample-count drift", narration, result, False))

        bad = payload(narration, "PASS_NARRATION_CONFORM_ONLY", False)
        bad["time_stretch_applied"] = True
        result.write_text(json.dumps(bad), encoding="utf-8")
        matrix.append(expect_blocked("time-stretch flag", narration, result, False))

        bad = payload(narration, "PASS_NARRATION_CONFORM_ONLY", False)
        bad["schema"] = "unknown"
        result.write_text(json.dumps(bad), encoding="utf-8")
        matrix.append(expect_blocked("schema substitution", narration, result, False))

        bad = payload(narration, "PASS_NARRATION_CONFORM_ONLY", False)
        del bad["intake_validation_sha256"]
        result.write_text(json.dumps(bad), encoding="utf-8")
        matrix.append(expect_blocked("missing intake lineage", narration, result, False))

    output = Path(__file__).resolve().parent / "Pilot_01_Audio_Conform_Provenance_Gate_Test_Matrix_v1.1.json"
    output.write_text(json.dumps({"verdict": "PASS", "tests": len(matrix), "matrix": matrix}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": "PASS", "tests": len(matrix)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
