#!/usr/bin/env python3
"""Adversarial tests for Pilot 01 chained release preflight v1.0."""

from __future__ import annotations

import copy
import csv
import hashlib
import json
from pathlib import Path

from validate_pilot_01_executive_release_decision_v1_1 import (
    CHAPTER_KEYS, RELEASE_ATTESTATION, SOUND_ATTESTATION,
)
from validate_pilot_01_release_preflight_v1_0 import validate_chain


ROOT = Path(__file__).resolve().parent
MATRIX = ROOT / "Pilot_01_Chained_Release_Preflight_Test_Matrix_v1.0.csv"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fixtures() -> tuple[dict, dict, dict, str, str]:
    decision = json.loads((ROOT / "Pilot_01_Executive_Release_Decision_Manifest_v1.1.json").read_text())
    decision["decisions"].update({
        "motion": "RETAIN_V1_2G",
        "voice": "CANDIDATE_A",
        "opening_sound": "DRY",
        "mix": "NO_MUSIC",
        "metadata": "NATIVE_AB_TEST_A_B_C",
        "publication": "AUTHORIZE_UNLISTED_UPLOAD",
    })
    decision["decisions"]["chapter_sound"] = {key: "DRY" for key in CHAPTER_KEYS}
    decision["sound_review_attestation"] = SOUND_ATTESTATION
    decision["authorization_id"] = "SELF-TEST-NOT-AUTHORIZATION"
    decision["authorization_attestation"] = RELEASE_ATTESTATION
    decision_bytes = (json.dumps(decision, indent=2, ensure_ascii=False) + "\n").encode()
    decision_sha = digest(decision_bytes)
    media_sha = digest(b"synthetic-audio-conform-fixture")
    baseline = {
        "schema": "pilot-01-prepublication-validation-v1.0",
        "overall": "PASS_WITH_HUMAN_GATES",
        "technical_checks": {"passed": 32, "failed": 0},
        "human_gates": [
            "retain_or_revert_v1.2g_progressive_focus",
            "select_final_voice_after_blind_listening",
            "authorize_music_or_no-music_mix_and_external_publication",
        ],
    }
    audio = {
        "schema": "pilot-01-audio-conform-validation-v1.3",
        "mode": "authorization_bound_audio_conform",
        "status": "PASS",
        "publishable": False,
        "release_authorized": False,
        "audio_conform_only": True,
        "executive_decision_status": "DECISION_MANIFEST_COMPLETE_FOR_DOWNSTREAM_PREFLIGHT",
        "publication_scope": "AUTHORIZE_UNLISTED_UPLOAD",
        "motion_decision": "RETAIN_V1_2G",
        "picture_variant": "v1.2g-progressive-focus",
        "picture_sha256": "3d1643246c066f377e841edc0f8653fec3c1bd9910d15151fb53732039259d27",
        "decision_manifest_sha256": decision_sha,
        "narration_conform_verdict": "PASS_NARRATION_CONFORM_ONLY",
        "narration_fixture_mode": False,
        "narration_sha256": "4" * 64,
        "narration_conform_result_sha256": "5" * 64,
        "duration_seconds": 597.760,
        "video_frames": 14944,
        "geometry": "1920x1080",
        "fps": "25/1",
        "audio_sample_rate": 48000,
        "audio_channels": 1,
        "output_sha256": media_sha,
    }
    return baseline, audio, decision, media_sha, decision_sha


def main() -> int:
    base, audio, decision, media_sha, decision_sha = fixtures()
    cases: list[tuple[str, dict, dict, dict, str, str, str]] = []

    def add(name: str, expected: str, mutate=None, media=None, dsha=None) -> None:
        b, a, d = copy.deepcopy(base), copy.deepcopy(audio), copy.deepcopy(decision)
        if mutate:
            mutate(b, a, d)
        cases.append((name, b, a, d, media or media_sha, dsha or decision_sha, expected))

    add("valid_synthetic_chain", "PASS_CHAINED_PREFLIGHT_ONLY")
    add("hold_manifest_blocks", "BLOCKED", lambda b, a, d: d["decisions"].update(publication="HOLD"))
    add("wrong_audio_schema_blocks", "BLOCKED", lambda b, a, d: a.update(schema="v1.2"))
    add("dry_run_mode_blocks", "BLOCKED", lambda b, a, d: a.update(mode="dry_run_control"))
    add("fixture_narration_blocks", "BLOCKED", lambda b, a, d: a.update(narration_fixture_mode=True))
    add("decision_hash_mismatch_blocks", "BLOCKED", dsha="0" * 64)
    add("media_hash_mismatch_blocks", "BLOCKED", media="1" * 64)
    add("motion_mismatch_blocks", "BLOCKED", lambda b, a, d: a.update(motion_decision="REVERT_V1_2F"))
    add("picture_mismatch_blocks", "BLOCKED", lambda b, a, d: a.update(picture_sha256="2" * 64))
    add("technical_failure_blocks", "BLOCKED", lambda b, a, d: b["technical_checks"].update(failed=1))
    add("authority_claim_blocks", "BLOCKED", lambda b, a, d: a.update(publishable=True))
    add("publication_scope_mismatch_blocks", "BLOCKED", lambda b, a, d: a.update(publication_scope="AUTHORIZE_PUBLICATION"))
    add("nan_duration_blocks", "BLOCKED", lambda b, a, d: a.update(duration_seconds=float("nan")))

    rows = []
    for name, b, a, d, msha, dsha, expected in cases:
        result = validate_chain(b, a, d, msha, dsha)
        authority_closed = all(result.get(k) is False for k in (
            "final_master_present", "upload_authorized", "publishable", "release_authorized"
        ))
        passed = result["verdict"] == expected and authority_closed and result.get("preflight_only") is True
        rows.append({
            "test": name,
            "expected": expected,
            "actual": result["verdict"],
            "authority_closed": str(authority_closed).lower(),
            "result": "PASS" if passed else "FAIL",
            "failures": "|".join(result.get("failures", [])),
        })

    with MATRIX.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"tests": len(rows), "passed": sum(r["result"] == "PASS" for r in rows), "matrix": str(MATRIX)}, indent=2))
    return 0 if all(r["result"] == "PASS" for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
