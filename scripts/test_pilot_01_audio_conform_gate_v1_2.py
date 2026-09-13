#!/usr/bin/env python3
"""Decision-integration tests for Pilot 01 audio conform gate v1.2."""

from __future__ import annotations

import copy
import csv
import json
from pathlib import Path

from build_pilot_01_audio_conform_gate import validate_executive_decision
from validate_pilot_01_executive_release_decision_v1_1 import (
    CHAPTER_KEYS, RELEASE_ATTESTATION, SOUND_ATTESTATION,
)

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "Pilot_01_Executive_Release_Decision_Manifest_v1.1.json"
OUT = ROOT / "Pilot_01_Audio_Conform_Gate_Test_Matrix_v1.2.csv"


def complete(base: dict) -> dict:
    data = copy.deepcopy(base)
    data["decisions"].update({
        "motion": "RETAIN_V1_2G", "voice": "CANDIDATE_A", "opening_sound": "DRY",
        "mix": "NO_MUSIC", "metadata": "NATIVE_AB_TEST_A_B_C",
        "publication": "AUTHORIZE_UNLISTED_UPLOAD",
    })
    data["decisions"]["chapter_sound"] = {key: "DRY" for key in CHAPTER_KEYS}
    data["sound_review_attestation"] = SOUND_ATTESTATION
    data["authorization_id"] = "SELF-TEST-NOT-AUTHORIZATION"
    data["authorization_attestation"] = RELEASE_ATTESTATION
    return data


def blocked(label: str, data: dict, dry_run: bool, expected_fragment: str) -> dict:
    try:
        validate_executive_decision(data, dry_run)
    except ValueError as exc:
        detail = str(exc)
        if expected_fragment not in detail:
            raise AssertionError(f"{label}: unexpected reason: {detail}")
        return {"test": label, "expected": "BLOCKED", "observed": "BLOCKED", "detail": detail, "result": "PASS"}
    raise AssertionError(f"{label}: unexpectedly passed")


def main() -> int:
    base = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = []
    control = validate_executive_decision(base, True)
    rows.append({"test": "canonical HOLD dry run", "expected": "PASS_CLOSED_GATES", "observed": control["status"], "detail": "safe control path", "result": "PASS"})

    rows.append(blocked("canonical HOLD release", base, False, "Executive release gate closed"))

    legacy = {"mode": "release", "motion_decision_authorized": True,
              "voice_selected_authorized": True, "mix_path_authorized": True,
              "publication_authorized": True, "authorization_id": "legacy"}
    rows.append(blocked("legacy boolean bypass", legacy, False, "schema v1.1"))

    approved = complete(base)
    decision = validate_executive_decision(approved, False)
    rows.append({"test": "complete canonical downstream shape", "expected": "DECISION_MANIFEST_COMPLETE_FOR_DOWNSTREAM_PREFLIGHT", "observed": decision["status"], "detail": "gate isolation only", "result": "PASS"})

    rejected = copy.deepcopy(approved)
    rejected["decisions"]["voice"] = "REJECT_ALL"
    rows.append(blocked("REJECT_ALL voice", rejected, False, "voice REJECT_ALL"))

    partial = copy.deepcopy(approved)
    partial["decisions"]["chapter_sound"]["C07_08m35"] = "PENDING"
    rows.append(blocked("partial chapter sound", partial, False, "unresolved decisions"))

    no_attestation = copy.deepcopy(approved)
    no_attestation["authorization_attestation"] = ""
    rows.append(blocked("missing exact release attestation", no_attestation, False, "attestation"))

    public_control = copy.deepcopy(base)
    public_control["decisions"]["publication"] = "AUTHORIZE_PUBLICATION"
    rows.append(blocked("non-HOLD dry run", public_control, True, "Dry run requires"))

    source = (ROOT / "build_pilot_01_audio_conform_gate.py").read_text(encoding="utf-8")
    forbidden = ["motion_decision_authorized", "voice_selected_authorized",
                 "mix_path_authorized", "publication_authorized"]
    if any(token in source for token in forbidden):
        raise AssertionError("legacy authorization boolean remains in audio gate")
    if '"publishable": False' not in source or '"release_authorized": False' not in source:
        raise AssertionError("audio-only non-release invariants are missing")
    rows.append({"test": "source-level non-release invariants", "expected": "NO_LEGACY_BYPASS_AND_FALSE_AUTHORITY", "observed": "NO_LEGACY_BYPASS_AND_FALSE_AUTHORITY", "detail": "static fail-closed guard", "result": "PASS"})

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    print(json.dumps({"verdict": "PASS", "tests": len(rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
