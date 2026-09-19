#!/usr/bin/env python3
"""Materialize the selected Kokoro repair plan as a complete fail-closed delivery.

This builder performs no synthesis and no global speed change. It selects only
previously generated, hash-addressed source WAVs; trims outer padding using the
same conservative activity rule as the timing map; converts to dry mono
PCM24/48 kHz; revises only explicitly allocated cue boundaries; and records
full per-take lineage. It grants no release or publication authority.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import array
import random
import re
import struct
import subprocess
import wave
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

RATE = 48000
SOURCE_RATE = 24000
THRESHOLD_DBFS = -45.0
KEEP_HEAD = Decimal("0.080")
KEEP_TAIL = Decimal("0.120")
HEADROOM = Decimal("0.100")
FILM_SECONDS = Decimal("597.760")
MICRO = {"T061": ("T062", Decimal("0.043")), "T074": ("T075", Decimal("0.056")), "T088": ("T089", Decimal("0.066"))}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def seconds(ts: str) -> Decimal:
    h, m, s = ts.split(":")
    return Decimal(h) * 3600 + Decimal(m) * 60 + Decimal(s)


def timestamp(value: Decimal) -> str:
    value = value.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    h = int(value // 3600)
    value -= Decimal(h * 3600)
    m = int(value // 60)
    s = value - Decimal(m * 60)
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w’'-]+\b", text, flags=re.UNICODE))


def active_bounds(path: Path) -> tuple[int, int, int]:
    with wave.open(str(path), "rb") as w:
        if (w.getnchannels(), w.getsampwidth(), w.getframerate()) != (1, 2, SOURCE_RATE):
            raise ValueError(f"{path.name}: expected mono PCM16/24 kHz source")
        total = w.getnframes()
        raw = w.readframes(total)
    values = array.array("h")
    values.frombytes(raw)
    frame = max(1, round(SOURCE_RATE * 0.010))
    threshold = 32767.0 * 10 ** (THRESHOLD_DBFS / 20)
    active = []
    for i in range(0, total, frame):
        chunk = values[i:i + frame]
        rms = math.sqrt(sum(float(x) * x for x in chunk) / max(1, len(chunk)))
        if rms >= threshold:
            active.append((i, min(total, i + frame)))
    if not active:
        raise ValueError(f"{path.name}: no activity above {THRESHOLD_DBFS} dBFS")
    first, last = active[0][0], active[-1][1]
    start = max(0, first - int(KEEP_HEAD * SOURCE_RATE))
    end = min(total, last + int(KEEP_TAIL * SOURCE_RATE))
    return start, end, total


def convert_trimmed(source: Path, output: Path) -> dict[str, object]:
    start, end, total = active_bounds(source)
    subprocess.run([
        "ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(source),
        "-af", f"atrim=start_sample={start}:end_sample={end},asetpts=PTS-STARTPTS,aresample={RATE}",
        "-ac", "1", "-ar", str(RATE), "-c:a", "pcm_s24le", str(output),
    ], check=True)
    with wave.open(str(output), "rb") as w:
        if (w.getnchannels(), w.getsampwidth(), w.getframerate()) != (1, 3, RATE):
            raise ValueError(f"{output.name}: output is not mono PCM24/48 kHz")
        samples = w.getnframes()
    return {
        "source_samples": total,
        "trim_start_sample_24k": start,
        "trim_end_sample_24k": end,
        "output_samples_48k": samples,
        "duration_seconds": round(samples / RATE, 6),
    }


def write_synthetic_floor(path: Path) -> None:
    rng = random.Random(20260919)
    frames = RATE * 30
    amplitude = 6500  # approximately -62 dBFS RMS for signed 24-bit PCM
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(3)
        w.setframerate(RATE)
        chunk = bytearray()
        for i in range(frames):
            sample = int((rng.random() * 2 - 1) * amplitude)
            if sample < 0:
                sample += 1 << 24
            chunk.extend((sample & 0xFF, (sample >> 8) & 0xFF, (sample >> 16) & 0xFF))
            if len(chunk) >= RATE * 3:
                w.writeframesraw(bytes(chunk))
                chunk = bytearray()
        if chunk:
            w.writeframesraw(bytes(chunk))


def main() -> int:
    root = Path(__file__).resolve().parent
    p = argparse.ArgumentParser()
    p.add_argument("--cue-v1", type=Path, default=root / "Pilot_01_Final_Voice_Cue_Sheet_v1.0.csv")
    p.add_argument("--map", type=Path, default=root / "timing-recovery-v1.1/Pilot_01_Kokoro_Timing_Recovery_Map_v1.1.csv")
    p.add_argument("--raw-dir", type=Path, default=root / "b01-kokoro-full")
    p.add_argument("--adaptive-dir", type=Path, default=root / "b01-kokoro-adaptive")
    p.add_argument("--repair-dir", type=Path, default=root / "kokoro-repair-selection-v1.0/takes")
    p.add_argument("--repair-manifest", type=Path, default=root / "kokoro-repair-selection-v1.0/Pilot_01_Kokoro_Repair_Selection_Manifest_v1.0.csv")
    p.add_argument("--out", type=Path, default=root / "kokoro-canonical-delivery-v1.0")
    args = p.parse_args()

    out = args.out
    takes_dir = out / "takes"
    takes_dir.mkdir(parents=True, exist_ok=True)
    cues = list(csv.DictReader(args.cue_v1.open(encoding="utf-8")))
    timing = {r["take"]: r for r in csv.DictReader(args.map.open(encoding="utf-8"))}
    repairs = {r["take"]: r for r in csv.DictReader(args.repair_manifest.open(encoding="utf-8"))}
    expected = [f"T{i:03d}" for i in range(1, 92)]
    if [r["take_id"] for r in cues] != expected or sorted(timing) != expected:
        raise ValueError("cue sheet and timing map must contain ordered T001-T091")
    if len(repairs) != 17:
        raise ValueError("repair manifest must contain exactly 17 selected takes")

    revised: list[dict[str, str]] = []
    lineage: list[dict[str, object]] = []
    boundaries: dict[str, list[Decimal]] = {}
    for cue in cues:
        take = cue["take_id"]
        row = timing[take]
        remedy = row["recommended_remedy"]
        if take in repairs:
            source = args.repair_dir / f"{take}.wav"
            source_class = repairs[take]["action"]
            speed = Decimal(repairs[take]["speed"])
            text = repairs[take]["text"]
            before = after = Decimal("0")
        elif remedy == "SAFE_TRIM_PLUS_UNIQUE_SILENCE_AT_ADAPTIVE_SPEED":
            source = args.adaptive_dir / f"{take}.wav"
            source_class = "ADAPTIVE_EXISTING"
            speed = Decimal(row["adaptive_speed"])
            text = cue["text"]
            before = Decimal(row["adaptive_from_before"])
            after = Decimal(row["adaptive_from_after"])
        elif remedy == "SAFE_TRIM_PLUS_UNIQUE_SILENCE_AT_1_00":
            source = args.raw_dir / f"{take}.wav"
            source_class = "RAW_NATURAL_SPEED"
            speed = Decimal("1.00")
            text = cue["text"]
            before = Decimal(row["raw_from_before"])
            after = Decimal(row["raw_from_after"])
        else:
            raise ValueError(f"{take}: unresolved remedy is not in repair selection")
        if not source.is_file():
            raise FileNotFoundError(source)
        boundaries[take] = [seconds(cue["start"]) - before, seconds(cue["end"]) + after]
        output = takes_dir / f"{take}.wav"
        metrics = convert_trimmed(source, output)
        lineage.append({
            "take_id": take, "filename": output.name, "voice": "am_michael",
            "source_class": source_class, "selected_speed": float(speed),
            "source_path_class": source.parent.name, "source_sha256": sha256(source),
            "output_sha256": sha256(output), "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "text": text, **metrics,
        })

    for borrower, (donor, amount) in MICRO.items():
        # Borrow from the immediately following donor by moving their shared boundary.
        if boundaries[borrower][1] != boundaries[donor][0]:
            raise ValueError(f"{borrower}/{donor}: micro-transfer requires a shared boundary")
        boundaries[borrower][1] += amount
        boundaries[donor][0] += amount

    by_take = {r["take_id"]: r for r in lineage}
    previous_end = Decimal("0")
    for cue in cues:
        take = cue["take_id"]
        start, end = boundaries[take]
        if start < previous_end or end <= start or end > FILM_SECONDS:
            raise ValueError(f"{take}: revised window invalid or overlapping")
        duration = Decimal(str(by_take[take]["duration_seconds"]))
        window = end - start
        if duration > window - HEADROOM:
            raise ValueError(f"{take}: materialized duration {duration} exceeds revised window {window} minus headroom")
        text = str(by_take[take]["text"])
        revised_row = dict(cue)
        revised_row.update({
            "start": timestamp(start), "end": timestamp(end),
            "available_seconds": f"{window:.3f}", "word_count": str(word_count(text)),
            "effective_wpm": f"{Decimal(word_count(text) * 60) / max(duration, Decimal('0.001')):.1f}",
            "text": text, "recording_status": "KOKORO_CANONICAL_DELIVERY_V1_0",
        })
        revised.append(revised_row)
        by_take[take]["revised_start"] = timestamp(start)
        by_take[take]["revised_end"] = timestamp(end)
        by_take[take]["window_seconds"] = float(window)
        by_take[take]["headroom_seconds"] = float(window - duration)
        previous_end = end

    cue_path = out / "Pilot_01_Kokoro_Cue_Sheet_v1.0.csv"
    with cue_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(cues[0]))
        w.writeheader(); w.writerows(revised)

    floor = takes_dir / "SYNTHETIC_FLOOR.wav"
    write_synthetic_floor(floor)
    lineage_path = out / "Pilot_01_Kokoro_Delivery_Lineage_v1.0.csv"
    with lineage_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lineage[0]))
        w.writeheader(); w.writerows(lineage)

    contract_fields = ["take_id", "filename", "sequence", "cue_first", "cue_last", "word_count", "text_sha256", "source_class", "selected_speed", "source_sha256", "start", "end", "window_seconds"]
    contract_path = out / "Pilot_01_Kokoro_Delivery_Contract_v1.0.csv"
    cue_by = {r["take_id"]: r for r in revised}
    with contract_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=contract_fields); w.writeheader()
        for row in lineage:
            cue = cue_by[row["take_id"]]
            w.writerow({
                "take_id": row["take_id"], "filename": row["filename"], "sequence": cue["sequence"],
                "cue_first": cue["cue_first"], "cue_last": cue["cue_last"], "word_count": cue["word_count"],
                "text_sha256": row["text_sha256"], "source_class": row["source_class"],
                "selected_speed": row["selected_speed"], "source_sha256": row["source_sha256"],
                "start": cue["start"], "end": cue["end"], "window_seconds": cue["available_seconds"],
            })

    license_path = out / "Pilot_01_Kokoro_License_Provenance_v1.0.json"
    license_data = {
        "model": "hexgrad/Kokoro-82M", "voice": "am_michael", "license": "Apache-2.0",
        "primary_source": "https://huggingface.co/hexgrad/Kokoro-82M",
        "verified_date": "2026-09-19", "scope_note": "Model card states Apache-licensed weights and production deployment is permitted.",
        "publication_authority": False,
    }
    license_path.write_text(json.dumps(license_data, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "schema": "pilot-01-kokoro-canonical-delivery-v1.0",
        "selected_voice": "am_michael", "selection_basis": "Kevin blind review — candidate 2",
        "selection_state_reference": "B01 verified user directive / 2026-09-19 durable reconciliation",
        "broad_voice_search_closed": True, "global_speed_change": False,
        "model": "hexgrad/Kokoro-82M", "model_license": "Apache-2.0",
        "model_source": license_data["primary_source"], "paid_credits_used": False,
        "capture": {"dry": True, "music_present": False, "sample_rate_hz": RATE, "bit_depth": 24, "channels": 1},
        "synthetic_floor_file": floor.name, "synthetic_floor_sha256": sha256(floor),
        "pronunciation_review": {"Nielsen": "OPEN", "Spotify": "OPEN"},
        "naturalness_review": "OPEN", "publishable": False, "release_authorized": False,
        "cue_sheet_sha256": sha256(cue_path), "contract_sha256": sha256(contract_path),
        "lineage_sha256": sha256(lineage_path), "license_provenance_sha256": sha256(license_path),
        "takes": [{"take_id": r["take_id"], "filename": r["filename"], "sha256": r["output_sha256"], "source_sha256": r["source_sha256"]} for r in lineage],
    }
    manifest_path = out / "Pilot_01_Kokoro_Delivery_Manifest_v1.0.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    summary = {
        "schema": "pilot-01-kokoro-canonical-delivery-build-v1.0", "verdict": "PASS_BUILD_ONLY",
        "takes": len(lineage), "raw_natural_speed": sum(r["source_class"] == "RAW_NATURAL_SPEED" for r in lineage),
        "adaptive_existing": sum(r["source_class"] == "ADAPTIVE_EXISTING" for r in lineage),
        "surgical_rewrites": sum(r["source_class"] == "SURGICAL_REWRITE" for r in lineage),
        "editorial_boundary_transfers": sum(r["source_class"] == "EDITORIAL_BOUNDARY_TRANSFER" for r in lineage),
        "max_speed": max(float(r["selected_speed"]) for r in lineage), "min_headroom_seconds": min(float(r["headroom_seconds"]) for r in lineage),
        "cue_sheet_sha256": sha256(cue_path), "contract_sha256": sha256(contract_path),
        "manifest_sha256": sha256(manifest_path), "lineage_sha256": sha256(lineage_path),
        "intake_passed": False, "conform_passed": False, "publishable": False, "release_authorized": False,
    }
    (out / "Pilot_01_Kokoro_Canonical_Delivery_Build_Summary_v1.0.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
