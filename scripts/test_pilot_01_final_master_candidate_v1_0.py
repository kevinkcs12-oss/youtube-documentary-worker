#!/usr/bin/env python3
"""Adversarial and real-remux tests for Pilot 01 final master candidate v1.0."""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from build_pilot_01_final_master_candidate_v1_0 import (
    CANDIDATE_LABEL, remux_candidate, stream_hashes, validate_preflight,
)


ROOT = Path(__file__).resolve().parent
MATRIX = ROOT / "Pilot_01_Final_Master_Candidate_Test_Matrix_v1.0.csv"


def base_preflight(media_sha: str) -> dict:
    return {
        "schema": "pilot-01-chained-release-preflight-v1.1",
        "verdict": "PASS_MEDIA_VERIFIED_PREFLIGHT_ONLY",
        "failures": [],
        "media_observed_directly": True,
        "full_decode_passed": True,
        "preflight_only": True,
        "audio_conform_sha256": media_sha,
        "final_master_present": False,
        "upload_authorized": False,
        "publishable": False,
        "release_authorized": False,
    }


def main() -> int:
    media_sha = "a" * 64
    base = base_preflight(media_sha)
    cases = []

    def add(name: str, expected_pass: bool, mutate=None, supplied_sha: str | None = None) -> None:
        item = copy.deepcopy(base)
        if mutate:
            mutate(item)
        failures = validate_preflight(item, supplied_sha or media_sha)
        actual = not failures
        cases.append({"test": name, "expected": expected_pass, "actual": actual, "failures": "|".join(failures)})

    add("complete_preflight_contract", True)
    add("wrong_schema_blocks", False, lambda x: x.update(schema="v1.0"))
    add("blocked_verdict_blocks", False, lambda x: x.update(verdict="BLOCKED"))
    add("nonempty_failures_block", False, lambda x: x.update(failures=["x"]))
    add("unobserved_media_blocks", False, lambda x: x.update(media_observed_directly=False))
    add("decode_not_proven_blocks", False, lambda x: x.update(full_decode_passed=False))
    add("wrong_input_bytes_block", False, supplied_sha="b" * 64)
    add("upload_claim_blocks", False, lambda x: x.update(upload_authorized=True))
    add("publishable_claim_blocks", False, lambda x: x.update(publishable=True))
    add("release_claim_blocks", False, lambda x: x.update(release_authorized=True))

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source, first, second = root / "source.mp4", root / "first.mp4", root / "second.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-v", "error",
            "-f", "lavfi", "-i", "testsrc2=s=320x180:r=25:d=2",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=2",
            "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac", "-ac", "1", str(source),
        ], check=True)
        remux_candidate(source, first)
        remux_candidate(source, second)
        source_streams, first_streams = stream_hashes(source), stream_hashes(first)
        deterministic = hashlib.sha256(first.read_bytes()).hexdigest() == hashlib.sha256(second.read_bytes()).hexdigest()
        probe = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format_tags=title,comment",
            "-of", "json", str(first),
        ], check=True, capture_output=True, text=True)
        tags = json.loads(probe.stdout).get("format", {}).get("tags", {})
        cases.extend([
            {"test": "real_remux_preserves_stream_payloads", "expected": True, "actual": source_streams == first_streams, "failures": ""},
            {"test": "real_remux_is_byte_deterministic", "expected": True, "actual": deterministic, "failures": ""},
            {"test": "real_remux_sets_nonupload_identity", "expected": True, "actual": tags.get("title") == CANDIDATE_LABEL and tags.get("comment") == CANDIDATE_LABEL, "failures": ""},
        ])
        blocked_manifest = root / "blocked_preflight.json"
        blocked_manifest.write_text(json.dumps({**base, "verdict": "BLOCKED"}), encoding="utf-8")
        blocked_output = root / "must_not_exist.mp4"
        blocked_validation = root / "blocked_validation.json"
        blocked_run = subprocess.run([
            "python3", str(ROOT / "build_pilot_01_final_master_candidate_v1_0.py"),
            "--audio-conform", str(source),
            "--preflight-validation", str(blocked_manifest),
            "--output", str(blocked_output),
            "--validation-output", str(blocked_validation),
        ], capture_output=True, text=True)
        blocked_result = json.loads(blocked_validation.read_text(encoding="utf-8"))
        cases.append({
            "test": "closed_preflight_creates_no_candidate",
            "expected": True,
            "actual": blocked_run.returncode == 2 and not blocked_output.exists() and blocked_result.get("verdict") == "BLOCKED",
            "failures": "",
        })

    for row in cases:
        row["result"] = "PASS" if row["actual"] == row["expected"] else "FAIL"
        row["expected"] = str(row["expected"]).lower()
        row["actual"] = str(row["actual"]).lower()
    with MATRIX.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=cases[0].keys())
        writer.writeheader()
        writer.writerows(cases)
    print(json.dumps({"tests": len(cases), "passed": sum(row["result"] == "PASS" for row in cases), "matrix": str(MATRIX)}, indent=2))
    return 0 if all(row["result"] == "PASS" for row in cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
