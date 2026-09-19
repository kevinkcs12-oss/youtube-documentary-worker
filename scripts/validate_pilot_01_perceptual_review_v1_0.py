#!/usr/bin/env python3
"""Validate the human perceptual review without granting release authority."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

EXPECTED_FILM_SHA256 = "8076d795c25f2fef0f377fd4abacaa72ad3a22b6f7dddb0cedfb47c7b413c580"
EXPECTED_ATTESTATION = "I REVIEWED THE FULL 09:57.760 FILM AT NORMAL SPEED"
DECISIONS = {"PASS_PERCEPTUAL_REVIEW", "TARGETED_REPAIR", "REJECT_VOICE"}
SEVERITIES = {"NONE", "MINOR", "MAJOR", "CRITICAL"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blocked(errors: list[str], scorecard: Path, decision: Path) -> dict:
    return {
        "schema": "pilot-01-perceptual-review-validation-v1.0",
        "verdict": "BLOCKED_INCOMPLETE_REVIEW",
        "errors": errors,
        "scorecard_sha256": sha256(scorecard),
        "decision_sha256": sha256(decision),
        "targeted_repair_take_ids": [],
        "human_perceptual_gate_passed": False,
        "final_master_authorized": False,
        "upload_authorized": False,
        "publishable": False,
        "release_authorized": False,
    }


def validate(scorecard: Path, decision_path: Path) -> dict:
    errors: list[str] = []
    with scorecard.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    expected_ids = [f"T{i:03d}" for i in range(1, 92)]
    ids = [r.get("take_id", "") for r in rows]
    if ids != expected_ids:
        errors.append("scorecard must contain ordered T001-T091 exactly once")

    defects: list[dict[str, str]] = []
    chapters_with_major = set()
    for row in rows:
        take = row.get("take_id", "UNKNOWN")
        verdict = row.get("human_verdict", "").strip().upper()
        severity = row.get("severity", "").strip().upper()
        notes = row.get("notes", "").strip()
        if verdict not in {"PASS", "DEFECT"}:
            errors.append(f"{take}: human_verdict must be PASS or DEFECT")
            continue
        if severity not in SEVERITIES:
            errors.append(f"{take}: invalid severity")
        if verdict == "PASS" and severity != "NONE":
            errors.append(f"{take}: PASS requires severity NONE")
        if verdict == "DEFECT":
            if severity == "NONE":
                errors.append(f"{take}: DEFECT cannot use severity NONE")
            if not notes:
                errors.append(f"{take}: DEFECT requires notes")
            defects.append({"take_id": take, "chapter": row.get("chapter", ""), "severity": severity, "issue_type": row.get("issue_type", ""), "notes": notes})
            if severity in {"MAJOR", "CRITICAL"}:
                chapters_with_major.add(row.get("chapter", ""))
        if row.get("repair_authorized", "").strip().upper() != "NO":
            errors.append(f"{take}: repair_authorized must remain NO in review validation")

    if decision.get("film_sha256") != EXPECTED_FILM_SHA256:
        errors.append("decision is not bound to the canonical full-film SHA-256")
    if decision.get("attestation") != EXPECTED_ATTESTATION:
        errors.append("exact full-film attestation is missing")
    if decision.get("continuous_watch_completed") is not True:
        errors.append("continuous_watch_completed must be true")
    if decision.get("normal_speed") is not True:
        errors.append("normal_speed must be true")
    if decision.get("hotspots_opened_after_first_pass") is not True:
        errors.append("hotspots must be opened only after the first pass")
    if not str(decision.get("reviewer_id", "")).strip():
        errors.append("reviewer_id is required")
    completed = str(decision.get("review_completed_at", ""))
    try:
        datetime.fromisoformat(completed.replace("Z", "+00:00"))
    except ValueError:
        errors.append("review_completed_at must be an ISO-8601 timestamp")
    overall = decision.get("overall_decision")
    if overall not in DECISIONS:
        errors.append("overall_decision is invalid")
    if overall == "PASS_PERCEPTUAL_REVIEW" and any(d["severity"] in {"MAJOR", "CRITICAL"} for d in defects):
        errors.append("PASS_PERCEPTUAL_REVIEW cannot coexist with MAJOR or CRITICAL defects")
    if overall == "TARGETED_REPAIR" and not defects:
        errors.append("TARGETED_REPAIR requires at least one named defect")
    if overall == "REJECT_VOICE":
        if decision.get("systemic_failure_confirmed") is not True:
            errors.append("REJECT_VOICE requires systemic_failure_confirmed=true")
        if len(chapters_with_major) < 2:
            errors.append("REJECT_VOICE requires MAJOR/CRITICAL defects in at least two chapters")

    if errors:
        return blocked(errors, scorecard, decision_path)
    verdict = {
        "PASS_PERCEPTUAL_REVIEW": "PASS_PERCEPTUAL_REVIEW_ONLY",
        "TARGETED_REPAIR": "TARGETED_REPAIR_REQUIRED",
        "REJECT_VOICE": "VOICE_REJECTED_BY_HUMAN_REVIEW",
    }[overall]
    return {
        "schema": "pilot-01-perceptual-review-validation-v1.0",
        "verdict": verdict,
        "errors": [],
        "film_sha256": EXPECTED_FILM_SHA256,
        "scorecard_sha256": sha256(scorecard),
        "decision_sha256": sha256(decision_path),
        "reviewer_id": decision["reviewer_id"],
        "review_completed_at": decision["review_completed_at"],
        "defect_count": len(defects),
        "defects": defects,
        "targeted_repair_take_ids": [d["take_id"] for d in defects] if overall == "TARGETED_REPAIR" else [],
        "human_perceptual_gate_passed": overall == "PASS_PERCEPTUAL_REVIEW",
        "final_master_authorized": False,
        "upload_authorized": False,
        "publishable": False,
        "release_authorized": False,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--scorecard", type=Path, required=True)
    p.add_argument("--decision", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = validate(args.scorecard, args.decision)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["verdict"])
    return 0 if not result["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
