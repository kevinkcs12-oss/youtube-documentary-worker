#!/usr/bin/env python3
"""Fail-closed technical, lineage, rights and timing intake for Kokoro delivery."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
import wave
from decimal import Decimal
from pathlib import Path

RATE = 48000
EXPECTED_CODEC = "pcm_s24le"
EXPECTED_VOICE = "am_michael"
EXPECTED_MODEL = "hexgrad/Kokoro-82M"
EXPECTED_LICENSE = "Apache-2.0"
FILM_SECONDS = Decimal("597.760")
MIN_HEADROOM = Decimal("0.099")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def seconds(ts: str) -> Decimal:
    h, m, s = ts.split(":")
    return Decimal(h) * 3600 + Decimal(m) * 60 + Decimal(s)


def probe(path: Path) -> dict:
    data = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "a:0",
        "-show_entries", "stream=codec_name,sample_rate,channels,bits_per_raw_sample,duration",
        "-of", "json", str(path),
    ], text=True))
    streams = data.get("streams", [])
    if len(streams) != 1:
        raise ValueError("exactly one audio stream required")
    return streams[0]


def pcm_metrics(path: Path) -> dict:
    raw = subprocess.check_output(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path), "-f", "s24le", "-ac", "1", "-ar", str(RATE), "-"])
    if not raw or len(raw) % 3:
        raise ValueError("decoded PCM is empty or unaligned")
    peak = 0
    clipped = 0
    sumsq = 0.0
    active_first = active_last = None
    threshold = int(((1 << 23) - 1) * 10 ** (-45 / 20))
    for i in range(0, len(raw), 3):
        v = raw[i] | (raw[i + 1] << 8) | (raw[i + 2] << 16)
        if v & 0x800000: v -= 1 << 24
        a = abs(v); peak = max(peak, a); clipped += a >= (1 << 23) - 2; sumsq += float(v) * v
        if a >= threshold:
            idx = i // 3
            if active_first is None: active_first = idx
            active_last = idx
    n = len(raw) // 3
    scale = float((1 << 23) - 1)
    return {
        "samples": n, "duration_seconds": n / RATE,
        "peak_dbfs": 20 * math.log10(max(peak / scale, 1e-12)),
        "rms_dbfs": 20 * math.log10(max(math.sqrt(sumsq / n) / scale, 1e-12)),
        "clipped_samples": clipped,
        "active_seconds": 0 if active_first is None else (active_last - active_first + 1) / RATE,
    }


def validate(delivery: Path) -> dict:
    failures: list[str] = []
    warnings: list[str] = []
    manifest_path = delivery / "Pilot_01_Kokoro_Delivery_Manifest_v1.0.json"
    cue_path = delivery / "Pilot_01_Kokoro_Cue_Sheet_v1.0.csv"
    contract_path = delivery / "Pilot_01_Kokoro_Delivery_Contract_v1.0.csv"
    lineage_path = delivery / "Pilot_01_Kokoro_Delivery_Lineage_v1.0.csv"
    license_path = delivery / "Pilot_01_Kokoro_License_Provenance_v1.0.json"
    takes_dir = delivery / "takes"
    for p in (manifest_path, cue_path, contract_path, lineage_path, license_path):
        if not p.is_file(): failures.append(f"missing control file: {p.name}")
    if failures:
        return {"verdict":"BLOCKED","failures":failures,"warnings":warnings,"release_authorized":False,"publishable":False}
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("schema") != "pilot-01-kokoro-canonical-delivery-v1.0": failures.append("manifest schema mismatch")
    if manifest.get("selected_voice") != EXPECTED_VOICE: failures.append("selected voice mismatch")
    if manifest.get("selection_basis") != "Kevin blind review — candidate 2": failures.append("voice selection basis mismatch")
    if manifest.get("broad_voice_search_closed") is not True: failures.append("broad voice search must remain closed")
    if manifest.get("global_speed_change") is not False: failures.append("global speed change is forbidden")
    if (manifest.get("model"), manifest.get("model_license")) != (EXPECTED_MODEL, EXPECTED_LICENSE): failures.append("model identity/license mismatch")
    if manifest.get("paid_credits_used") is not False: failures.append("paid-credit declaration must be false")
    if manifest.get("capture") != {"dry":True,"music_present":False,"sample_rate_hz":RATE,"bit_depth":24,"channels":1}: failures.append("capture declaration mismatch")
    if manifest.get("release_authorized") is not False or manifest.get("publishable") is not False: failures.append("intake must not claim release authority")
    for p, key in ((cue_path,"cue_sheet_sha256"),(contract_path,"contract_sha256"),(lineage_path,"lineage_sha256"),(license_path,"license_provenance_sha256")):
        if manifest.get(key) != sha256(p): failures.append(f"{key} mismatch")
    license_data = json.loads(license_path.read_text())
    if (license_data.get("model"), license_data.get("voice"), license_data.get("license")) != (EXPECTED_MODEL,EXPECTED_VOICE,EXPECTED_LICENSE): failures.append("license provenance identity mismatch")
    if license_data.get("publication_authority") is not False: failures.append("license record improperly claims publication authority")

    cues = list(csv.DictReader(cue_path.open()))
    contracts = list(csv.DictReader(contract_path.open()))
    lineage = list(csv.DictReader(lineage_path.open()))
    entries = manifest.get("takes", [])
    expected = [f"T{i:03d}" for i in range(1,92)]
    for name, rows, key in (("cue",cues,"take_id"),("contract",contracts,"take_id"),("lineage",lineage,"take_id"),("manifest",entries,"take_id")):
        if len(rows) != 91 or [r.get(key) for r in rows] != expected: failures.append(f"{name} must contain ordered T001-T091")
    by_contract = {r["take_id"]:r for r in contracts}
    by_lineage = {r["take_id"]:r for r in lineage}
    by_entry = {r.get("take_id"):r for r in entries if isinstance(r,dict)}
    previous_end = Decimal("0")
    observed = []
    for cue in cues:
        take = cue["take_id"]; start=seconds(cue["start"]); end=seconds(cue["end"])
        if start < previous_end or end <= start or end > FILM_SECONDS: failures.append(f"{take}: invalid revised cue window")
        previous_end = end
        path = takes_dir / f"{take}.wav"
        if not path.is_file(): failures.append(f"{take}: missing WAV"); continue
        digest = sha256(path)
        if by_entry.get(take,{}).get("sha256") != digest: failures.append(f"{take}: manifest SHA-256 mismatch")
        if by_lineage.get(take,{}).get("output_sha256") != digest: failures.append(f"{take}: lineage output SHA-256 mismatch")
        if by_entry.get(take,{}).get("source_sha256") != by_lineage.get(take,{}).get("source_sha256"): failures.append(f"{take}: source lineage mismatch")
        if by_contract.get(take,{}).get("text_sha256") != by_lineage.get(take,{}).get("text_sha256"): failures.append(f"{take}: text lineage mismatch")
        try:
            info=probe(path)
            if info.get("codec_name")!=EXPECTED_CODEC or int(info.get("sample_rate",0))!=RATE or int(info.get("channels",0))!=1: failures.append(f"{take}: must be mono PCM24/48 kHz")
            met=pcm_metrics(path); window=end-start
            if Decimal(str(met["duration_seconds"])) > window-MIN_HEADROOM: failures.append(f"{take}: exceeds revised window/headroom")
            if met["clipped_samples"]: failures.append(f"{take}: clipped samples")
            if met["active_seconds"] <= 0: failures.append(f"{take}: no speech detected")
            words=int(cue["word_count"]); wpm=words*60/max(met["active_seconds"],0.001)
            # Active-span WPM overstates pace on short, pause-led phrases. It is
            # a review signal, not a proxy for perceived naturalness. The hard
            # gate catches only extreme values; all 170+ cases stay visible.
            if wpm < 80 or wpm > 240: failures.append(f"{take}: implausible active rate {wpm:.1f} WPM")
            elif wpm < 120 or wpm > 170: warnings.append(f"{take}: review active rate {wpm:.1f} WPM")
            observed.append({"take_id":take,"sha256":digest,"duration_seconds":round(met["duration_seconds"],6),"window_seconds":float(window),"headroom_seconds":round(float(window)-met["duration_seconds"],6),"active_wpm":round(wpm,1),"peak_dbfs":round(met["peak_dbfs"],2)})
        except Exception as exc: failures.append(f"{take}: decode/measurement failure: {exc}")
    floor = takes_dir / str(manifest.get("synthetic_floor_file",""))
    if not floor.is_file() or manifest.get("synthetic_floor_sha256") != (sha256(floor) if floor.is_file() else None): failures.append("synthetic floor missing or hash mismatch")
    elif (m:=pcm_metrics(floor))["duration_seconds"] < 30 or m["rms_dbfs"] < -80 or m["clipped_samples"]: failures.append("synthetic floor format/level invalid")
    actual={p.name for p in takes_dir.glob("*.wav")}; expected_files={f"T{i:03d}.wav" for i in range(1,92)}|{"SYNTHETIC_FLOOR.wav"}
    if actual != expected_files: failures.append("delivery WAV set is not exactly 91 takes plus synthetic floor")
    if manifest.get("pronunciation_review") != {"Nielsen":"OPEN","Spotify":"OPEN"}: failures.append("pronunciation review must remain explicitly OPEN")
    if manifest.get("naturalness_review") != "OPEN": failures.append("naturalness review must remain OPEN")
    if not failures:
        warnings.extend(["Nielsen pronunciation requires human review", "Spotify pronunciation requires human review", "continuous naturalness review remains open"])
    return {
        "schema":"pilot-01-kokoro-canonical-intake-v1.0", "verdict":"PASS_INTAKE_ONLY" if not failures else "BLOCKED",
        "voice":EXPECTED_VOICE, "takes_expected":91, "takes_validated":len(observed), "failures":failures, "warnings":warnings,
        "pronunciation_review_open":True, "naturalness_review_open":True, "release_authorized":False, "publishable":False,
        "manifest_sha256":sha256(manifest_path), "cue_sheet_sha256":sha256(cue_path), "contract_sha256":sha256(contract_path),
        "observed_takes":observed,
    }


def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--delivery",type=Path,required=True); p.add_argument("--result",type=Path,required=True); a=p.parse_args()
    result=validate(a.delivery); a.result.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:result[k] for k in ("verdict","takes_expected","takes_validated","failures","warnings")},indent=2))
    return 0 if result["verdict"]=="PASS_INTAKE_ONLY" else 2


if __name__=="__main__": sys.exit(main())
