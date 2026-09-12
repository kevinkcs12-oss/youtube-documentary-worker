#!/usr/bin/env python3
"""Fail-closed validator for Pilot 01 executive release decisions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


DEFAULT_MANIFEST = Path("Pilot_01_Executive_Release_Decision_Manifest_v1.0.json")
REQUIRED_KEYS = ("motion", "voice", "mix", "metadata", "publication")
RELEASE_ATTESTATION = (
    "I authorize the selected Pilot 01 configuration and the stated publication scope."
)


def validate(path: Path, release: bool) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    decisions = data.get("decisions")
    allowed = data.get("allowed_values")

    if data.get("schema") != "pilot-01-executive-release-decision-v1.0":
        errors.append("schema mismatch")
    if not isinstance(decisions, dict) or not isinstance(allowed, dict):
        errors.append("decisions or allowed_values missing")
        decisions = decisions if isinstance(decisions, dict) else {}
        allowed = allowed if isinstance(allowed, dict) else {}

    for key in REQUIRED_KEYS:
        value = decisions.get(key)
        valid = allowed.get(key, [])
        if value != "PENDING" and value not in valid:
            errors.append(f"{key}: invalid value {value!r}")

    publication = decisions.get("publication")
    closed = publication == "HOLD"
    unresolved = [k for k in REQUIRED_KEYS[:-1] if decisions.get(k) == "PENDING"]

    if release:
        if unresolved:
            errors.append("unresolved decisions: " + ", ".join(unresolved))
        if closed:
            errors.append("publication remains HOLD")
        if publication not in {"AUTHORIZE_UNLISTED_UPLOAD", "AUTHORIZE_PUBLICATION"}:
            errors.append("publication scope is not affirmative")
        if not data.get("authorization_id"):
            errors.append("authorization_id missing")
        if data.get("authorization_attestation") != RELEASE_ATTESTATION:
            errors.append("exact authorization attestation missing")

    if errors:
        status = "BLOCKED"
    elif release:
        status = "DECISION_MANIFEST_COMPLETE_FOR_DOWNSTREAM_PREFLIGHT"
    else:
        status = "PASS_CLOSED_GATES" if closed else "PASS_CONFIGURATION_REVIEW"

    return {
        "status": status,
        "release_mode": release,
        "errors": errors,
        "unresolved_decisions": unresolved,
        "publication_scope": publication,
        "authorization_id_present": bool(data.get("authorization_id")),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", nargs="?", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--release", action="store_true")
    args = parser.parse_args()
    result = validate(args.manifest, args.release)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"].startswith("PASS") else (0 if result["status"].startswith("DECISION") else 2)


if __name__ == "__main__":
    sys.exit(main())
