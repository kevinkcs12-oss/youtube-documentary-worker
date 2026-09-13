#!/usr/bin/env python3
"""Fail-closed validator for Pilot 01 executive release decision v1.1."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path


DEFAULT_MANIFEST = Path("Pilot_01_Executive_Release_Decision_Manifest_v1.1.json")
SCALAR_KEYS = ("motion", "voice", "opening_sound", "mix", "metadata", "publication")
CHAPTER_KEYS = (
    "C02_02m22", "C03_03m30", "C04_04m45",
    "C05_06m04", "C06_07m19", "C07_08m35",
)
SOUND_ATTESTATION = "I reviewed the opening and six chapter-transition A/B surfaces."
RELEASE_ATTESTATION = (
    "I authorize the selected Pilot 01 configuration and the stated publication scope."
)


def validate_data(data: dict[str, object], release: bool) -> dict[str, object]:
    errors: list[str] = []
    if data.get("schema") != "pilot-01-executive-release-decision-v1.1":
        errors.append("schema mismatch")

    decisions = data.get("decisions")
    allowed = data.get("allowed_values")
    if not isinstance(decisions, dict) or not isinstance(allowed, dict):
        errors.append("decisions or allowed_values missing")
        decisions = decisions if isinstance(decisions, dict) else {}
        allowed = allowed if isinstance(allowed, dict) else {}

    for key in SCALAR_KEYS:
        value = decisions.get(key)
        valid = allowed.get(key, [])
        if value != "PENDING" and value not in valid:
            errors.append(f"{key}: invalid value {value!r}")

    chapter = decisions.get("chapter_sound")
    if not isinstance(chapter, dict):
        errors.append("chapter_sound missing or not an object")
        chapter = {}
    missing_chapters = [key for key in CHAPTER_KEYS if key not in chapter]
    extra_chapters = sorted(set(chapter) - set(CHAPTER_KEYS))
    if missing_chapters:
        errors.append("missing chapter_sound keys: " + ", ".join(missing_chapters))
    if extra_chapters:
        errors.append("unexpected chapter_sound keys: " + ", ".join(extra_chapters))
    for key in CHAPTER_KEYS:
        value = chapter.get(key)
        if value != "PENDING" and value not in allowed.get("chapter_sound", []):
            errors.append(f"chapter_sound.{key}: invalid value {value!r}")

    unresolved = [key for key in SCALAR_KEYS[:-1] if decisions.get(key) == "PENDING"]
    unresolved.extend(f"chapter_sound.{key}" for key in CHAPTER_KEYS if chapter.get(key) == "PENDING")
    publication = decisions.get("publication")
    closed = publication == "HOLD"

    if release:
        if unresolved:
            errors.append("unresolved decisions: " + ", ".join(unresolved))
        if decisions.get("voice") == "REJECT_ALL":
            errors.append("voice REJECT_ALL cannot enter release conform")
        if closed:
            errors.append("publication remains HOLD")
        if publication not in {"AUTHORIZE_UNLISTED_UPLOAD", "AUTHORIZE_PUBLICATION"}:
            errors.append("publication scope is not affirmative")
        if data.get("sound_review_attestation") != SOUND_ATTESTATION:
            errors.append("exact sound-review attestation missing")
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
        "sound_choices": {
            "opening": decisions.get("opening_sound"),
            "chapters": {key: chapter.get(key) for key in CHAPTER_KEYS},
        },
        "authorization_id_present": bool(data.get("authorization_id")),
        "release_authorized": False,
    }


def validate(path: Path, release: bool) -> dict[str, object]:
    return validate_data(json.loads(path.read_text(encoding="utf-8")), release)


def self_test(base: dict[str, object]) -> dict[str, object]:
    results: list[dict[str, object]] = []

    def record(name: str, data: dict[str, object], release: bool, expected: str) -> None:
        actual = validate_data(data, release)
        results.append({"name": name, "expected": expected, "actual": actual["status"], "pass": actual["status"] == expected})

    record("closed-default", copy.deepcopy(base), False, "PASS_CLOSED_GATES")
    record("closed-release-block", copy.deepcopy(base), True, "BLOCKED")

    complete = copy.deepcopy(base)
    decisions = complete["decisions"]
    decisions.update({
        "motion": "RETAIN_V1_2G", "voice": "CANDIDATE_A", "opening_sound": "DRY",
        "mix": "NO_MUSIC", "metadata": "NATIVE_AB_TEST_A_B_C",
        "publication": "AUTHORIZE_UNLISTED_UPLOAD",
    })
    decisions["chapter_sound"] = {key: "DRY" for key in CHAPTER_KEYS}
    complete["sound_review_attestation"] = SOUND_ATTESTATION
    complete["authorization_id"] = "SELF-TEST-NOT-AUTHORIZATION"
    complete["authorization_attestation"] = RELEASE_ATTESTATION
    record("complete-release-shape", complete, True, "DECISION_MANIFEST_COMPLETE_FOR_DOWNSTREAM_PREFLIGHT")

    rejected_voice = copy.deepcopy(complete)
    rejected_voice["decisions"]["voice"] = "REJECT_ALL"
    record("reject-all-voice-block", rejected_voice, True, "BLOCKED")

    missing_chapter = copy.deepcopy(complete)
    del missing_chapter["decisions"]["chapter_sound"]["C07_08m35"]
    record("missing-chapter-block", missing_chapter, True, "BLOCKED")

    extra_chapter = copy.deepcopy(complete)
    extra_chapter["decisions"]["chapter_sound"]["C99"] = "DRY"
    record("extra-chapter-block", extra_chapter, True, "BLOCKED")

    missing_sound_attestation = copy.deepcopy(complete)
    missing_sound_attestation["sound_review_attestation"] = None
    record("missing-sound-attestation-block", missing_sound_attestation, True, "BLOCKED")

    return {"status": "PASS" if all(item["pass"] for item in results) else "FAIL", "tests": results}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", nargs="?", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--release", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    result = self_test(data) if args.self_test else validate_data(data, args.release)
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.self_test:
        return 0 if result["status"] == "PASS" else 3
    return 0 if result["status"].startswith(("PASS", "DECISION")) else 2


if __name__ == "__main__":
    sys.exit(main())
