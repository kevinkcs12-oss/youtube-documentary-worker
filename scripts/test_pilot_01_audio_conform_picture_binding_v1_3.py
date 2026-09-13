#!/usr/bin/env python3
"""Adversarial picture-decision binding tests for Pilot 01 audio gate v1.3."""

from __future__ import annotations

import copy
import csv
import json
from pathlib import Path

from build_pilot_01_audio_conform_gate import (
    AUDIO_CONFORM_SCHEMA, PICTURE_BY_MOTION, resolve_picture_authority,
    validate_picture_sha,
)
from test_pilot_01_audio_conform_gate_v1_2 import complete

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "Pilot_01_Executive_Release_Decision_Manifest_v1.1.json"
OUT = ROOT / "Pilot_01_Audio_Conform_Picture_Binding_Test_Matrix_v1.3.csv"


def expect_block(label: str, fn, fragment: str) -> dict:
    try:
        fn()
    except ValueError as exc:
        detail = str(exc)
        if fragment not in detail:
            raise AssertionError(f"{label}: unexpected reason: {detail}")
        return {"test": label, "expected": "BLOCKED", "observed": "BLOCKED", "detail": detail, "result": "PASS"}
    raise AssertionError(f"{label}: unexpectedly passed")


def passed(label: str, observed: str, detail: str) -> dict:
    return {"test": label, "expected": observed, "observed": observed, "detail": detail, "result": "PASS"}


def main() -> int:
    base = json.loads(MANIFEST.read_text(encoding="utf-8"))
    approved = complete(base)
    rows = []

    motion, authority = resolve_picture_authority(base, True)
    rows.append(passed("closed HOLD resolves declared review candidate", "RETAIN_V1_2G", authority["variant"]))
    validate_picture_sha(PICTURE_BY_MOTION[motion]["sha256"], authority)
    rows.append(passed("HOLD candidate exact bytes", "PASS", authority["sha256"]))

    motion, authority = resolve_picture_authority(approved, False)
    rows.append(passed("explicit retain resolves v1.2g", "RETAIN_V1_2G", authority["variant"]))

    reverted = copy.deepcopy(approved)
    reverted["decisions"]["motion"] = "REVERT_V1_2F"
    motion, revert_authority = resolve_picture_authority(reverted, False)
    rows.append(passed("explicit revert resolves v1.2f", "REVERT_V1_2F", revert_authority["variant"]))
    validate_picture_sha(PICTURE_BY_MOTION[motion]["sha256"], revert_authority)

    rows.append(expect_block(
        "retain decision with v1.2f bytes",
        lambda: validate_picture_sha(PICTURE_BY_MOTION["REVERT_V1_2F"]["sha256"], authority),
        "contradicts selected v1.2g",
    ))
    rows.append(expect_block(
        "revert decision with v1.2g bytes",
        lambda: validate_picture_sha(PICTURE_BY_MOTION["RETAIN_V1_2G"]["sha256"], revert_authority),
        "contradicts selected v1.2f",
    ))

    unknown = copy.deepcopy(base)
    unknown["picture_candidate"] = "unpinned-candidate"
    rows.append(expect_block(
        "unknown HOLD picture candidate", lambda: resolve_picture_authority(unknown, True), "not a pinned"
    ))

    source = (ROOT / "build_pilot_01_audio_conform_gate.py").read_text(encoding="utf-8")
    if AUDIO_CONFORM_SCHEMA not in source or '"decision_manifest_sha256"' not in source:
        raise AssertionError("downstream schema or decision-manifest binding missing")
    rows.append(passed("downstream schema and manifest binding", "PASS", AUDIO_CONFORM_SCHEMA))

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    print(json.dumps({"verdict": "PASS", "tests": len(rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
