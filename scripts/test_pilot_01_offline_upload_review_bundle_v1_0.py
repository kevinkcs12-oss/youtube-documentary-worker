#!/usr/bin/env python3
"""Adversarial tests for Pilot 01 offline upload review bundle v1.0."""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from build_pilot_01_offline_upload_review_bundle_v1_0 import deterministic_zip, validate_chain, validate_sidecars
from test_pilot_01_release_preflight_v1_0 import fixtures as decision_fixtures


ROOT = Path(__file__).resolve().parent
MATRIX = ROOT / "Pilot_01_Offline_Upload_Review_Bundle_Test_Matrix_v1.0.csv"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    rows = []
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        master = root / "candidate.mp4"
        master.write_bytes(b"candidate-fixture")
        _, _, decision, _, _ = decision_fixtures()
        decision_path = root / "decision.json"
        decision_path.write_text(json.dumps(decision, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        preflight = {
            "schema": "pilot-01-chained-release-preflight-v1.1",
            "verdict": "PASS_MEDIA_VERIFIED_PREFLIGHT_ONLY",
            "decision_manifest_sha256": digest(decision_path),
            "publication_scope_reviewed": "AUTHORIZE_UNLISTED_UPLOAD",
            "final_master_present": False, "upload_authorized": False,
            "publishable": False, "release_authorized": False,
        }
        preflight_path = root / "preflight.json"
        preflight_path.write_text(json.dumps(preflight, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        master_validation = {
            "schema": "pilot-01-final-master-candidate-validation-v1.0",
            "verdict": "PASS_MASTER_CANDIDATE_ONLY", "failures": [],
            "candidate_sha256": digest(master), "preflight_validation_sha256": digest(preflight_path),
            "master_candidate_present": True, "final_master_present": False,
            "upload_authorized": False, "publishable": False, "release_authorized": False,
        }

        def chain_case(name: str, expected: bool, mutate=None) -> None:
            mv, pf, dec = copy.deepcopy(master_validation), copy.deepcopy(preflight), copy.deepcopy(decision)
            if mutate: mutate(mv, pf, dec)
            actual = not validate_chain(master, mv, preflight_path, pf, decision_path, dec)
            rows.append({"test": name, "expected": str(expected).lower(), "actual": str(actual).lower(), "result": "PASS" if actual == expected else "FAIL"})

        chain_case("valid_chain", True)
        chain_case("wrong_master_sha_blocks", False, lambda m, p, d: m.update(candidate_sha256="0" * 64))
        chain_case("wrong_master_verdict_blocks", False, lambda m, p, d: m.update(verdict="BLOCKED"))
        chain_case("preflight_hash_mismatch_blocks", False, lambda m, p, d: m.update(preflight_validation_sha256="0" * 64))
        chain_case("decision_hash_mismatch_blocks", False, lambda m, p, d: p.update(decision_manifest_sha256="0" * 64))
        chain_case("hold_decision_blocks", False, lambda m, p, d: d["decisions"].update(publication="HOLD"))
        chain_case("master_upload_claim_blocks", False, lambda m, p, d: m.update(upload_authorized=True))

        captions = root / "captions.srt"
        blocks = []
        for index in range(161):
            start_ms, end_ms = index * 3000, index * 3000 + 2000
            stamp = lambda value: f"00:{value // 60000:02d}:{(value % 60000) // 1000:02d},{value % 1000:03d}"
            blocks.append(f"{index + 1}\n{stamp(start_ms)} --> {stamp(end_ms)}\nCue {index + 1}")
        captions.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
        description = root / "description.txt"
        description.write_text("\n".join(f"{time} Chapter" for time in ["00:00", "01:04", "02:22", "03:30", "04:45", "06:04", "07:19", "08:35"]) + "\nnot that everything is literally identical\ndo not grant visual-use rights\n", encoding="utf-8")
        sources = root / "sources.csv"
        with sources.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["id", "claim_not_supported"]); writer.writeheader()
            writer.writerows({"id": name, "claim_not_supported": "bounded"} for name in [*[f"F{i}" for i in range(1, 8)], *[f"CE{i}" for i in range(1, 4)]])
        metadata = root / "metadata.csv"
        with metadata.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["cell", "title"]); writer.writeheader()
            writer.writerows({"cell": cell, "title": f"Title {cell}"} for cell in "ABC")
        thumbs = {}
        for cell in "ABC":
            path = root / f"thumb_{cell}.png"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=c=black:s=1280x720:d=0.04", "-frames:v", "1", str(path)], check=True)
            thumbs[cell] = path

        def sidecar_case(name: str, expected: bool, choice="NATIVE_AB_TEST_A_B_C", mutate=None) -> None:
            paths = {"captions": captions, "description": description, "sources": sources, "metadata": metadata, "thumbs": dict(thumbs)}
            if mutate: mutate(paths)
            failures, _ = validate_sidecars(paths["captions"], paths["description"], paths["sources"], paths["metadata"], paths["thumbs"], choice)
            actual = not failures
            rows.append({"test": name, "expected": str(expected).lower(), "actual": str(actual).lower(), "result": "PASS" if actual == expected else "FAIL"})

        sidecar_case("valid_sidecars", True)
        bad_captions = root / "bad.srt"; bad_captions.write_text("1\n00:00:00,000 --> 00:00:01,000\nOnly one\n", encoding="utf-8")
        sidecar_case("caption_count_blocks", False, mutate=lambda p: p.update(captions=bad_captions))
        bad_description = root / "bad.txt"; bad_description.write_text("missing chapters", encoding="utf-8")
        sidecar_case("description_contract_blocks", False, mutate=lambda p: p.update(description=bad_description))
        sidecar_case("missing_selected_thumbnail_blocks", False, choice="CELL_B", mutate=lambda p: p["thumbs"].pop("B"))
        wrong_thumb = root / "wrong.png"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=640x360:d=0.04", "-frames:v", "1", str(wrong_thumb)], check=True)
        sidecar_case("thumbnail_geometry_blocks", False, choice="CELL_A", mutate=lambda p: p["thumbs"].update(A=wrong_thumb))

        master_validation_path = root / "master_validation.json"
        master_validation_path.write_text(json.dumps(master_validation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        base_command = [
            sys.executable, str(ROOT / "build_pilot_01_offline_upload_review_bundle_v1_0.py"),
            "--master-candidate", str(master), "--master-validation", str(master_validation_path),
            "--preflight-validation", str(preflight_path), "--decision-manifest", str(decision_path),
            "--description", str(description), "--sources", str(sources), "--metadata", str(metadata),
            "--thumbnail-a", str(thumbs["A"]), "--thumbnail-b", str(thumbs["B"]), "--thumbnail-c", str(thumbs["C"]),
        ]
        cli_bundle, cli_validation = root / "cli.zip", root / "cli_validation.json"
        cli = subprocess.run(base_command + ["--captions", str(captions), "--output", str(cli_bundle), "--validation-output", str(cli_validation)], capture_output=True, text=True)
        cli_data = json.loads(cli_validation.read_text(encoding="utf-8"))
        with zipfile.ZipFile(cli_bundle) as archive:
            cli_entries = set(archive.namelist())
        cli_pass = cli.returncode == 0 and cli_data["verdict"] == "PASS_OFFLINE_UPLOAD_REVIEW_BUNDLE_ONLY" and {"thumbnail_A.png", "thumbnail_B.png", "thumbnail_C.png", "UPLOAD_REVIEW_MANIFEST.json"}.issubset(cli_entries)
        rows.append({"test": "cli_builds_closed_authority_bundle", "expected": "true", "actual": str(cli_pass).lower(), "result": "PASS" if cli_pass else "FAIL"})

        blocked_bundle, blocked_validation = root / "blocked.zip", root / "blocked_validation.json"
        blocked = subprocess.run(base_command + ["--captions", str(bad_captions), "--output", str(blocked_bundle), "--validation-output", str(blocked_validation)], capture_output=True, text=True)
        blocked_data = json.loads(blocked_validation.read_text(encoding="utf-8"))
        blocked_pass = blocked.returncode == 2 and blocked_data["verdict"] == "BLOCKED" and not blocked_bundle.exists()
        rows.append({"test": "cli_blocked_input_creates_no_bundle", "expected": "true", "actual": str(blocked_pass).lower(), "result": "PASS" if blocked_pass else "FAIL"})

        entries = {"master_candidate.mp4": master, "captions.srt": captions}
        manifest = {"schema": "fixture", "upload_authorized": False, "publishable": False}
        first, second = root / "one.zip", root / "two.zip"
        deterministic_zip(first, entries, manifest); deterministic_zip(second, entries, manifest)
        rows.append({"test": "bundle_is_byte_deterministic", "expected": "true", "actual": str(digest(first) == digest(second)).lower(), "result": "PASS" if digest(first) == digest(second) else "FAIL"})

        try:
            deterministic_zip(first, entries, manifest)
            refused_existing = False
        except ValueError:
            refused_existing = True
        rows.append({"test": "existing_bundle_refused", "expected": "true", "actual": str(refused_existing).lower(), "result": "PASS" if refused_existing else "FAIL"})

        failed_output = root / "failed.zip"
        try:
            deterministic_zip(failed_output, {"missing.bin": root / "missing.bin"}, manifest)
        except OSError:
            pass
        clean_failure = not failed_output.exists() and not failed_output.with_name(failed_output.name + ".partial").exists()
        rows.append({"test": "failed_build_leaves_no_partial_archive", "expected": "true", "actual": str(clean_failure).lower(), "result": "PASS" if clean_failure else "FAIL"})

    with MATRIX.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    print(json.dumps({"tests": len(rows), "passed": sum(row["result"] == "PASS" for row in rows), "matrix": str(MATRIX)}, indent=2))
    return 0 if all(row["result"] == "PASS" for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
