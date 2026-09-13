#!/usr/bin/env python3
"""Synthetic-fixture and adversarial tests for the Pilot 01 narration conformer."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CUES = ROOT / "Pilot_01_Final_Voice_Cue_Sheet_v1.0.csv"
CONTRACT = ROOT / "Pilot_01_Final_Voice_Delivery_Contract_v1.0.csv"
VALIDATOR = ROOT / "validate_pilot_01_final_voice_delivery.py"
CONFORMER = ROOT / "conform_pilot_01_final_narration_timeline_v1_0.py"
WORK = ROOT / "narration_conform_fixture_work"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(command: list[str], expected: int = 0) -> subprocess.CompletedProcess:
    p = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != expected:
        raise RuntimeError(f"expected exit {expected}, got {p.returncode}: {p.stderr[-1000:]}")
    return p


def tone(path: Path, duration: float, frequency: int) -> None:
    run([
        "ffmpeg", "-y", "-nostdin", "-v", "error", "-f", "lavfi", "-i",
        f"sine=frequency={frequency}:sample_rate=48000:duration={duration:.6f}",
        "-af", "volume=2.0", "-ac", "1", "-ar", "48000", "-c:a", "pcm_s24le", str(path),
    ])


def build_fixture(delivery: Path, overlong_first: bool = False) -> Path:
    delivery.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(CUES.open(encoding="utf-8")))
    takes = []
    for i, row in enumerate(rows, 1):
        available = float(row["available_seconds"])
        speech_target = int(row["word_count"]) * 60 / 142
        duration = min(max(0.30, speech_target), available - 0.10)
        if i == 1 and overlong_first:
            duration = available + 0.25
        path = delivery / f'T{i:03d}.wav'
        tone(path, duration, 310 + i % 17 * 11)
        takes.append({"take_id": f"T{i:03d}", "filename": path.name, "sha256": sha256(path)})
    room = delivery / "ROOM_TONE.wav"
    run([
        "ffmpeg", "-y", "-nostdin", "-v", "error", "-f", "lavfi", "-i",
        "anoisesrc=color=pink:amplitude=0.002:sample_rate=48000:duration=30.5",
        "-ac", "1", "-ar", "48000", "-c:a", "pcm_s24le", str(room),
    ])
    manifest = {
        "schema": "pilot-01-final-voice-delivery-v1.0",
        "editorial_status": "SYNTHETIC_FIXTURE_ONLY_DO_NOT_PUBLISH",
        "selected_voice": "A",
        "recording_authorization_id": "FIXTURE_ONLY_DO_NOT_USE",
        "performer_consent_asserted": True,
        "pronunciation_verified": {"Nielsen": True, "Spotify": True},
        "capture": {"dry": True, "music_present": False, "sample_rate_hz": 48000, "bit_depth": 24, "channels": 1},
        "room_tone_file": "ROOM_TONE.wav",
        "contract_sha256": sha256(CONTRACT),
        "takes": takes,
    }
    manifest_path = delivery.parent / (delivery.name + "_manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def conform(delivery: Path, manifest: Path, prefix: str, cue: Path = CUES, expected: int = 0) -> dict:
    result = WORK / f"{prefix}_result.json"
    run([
        sys.executable, str(CONFORMER), "--delivery-dir", str(delivery), "--manifest", str(manifest),
        "--cue-sheet", str(cue), "--validator", str(VALIDATOR),
        "--output", str(WORK / f"{prefix}.wav"),
        "--placements", str(WORK / f"{prefix}_placements.csv"),
        "--result", str(result), "--fixture-mode",
    ], expected=expected)
    return json.loads(result.read_text(encoding="utf-8"))


def main() -> int:
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir()
    run([sys.executable, str(VALIDATOR), "--emit-contract"])
    positive = WORK / "positive_delivery"
    positive_manifest = build_fixture(positive)
    first = conform(positive, positive_manifest, "positive_a")
    second = conform(positive, positive_manifest, "positive_b")
    if first["verdict"] != "PASS_FIXTURE_CONFORM_ONLY" or first["samples"] != 28692480:
        raise RuntimeError("positive conform verdict or sample count mismatch")
    if first["output_sha256"] != second["output_sha256"]:
        raise RuntimeError("independent conform outputs are not deterministic")

    overlong = WORK / "overlong_delivery"
    overlong_manifest = build_fixture(overlong, overlong_first=True)
    overlong_result = conform(overlong, overlong_manifest, "overlong", expected=2)
    if "exceeds cue window" not in overlong_result.get("error", ""):
        raise RuntimeError("overlong take was not specifically blocked")

    missing = WORK / "missing_delivery"
    shutil.copytree(positive, missing, copy_function=lambda s, d: shutil.copy2(s, d))
    (missing / "T091.wav").unlink()
    missing_manifest = WORK / "missing_manifest.json"
    shutil.copy2(positive_manifest, missing_manifest)
    missing_result = conform(missing, missing_manifest, "missing", expected=2)
    if "intake" not in missing_result.get("error", "") and "exit status" not in missing_result.get("error", ""):
        raise RuntimeError("missing take did not fail closed at intake")

    altered_cue = WORK / "altered_cues.csv"
    altered_cue.write_text(CUES.read_text(encoding="utf-8").replace("00:00:07.000", "00:00:06.900", 1), encoding="utf-8")
    altered_result = conform(positive, positive_manifest, "altered_cue", cue=altered_cue, expected=2)
    if "cue-sheet SHA-256 mismatch" not in altered_result.get("error", ""):
        raise RuntimeError("altered cue sheet was not blocked")

    matrix = [
        {"test": "positive fixture", "expected": "PASS_FIXTURE_CONFORM_ONLY", "observed": first["verdict"], "result": "PASS"},
        {"test": "independent deterministic rerender", "expected": "identical SHA-256", "observed": first["output_sha256"], "result": "PASS"},
        {"test": "overlong take", "expected": "BLOCKED", "observed": overlong_result["verdict"], "result": "PASS"},
        {"test": "missing take", "expected": "BLOCKED", "observed": missing_result["verdict"], "result": "PASS"},
        {"test": "altered cue sheet", "expected": "BLOCKED", "observed": altered_result["verdict"], "result": "PASS"},
    ]
    out = ROOT / "Pilot_01_Final_Narration_Timeline_Conform_Test_Matrix_v1.0.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(matrix[0]))
        writer.writeheader(); writer.writerows(matrix)
    print(json.dumps({"verdict": "PASS_FIXTURE_CONFORM_ONLY", "tests": len(matrix), "output_sha256": first["output_sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
