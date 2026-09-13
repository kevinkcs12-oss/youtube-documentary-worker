#!/usr/bin/env python3
"""Fail-closed intake validator for Pilot 01 final narration recordings."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CUE_SHEET = ROOT / "Pilot_01_Final_Voice_Cue_Sheet_v1.0.csv"
CONTRACT = ROOT / "Pilot_01_Final_Voice_Delivery_Contract_v1.0.csv"
TEMPLATE = ROOT / "Pilot_01_Final_Voice_Delivery_Manifest_Template_v1.0.json"
RESULT = ROOT / "Pilot_01_Final_Voice_Delivery_Validation_v1.0.json"
EXPECTED_RATE = 48000
EXPECTED_CODEC = "pcm_s24le"
MAX_PEAK_DBFS = -0.5
SPEECH_THRESHOLD = 10 ** (-45 / 20)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_cues() -> list[dict[str, str]]:
    rows = list(csv.DictReader(CUE_SHEET.open(encoding="utf-8")))
    if len(rows) != 91 or [r["take_id"] for r in rows] != [f"T{i:03d}" for i in range(1, 92)]:
        raise SystemExit("canonical cue sheet does not contain ordered T001-T091")
    return rows


def emit_contract(rows: list[dict[str, str]]) -> None:
    fields = ["take_id", "filename", "sequence", "cue_first", "cue_last", "word_count", "timing_flag", "text_sha256"]
    with CONTRACT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow({
                "take_id": r["take_id"],
                "filename": f'{r["take_id"]}.wav',
                "sequence": r["sequence"],
                "cue_first": r["cue_first"],
                "cue_last": r["cue_last"],
                "word_count": r["word_count"],
                "timing_flag": r["timing_flag"],
                "text_sha256": hashlib.sha256(r["text"].encode("utf-8")).hexdigest(),
            })
    manifest = {
        "schema": "pilot-01-final-voice-delivery-v1.0",
        "editorial_status": "PENDING_HUMAN_DECISIONS",
        "selected_voice": "PENDING",
        "recording_authorization_id": "",
        "performer_consent_asserted": False,
        "pronunciation_verified": {"Nielsen": False, "Spotify": False},
        "capture": {"dry": True, "music_present": False, "sample_rate_hz": EXPECTED_RATE, "bit_depth": 24, "channels": 1},
        "room_tone_file": "ROOM_TONE.wav",
        "contract_sha256": sha256(CONTRACT),
        "takes": [{"take_id": r["take_id"], "filename": f'{r["take_id"]}.wav', "sha256": ""} for r in rows],
    }
    TEMPLATE.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def probe(path: Path) -> dict[str, object]:
    command = ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
               "stream=codec_name,sample_rate,channels,bits_per_raw_sample,duration", "-of", "json", str(path)]
    data = json.loads(subprocess.check_output(command, text=True))
    streams = data.get("streams", [])
    if len(streams) != 1:
        raise ValueError("exactly one audio stream required")
    return streams[0]


def decode_s24le(path: Path) -> tuple[list[int], int]:
    info = probe(path)
    rate = int(info.get("sample_rate", 0))
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(path), "-f", "s24le", "-ac", "1", "-ar", str(rate), "-"])
    values = []
    for i in range(0, len(raw) - 2, 3):
        value = raw[i] | (raw[i + 1] << 8) | (raw[i + 2] << 16)
        if value & 0x800000:
            value -= 1 << 24
        values.append(value)
    return values, rate


def metrics(path: Path, words: int | None = None) -> dict[str, object]:
    values, rate = decode_s24le(path)
    if not values:
        raise ValueError("decoded audio is empty")
    scale = float((1 << 23) - 1)
    peak = max(abs(v) for v in values) / scale
    rms = math.sqrt(sum((v / scale) ** 2 for v in values) / len(values))
    peak_db = 20 * math.log10(max(peak, 1e-12))
    rms_db = 20 * math.log10(max(rms, 1e-12))
    clipping = sum(1 for v in values if abs(v) >= (1 << 23) - 2)
    result: dict[str, object] = {
        "duration_seconds": round(len(values) / rate, 3),
        "peak_dbfs": round(peak_db, 2),
        "rms_dbfs": round(rms_db, 2),
        "clipped_samples": clipping,
    }
    if words is not None:
        active = [i for i, v in enumerate(values) if abs(v) / scale >= SPEECH_THRESHOLD]
        if active:
            speech_seconds = (active[-1] - active[0] + 1) / rate
            result["active_speech_seconds"] = round(speech_seconds, 3)
            result["estimated_wpm"] = round(words * 60 / speech_seconds, 1)
            result["leading_silence_seconds"] = round(active[0] / rate, 3)
            result["trailing_silence_seconds"] = round((len(values) - 1 - active[-1]) / rate, 3)
    return result


def validate(delivery: Path, manifest_path: Path, rows: list[dict[str, str]]) -> dict[str, object]:
    failures: list[str] = []
    warnings: list[str] = []
    observed: list[dict[str, object]] = []
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != "pilot-01-final-voice-delivery-v1.0": failures.append("manifest schema mismatch")
    if manifest.get("selected_voice") not in list("ABCD"): failures.append("selected_voice must be an explicitly approved A-D candidate")
    if not manifest.get("recording_authorization_id"): failures.append("recording_authorization_id is missing")
    if manifest.get("performer_consent_asserted") is not True: failures.append("performer consent is not asserted")
    pronunciations = manifest.get("pronunciation_verified", {})
    for term in ("Nielsen", "Spotify"):
        if pronunciations.get(term) is not True: failures.append(f"pronunciation not verified: {term}")
    capture = manifest.get("capture", {})
    if capture != {"dry": True, "music_present": False, "sample_rate_hz": 48000, "bit_depth": 24, "channels": 1}:
        failures.append("capture declaration must be dry, music-free, mono 48 kHz/24-bit")
    if manifest.get("contract_sha256") != sha256(CONTRACT): failures.append("delivery contract SHA-256 mismatch")
    take_entries = manifest.get("takes", [])
    by_id = {x.get("take_id"): x for x in take_entries if isinstance(x, dict)}
    if len(take_entries) != 91 or len(by_id) != 91: failures.append("manifest must contain 91 unique take entries")
    expected_files = {f'{r["take_id"]}.wav' for r in rows} | {"ROOM_TONE.wav"}
    actual_files = {p.name for p in delivery.glob("*.wav")}
    missing = sorted(expected_files - actual_files)
    extra = sorted(actual_files - expected_files)
    if missing: failures.append("missing WAV files: " + ", ".join(missing))
    if extra: failures.append("unexpected WAV files: " + ", ".join(extra))
    for row in rows:
        take_id = row["take_id"]
        path = delivery / f"{take_id}.wav"
        if not path.is_file(): continue
        entry = by_id.get(take_id, {})
        if entry.get("filename") != path.name: failures.append(f"{take_id}: manifest filename mismatch")
        digest = sha256(path)
        if entry.get("sha256") != digest: failures.append(f"{take_id}: SHA-256 mismatch or absent")
        try:
            info = probe(path)
            if info.get("codec_name") != EXPECTED_CODEC: failures.append(f"{take_id}: codec must be pcm_s24le")
            if int(info.get("sample_rate", 0)) != EXPECTED_RATE: failures.append(f"{take_id}: sample rate must be 48000 Hz")
            if int(info.get("channels", 0)) != 1: failures.append(f"{take_id}: audio must be mono")
            met = metrics(path, int(row["word_count"]))
            if met["clipped_samples"]: failures.append(f"{take_id}: clipped samples detected")
            if met["peak_dbfs"] > MAX_PEAK_DBFS: failures.append(f"{take_id}: peak exceeds {MAX_PEAK_DBFS} dBFS")
            wpm = met.get("estimated_wpm")
            if wpm is None: failures.append(f"{take_id}: no speech detected above -45 dBFS")
            elif wpm < 80 or wpm > 200: failures.append(f"{take_id}: implausible active-speech rate {wpm} WPM")
            elif wpm < 120 or wpm > 170: warnings.append(f"{take_id}: review active-speech rate {wpm} WPM")
            if met["peak_dbfs"] < -18 or met["peak_dbfs"] > -3: warnings.append(f"{take_id}: raw peak outside preferred -18 to -3 dBFS window")
            observed.append({"take_id": take_id, "sha256": digest, **met})
        except Exception as exc:
            failures.append(f"{take_id}: decode/measurement failure: {exc}")
    room = delivery / str(manifest.get("room_tone_file", "ROOM_TONE.wav"))
    if room.is_file():
        try:
            info = probe(room)
            if info.get("codec_name") != EXPECTED_CODEC or int(info.get("sample_rate", 0)) != EXPECTED_RATE or int(info.get("channels", 0)) != 1:
                failures.append("room tone must be mono pcm_s24le at 48 kHz")
            met = metrics(room)
            if met["duration_seconds"] < 30: failures.append("room tone must be at least 30 seconds")
            if met["rms_dbfs"] < -80: failures.append("room tone appears to be digital silence")
            if met["clipped_samples"]: failures.append("room tone contains clipped samples")
        except Exception as exc:
            failures.append(f"room tone decode/measurement failure: {exc}")
    verdict = "PASS_INTAKE_ONLY" if not failures else "BLOCKED"
    return {"schema": "pilot-01-final-voice-delivery-validation-v1.0", "verdict": verdict,
            "release_authorized": False, "takes_expected": 91, "takes_validated": len(observed),
            "failures": failures, "warnings": warnings, "observed_takes": observed}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit-contract", action="store_true")
    parser.add_argument("--delivery-dir", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    rows = load_cues()
    emit_contract(rows)
    if args.emit_contract and not args.delivery_dir:
        print(json.dumps({"verdict": "PASS_CONTRACT_ONLY", "takes": 91, "contract_sha256": sha256(CONTRACT)}))
        return 0
    if not args.delivery_dir or not args.manifest:
        parser.error("--delivery-dir and --manifest are required for intake validation")
    result = validate(args.delivery_dir, args.manifest, rows)
    RESULT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("verdict", "takes_expected", "takes_validated", "failures", "warnings")}, indent=2))
    return 0 if result["verdict"] == "PASS_INTAKE_ONLY" else 2


if __name__ == "__main__":
    sys.exit(main())
