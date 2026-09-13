#!/usr/bin/env python3
"""Fail-closed chained release preflight for Pilot 01.

This validator proves that a technically validated package, a canonical executive
decision, and an authorization-bound audio conform agree.  It deliberately cannot
authorize an upload, publication, or final-master designation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

from validate_pilot_01_executive_release_decision_v1_1 import validate_data


SCHEMA = "pilot-01-chained-release-preflight-v1.0"
AUDIO_SCHEMA = "pilot-01-audio-conform-validation-v1.3"
BASELINE_SCHEMA = "pilot-01-prepublication-validation-v1.0"
EXPECTED_HUMAN_GATES = {
    "retain_or_revert_v1.2g_progressive_focus",
    "select_final_voice_after_blind_listening",
    "authorize_music_or_no-music_mix_and_external_publication",
}
HEX_FIELDS = (
    "output_sha256", "decision_manifest_sha256", "picture_sha256",
    "narration_sha256", "narration_conform_result_sha256",
)
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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json_sha256(data: dict[str, object]) -> str:
    payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_chain(
    technical_baseline: dict[str, object],
    audio_validation: dict[str, object],
    decision_manifest: dict[str, object],
    audio_media_sha256: str,
    decision_manifest_sha256: str,
) -> dict[str, object]:
    failures: list[str] = []

    technical = technical_baseline.get("technical_checks", {})
    if technical_baseline.get("schema") != BASELINE_SCHEMA:
        failures.append("technical_baseline_schema")
    if technical_baseline.get("overall") != "PASS_WITH_HUMAN_GATES":
        failures.append("technical_baseline_overall")
    if not isinstance(technical, dict) or technical.get("failed") != 0:
        failures.append("technical_baseline_failures")
    human_gates = technical_baseline.get("human_gates", [])
    if (not isinstance(human_gates, list) or len(human_gates) != len(EXPECTED_HUMAN_GATES)
            or set(human_gates) != EXPECTED_HUMAN_GATES):
        failures.append("technical_baseline_human_gates")

    decision_result = validate_data(decision_manifest, release=True)
    if decision_result.get("status") != "DECISION_MANIFEST_COMPLETE_FOR_DOWNSTREAM_PREFLIGHT":
        failures.append("executive_decision_incomplete")
    if decision_result.get("release_authorized") is not False:
        failures.append("executive_validator_claims_authority")

    if audio_validation.get("schema") != AUDIO_SCHEMA:
        failures.append("audio_schema")
    if audio_validation.get("mode") != "authorization_bound_audio_conform":
        failures.append("audio_mode")
    if audio_validation.get("status") != "PASS":
        failures.append("audio_status")
    if audio_validation.get("publishable") is not False:
        failures.append("audio_claims_publishable")
    if audio_validation.get("release_authorized") is not False:
        failures.append("audio_claims_release_authority")
    if audio_validation.get("audio_conform_only") is not True:
        failures.append("audio_not_conform_only")
    if audio_validation.get("executive_decision_status") != decision_result.get("status"):
        failures.append("executive_status_mismatch")
    for field in HEX_FIELDS:
        value = audio_validation.get(field)
        if (not isinstance(value, str) or len(value) != 64
                or any(char not in "0123456789abcdef" for char in value)):
            failures.append(f"invalid_{field}")
    if audio_validation.get("output_sha256") != audio_media_sha256:
        failures.append("audio_media_sha256")
    if audio_validation.get("decision_manifest_sha256") != decision_manifest_sha256:
        failures.append("decision_manifest_sha256")

    decisions = decision_manifest.get("decisions", {})
    decisions = decisions if isinstance(decisions, dict) else {}
    motion = decisions.get("motion")
    authority = PICTURE_BY_MOTION.get(str(motion))
    if audio_validation.get("motion_decision") != motion:
        failures.append("motion_decision")
    if authority is None:
        failures.append("picture_authority")
    else:
        if audio_validation.get("picture_variant") != authority["variant"]:
            failures.append("picture_variant")
        if audio_validation.get("picture_sha256") != authority["sha256"]:
            failures.append("picture_sha256")

    publication = decisions.get("publication")
    if publication not in {"AUTHORIZE_UNLISTED_UPLOAD", "AUTHORIZE_PUBLICATION"}:
        failures.append("publication_scope_not_affirmative")
    if audio_validation.get("publication_scope") != publication:
        failures.append("publication_scope_mismatch")

    if audio_validation.get("narration_conform_verdict") != "PASS_NARRATION_CONFORM_ONLY":
        failures.append("narration_conform_verdict")
    if audio_validation.get("narration_fixture_mode") is not False:
        failures.append("narration_fixture_mode")
    try:
        duration = float(audio_validation.get("duration_seconds", -1))
    except (TypeError, ValueError):
        duration = -1.0
    if not math.isfinite(duration) or abs(duration - 597.760) > 0.001:
        failures.append("duration")
    if audio_validation.get("video_frames") != 14944:
        failures.append("frames")
    if audio_validation.get("geometry") != "1920x1080":
        failures.append("geometry")
    if audio_validation.get("fps") != "25/1":
        failures.append("fps")
    if audio_validation.get("audio_sample_rate") != 48000:
        failures.append("audio_sample_rate")
    if audio_validation.get("audio_channels") != 1:
        failures.append("audio_channels")

    failures = list(dict.fromkeys(failures))
    passed = not failures
    return {
        "schema": SCHEMA,
        "verdict": "PASS_CHAINED_PREFLIGHT_ONLY" if passed else "BLOCKED",
        "failures": failures,
        "technical_baseline_status": technical_baseline.get("overall"),
        "executive_decision_status": decision_result.get("status"),
        "publication_scope_reviewed": publication,
        "motion_decision": motion,
        "picture_variant": audio_validation.get("picture_variant"),
        "picture_sha256": audio_validation.get("picture_sha256"),
        "audio_conform_sha256": audio_media_sha256,
        "decision_manifest_sha256": decision_manifest_sha256,
        "authorization_id_present": bool(decision_result.get("authorization_id_present")),
        "final_master_present": False,
        "upload_authorized": False,
        "publishable": False,
        "release_authorized": False,
        "preflight_only": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--technical-baseline", type=Path, required=True)
    parser.add_argument("--audio-conform", type=Path, required=True)
    parser.add_argument("--audio-validation", type=Path, required=True)
    parser.add_argument("--decision-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        baseline = json.loads(args.technical_baseline.read_text(encoding="utf-8"))
        audio = json.loads(args.audio_validation.read_text(encoding="utf-8"))
        decision = json.loads(args.decision_manifest.read_text(encoding="utf-8"))
        result = validate_chain(
            baseline,
            audio,
            decision,
            sha256(args.audio_conform),
            sha256(args.decision_manifest),
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        result = {
            "schema": SCHEMA,
            "verdict": "BLOCKED",
            "failures": [f"input_error:{type(exc).__name__}"],
            "final_master_present": False,
            "upload_authorized": False,
            "publishable": False,
            "release_authorized": False,
            "preflight_only": True,
        }

    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["verdict"] == "PASS_CHAINED_PREFLIGHT_ONLY" else 2


if __name__ == "__main__":
    sys.exit(main())
