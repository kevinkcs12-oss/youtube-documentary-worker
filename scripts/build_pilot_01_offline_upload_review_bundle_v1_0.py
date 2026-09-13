#!/usr/bin/env python3
"""Build a deterministic, offline-only upload review bundle for Pilot 01."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

from validate_pilot_01_executive_release_decision_v1_1 import validate_data


SCHEMA = "pilot-01-offline-upload-review-bundle-v1.0"
VALIDATION_SCHEMA = "pilot-01-offline-upload-review-bundle-validation-v1.0"
EXPECTED_CHAPTERS = ["00:00", "01:04", "02:22", "03:30", "04:45", "06:04", "07:19", "08:35"]
EXPECTED_SOURCE_IDS = {f"F{i}" for i in range(1, 8)} | {f"CE{i}" for i in range(1, 4)}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def image_dimensions(path: Path) -> tuple[int, int]:
    result = subprocess.run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "json", str(path),
    ], check=True, capture_output=True, text=True)
    stream = json.loads(result.stdout)["streams"][0]
    return int(stream["width"]), int(stream["height"])


def srt_seconds(value: str) -> float:
    hours, minutes, rest = value.split(":")
    seconds, millis = rest.split(",")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000


def validate_sidecars(captions: Path, description: Path, sources: Path,
                      metadata: Path, thumbnails: dict[str, Path],
                      metadata_choice: str) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    text = captions.read_text(encoding="utf-8")
    blocks = [block for block in re.split(r"\n\s*\n", text.strip()) if block]
    cues: list[tuple[float, float]] = []
    try:
        for block in blocks:
            lines = block.splitlines()
            match = re.fullmatch(r"(\d\d:\d\d:\d\d,\d{3}) --> (\d\d:\d\d:\d\d,\d{3})", lines[1])
            if not match:
                raise ValueError
            cues.append((srt_seconds(match.group(1)), srt_seconds(match.group(2))))
    except (IndexError, ValueError):
        failures.append("captions_parse")
        cues = []
    if len(cues) != 161:
        failures.append("captions_count")
    if cues and (any(left[1] > right[0] for left, right in zip(cues, cues[1:])) or cues[-1][1] > 597.760):
        failures.append("captions_timing")

    description_text = description.read_text(encoding="utf-8")
    if re.findall(r"(?m)^(\d\d:\d\d) ", description_text) != EXPECTED_CHAPTERS:
        failures.append("description_chapters")
    if "not that everything is literally identical" not in description_text:
        failures.append("description_scope_disclaimer")
    if "do not grant visual-use rights" not in description_text:
        failures.append("description_rights_disclaimer")

    with sources.open(newline="", encoding="utf-8") as handle:
        source_rows = list(csv.DictReader(handle))
    source_ids = {row.get("id", "") for row in source_rows}
    if len(source_rows) != 10 or source_ids != EXPECTED_SOURCE_IDS:
        failures.append("source_registry_rows")
    if any(not row.get("claim_not_supported", "").strip() for row in source_rows):
        failures.append("source_boundaries")

    with metadata.open(newline="", encoding="utf-8") as handle:
        metadata_rows = list(csv.DictReader(handle))
    cells = {row.get("cell", "") for row in metadata_rows}
    if len(metadata_rows) != 3 or cells != {"A", "B", "C"}:
        failures.append("metadata_cells")
    selected = ["A", "B", "C"] if metadata_choice == "NATIVE_AB_TEST_A_B_C" else [metadata_choice.removeprefix("CELL_")]
    if any(cell not in {"A", "B", "C"} for cell in selected):
        failures.append("metadata_selection")
    for cell in selected:
        path = thumbnails.get(cell)
        if path is None or not path.is_file():
            failures.append(f"thumbnail_{cell}_missing")
        elif image_dimensions(path) != (1280, 720):
            failures.append(f"thumbnail_{cell}_geometry")
    return list(dict.fromkeys(failures)), selected


def validate_chain(master: Path, master_validation: dict[str, object],
                   preflight_path: Path, preflight: dict[str, object],
                   decision_path: Path, decision: dict[str, object]) -> list[str]:
    failures: list[str] = []
    if master_validation.get("schema") != "pilot-01-final-master-candidate-validation-v1.0":
        failures.append("master_validation_schema")
    if master_validation.get("verdict") != "PASS_MASTER_CANDIDATE_ONLY" or master_validation.get("failures") != []:
        failures.append("master_validation_verdict")
    if master_validation.get("candidate_sha256") != sha256(master):
        failures.append("master_candidate_sha256")
    if master_validation.get("preflight_validation_sha256") != sha256(preflight_path):
        failures.append("preflight_validation_sha256")
    if master_validation.get("master_candidate_present") is not True:
        failures.append("master_candidate_absent")
    for key in ("final_master_present", "upload_authorized", "publishable", "release_authorized"):
        if master_validation.get(key) is not False:
            failures.append(f"master_{key}")

    if preflight.get("schema") != "pilot-01-chained-release-preflight-v1.1" or preflight.get("verdict") != "PASS_MEDIA_VERIFIED_PREFLIGHT_ONLY":
        failures.append("preflight_status")
    if preflight.get("decision_manifest_sha256") != sha256(decision_path):
        failures.append("decision_manifest_sha256")
    for key in ("final_master_present", "upload_authorized", "publishable", "release_authorized"):
        if preflight.get(key) is not False:
            failures.append(f"preflight_{key}")

    decision_result = validate_data(decision, release=True)
    if decision_result.get("status") != "DECISION_MANIFEST_COMPLETE_FOR_DOWNSTREAM_PREFLIGHT":
        failures.append("executive_decision")
    if decision_result.get("release_authorized") is not False:
        failures.append("executive_authority_claim")
    if preflight.get("publication_scope_reviewed") != decision.get("decisions", {}).get("publication"):
        failures.append("publication_scope")
    return list(dict.fromkeys(failures))


def deterministic_zip(output: Path, entries: dict[str, Path], manifest: dict[str, object]) -> None:
    if output.exists():
        raise ValueError("bundle output already exists")
    partial = output.with_name(output.name + ".partial")
    if partial.exists():
        raise ValueError("bundle partial output already exists")
    try:
        with zipfile.ZipFile(partial, "x", compression=zipfile.ZIP_STORED) as archive:
            payloads = {"UPLOAD_REVIEW_MANIFEST.json": (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")}
            payloads.update({name: path.read_bytes() for name, path in entries.items()})
            for name in sorted(payloads):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_STORED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, payloads[name])
        partial.rename(output)
    except Exception:
        if partial.exists():
            partial.unlink()
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--master-candidate", type=Path, required=True)
    parser.add_argument("--master-validation", type=Path, required=True)
    parser.add_argument("--preflight-validation", type=Path, required=True)
    parser.add_argument("--decision-manifest", type=Path, required=True)
    parser.add_argument("--captions", type=Path, required=True)
    parser.add_argument("--description", type=Path, required=True)
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--thumbnail-a", type=Path)
    parser.add_argument("--thumbnail-b", type=Path)
    parser.add_argument("--thumbnail-c", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--validation-output", type=Path, required=True)
    args = parser.parse_args()
    try:
        master_validation = json.loads(args.master_validation.read_text(encoding="utf-8"))
        preflight = json.loads(args.preflight_validation.read_text(encoding="utf-8"))
        decision = json.loads(args.decision_manifest.read_text(encoding="utf-8"))
        failures = validate_chain(args.master_candidate, master_validation, args.preflight_validation, preflight, args.decision_manifest, decision)
        thumbnails = {key: value for key, value in {"A": args.thumbnail_a, "B": args.thumbnail_b, "C": args.thumbnail_c}.items() if value}
        sidecar_failures, selected = validate_sidecars(args.captions, args.description, args.sources, args.metadata, thumbnails, decision.get("decisions", {}).get("metadata", ""))
        failures.extend(sidecar_failures)
        if failures:
            result = {"schema": VALIDATION_SCHEMA, "verdict": "BLOCKED", "failures": list(dict.fromkeys(failures))}
        else:
            entries = {
                "master_candidate.mp4": args.master_candidate,
                "captions.srt": args.captions,
                "description.txt": args.description,
                "source_registry.csv": args.sources,
                "metadata_variants.csv": args.metadata,
                "executive_decision_manifest.json": args.decision_manifest,
                "media_preflight_validation.json": args.preflight_validation,
                "master_candidate_validation.json": args.master_validation,
            }
            entries.update({f"thumbnail_{cell}.png": thumbnails[cell] for cell in selected})
            manifest = {
                "schema": SCHEMA,
                "project": "Why Does Everything Look the Same Now?",
                "files": {name: {"sha256": sha256(path), "bytes": path.stat().st_size} for name, path in sorted(entries.items())},
                "metadata_cells_included": selected,
                "publication_scope_reviewed": decision["decisions"]["publication"],
                "offline_review_bundle_only": True,
                "upload_authorized": False,
                "publishable": False,
                "release_authorized": False,
            }
            deterministic_zip(args.output, entries, manifest)
            result = {
                "schema": VALIDATION_SCHEMA,
                "verdict": "PASS_OFFLINE_UPLOAD_REVIEW_BUNDLE_ONLY",
                "failures": [],
                "bundle_sha256": sha256(args.output),
                "metadata_cells_included": selected,
                "offline_review_bundle_only": True,
                "upload_authorized": False,
                "publishable": False,
                "release_authorized": False,
            }
    except (OSError, ValueError, KeyError, IndexError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        result = {"schema": VALIDATION_SCHEMA, "verdict": "BLOCKED", "failures": [f"input_or_bundle_error:{type(exc).__name__}"]}
    result.update({"upload_authorized": False, "publishable": False, "release_authorized": False})
    args.validation_output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["verdict"] == "PASS_OFFLINE_UPLOAD_REVIEW_BUNDLE_ONLY" else 2


if __name__ == "__main__":
    sys.exit(main())
