#!/usr/bin/env python3
"""Adversarial tests for media-verified chained preflight v1.1."""

from __future__ import annotations

import copy
import csv
import json
from pathlib import Path

from test_pilot_01_release_preflight_v1_0 import fixtures
from validate_pilot_01_release_preflight_v1_1 import EXPECTED_LABEL, validate_chain


ROOT = Path(__file__).resolve().parent
MATRIX = ROOT / "Pilot_01_Media_Verified_Preflight_Test_Matrix_v1.1.csv"


def facts() -> dict:
    return {
        "decode_ok": True,
        "video_stream_count": 1,
        "audio_stream_count": 1,
        "duration_seconds": "597.760000",
        "video_frames": "14944",
        "geometry": "1920x1080",
        "fps": "25/1",
        "audio_sample_rate": "48000",
        "audio_channels": 1,
        "title": EXPECTED_LABEL,
        "comment": EXPECTED_LABEL,
        "integrated_lufs": "-16.02",
        "true_peak_dbtp": "-1.18",
    }


def main() -> int:
    base, audio, decision, media_sha, decision_sha = fixtures()
    cases = []

    def add(name: str, expected: str = "BLOCKED", mutate=None) -> None:
        b, a, d, f = copy.deepcopy(base), copy.deepcopy(audio), copy.deepcopy(decision), facts()
        if mutate:
            mutate(b, a, d, f)
        cases.append((name, expected, b, a, d, f))

    add("valid_media_verified_fixture", "PASS_MEDIA_VERIFIED_PREFLIGHT_ONLY")
    add("decode_failure_blocks", mutate=lambda b, a, d, f: f.update(decode_ok=False))
    add("extra_audio_stream_blocks", mutate=lambda b, a, d, f: f.update(audio_stream_count=2))
    add("observed_duration_mismatch_blocks", mutate=lambda b, a, d, f: f.update(duration_seconds="597.700"))
    add("observed_frame_mismatch_blocks", mutate=lambda b, a, d, f: f.update(video_frames="14943"))
    add("observed_geometry_mismatch_blocks", mutate=lambda b, a, d, f: f.update(geometry="1280x720"))
    add("observed_fps_mismatch_blocks", mutate=lambda b, a, d, f: f.update(fps="30/1"))
    add("observed_audio_format_mismatch_blocks", mutate=lambda b, a, d, f: f.update(audio_sample_rate="44100"))
    add("identity_metadata_missing_blocks", mutate=lambda b, a, d, f: f.update(title=None))
    add("loudness_out_of_range_blocks", mutate=lambda b, a, d, f: f.update(integrated_lufs="-18.0"))
    add("true_peak_out_of_range_blocks", mutate=lambda b, a, d, f: f.update(true_peak_dbtp="-0.5"))
    add("nonfinite_loudness_blocks", mutate=lambda b, a, d, f: f.update(integrated_lufs=float("nan")))
    add("declared_observed_disagreement_blocks", mutate=lambda b, a, d, f: a.update(video_frames=14945))
    add("upstream_chain_failure_still_blocks", mutate=lambda b, a, d, f: a.update(decision_manifest_sha256="0" * 64))

    rows = []
    for name, expected, b, a, d, f in cases:
        result = validate_chain(b, a, d, media_sha, decision_sha, f)
        authority_closed = all(result.get(key) is False for key in (
            "final_master_present", "upload_authorized", "publishable", "release_authorized",
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
    print(json.dumps({"tests": len(rows), "passed": sum(row["result"] == "PASS" for row in rows), "matrix": str(MATRIX)}, indent=2))
    return 0 if all(row["result"] == "PASS" for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
