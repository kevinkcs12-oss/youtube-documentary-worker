#!/usr/bin/env python3
"""Build a deterministic, fail-closed companion for the Pilot 01 human review."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import zipfile
from pathlib import Path

EXPECTED_FILM_SHA256 = "8076d795c25f2fef0f377fd4abacaa72ad3a22b6f7dddb0cedfb47c7b413c580"
EXPECTED_TAKE_COUNT = 91
EXPECTED_CUE_END = "00:09:56.960"
EXPECTED_TIMELINE_SECONDS = 597.760
NAMED_PRONUNCIATIONS = {"T035": "Nielsen", "T062": "Spotify", "T065": "Spotify"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_warnings(path: Path) -> tuple[dict[str, float], list[str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("verdict") != "PASS_INTAKE_ONLY":
        raise ValueError("authoritative intake verdict is not PASS_INTAKE_ONLY")
    rates: dict[str, float] = {}
    global_warnings: list[str] = []
    for warning in payload.get("warnings", []):
        m = re.fullmatch(r"(T\d{3}): review active rate ([0-9.]+) WPM", warning)
        if m:
            rates[m.group(1)] = float(m.group(2))
        else:
            global_warnings.append(warning)
    return rates, global_warnings


def load_cues(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    ids = [r["take_id"] for r in rows]
    expected = [f"T{i:03d}" for i in range(1, EXPECTED_TAKE_COUNT + 1)]
    if ids != expected:
        raise ValueError("cue sheet must contain ordered T001-T091 exactly once")
    if rows[-1]["end"] != EXPECTED_CUE_END:
        raise ValueError(f"final spoken cue must end at {EXPECTED_CUE_END}")
    return rows


def write_scorecard(path: Path, cues: list[dict[str, str]], rates: dict[str, float]) -> None:
    fields = [
        "take_id", "chapter", "start", "end", "text", "review_priority",
        "machine_signal_only", "pronunciation_check", "human_verdict",
        "severity", "issue_type", "notes", "repair_authorized"
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in cues:
            take_id = row["take_id"]
            rate = rates.get(take_id)
            pronunciation = NAMED_PRONUNCIATIONS.get(take_id, "")
            signals = []
            if rate is not None:
                signals.append(f"active_span_rate={rate:.1f}_WPM")
            if pronunciation:
                signals.append("named_pronunciation")
            priority = "RECHECK_AFTER_CONTINUOUS_PASS" if signals else "CONTINUOUS_PASS"
            writer.writerow({
                "take_id": take_id,
                "chapter": row["chapter"],
                "start": row["start"],
                "end": row["end"],
                "text": row["text"],
                "review_priority": priority,
                "machine_signal_only": ";".join(signals),
                "pronunciation_check": pronunciation,
                "human_verdict": "",
                "severity": "",
                "issue_type": "",
                "notes": "",
                "repair_authorized": "NO",
            })


def write_hotspots(path: Path, cues: list[dict[str, str]], rates: dict[str, float]) -> None:
    by_id = {row["take_id"]: row for row in cues}
    ids = sorted(set(rates) | set(NAMED_PRONUNCIATIONS))
    fields = ["take_id", "start", "end", "reason", "text"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for take_id in ids:
            row = by_id[take_id]
            reasons = []
            if take_id in rates:
                reasons.append(f"active-span rate {rates[take_id]:.1f} WPM; listen, do not auto-fail")
            if take_id in NAMED_PRONUNCIATIONS:
                reasons.append(f"pronunciation: {NAMED_PRONUNCIATIONS[take_id]}")
            writer.writerow({"take_id": take_id, "start": row["start"], "end": row["end"], "reason": "; ".join(reasons), "text": row["text"]})


def write_card(path: Path, film_sha: str, warning_count: int, hotspot_count: int) -> None:
    path.write_text(f"""# Pilot 01 — Full-film perceptual review card v1.0

## Authority and scope

- Review exactly `Pilot_01_Kokoro_Full_Film_Review_DO_NOT_UPLOAD_v1.0.mp4`.
- Verified SHA-256: `{film_sha}`.
- Runtime: 09:57.760. Voice: Kevin-selected Kokoro `am_michael`.
- This card records human perception only. It cannot authorize upload, publication, release, or a final master.

## One-pass protocol

1. Watch the film once from 00:00 to 09:57.760 at normal speed, without opening the hotspot list. Use ordinary listening equipment and a comfortable fixed volume.
2. Mark only defects that are actually heard. Record the clock time immediately; do not infer a defect from a machine flag.
3. Classify each marked defect as `CRITICAL`, `MAJOR`, or `MINOR`:
   - `CRITICAL`: wrong/missing words, meaning changed, broken audio, or materially misleading pronunciation.
   - `MAJOR`: clearly synthetic cadence, distracting speed, or pause/visual mismatch that damages trust.
   - `MINOR`: noticeable but non-distracting imperfection.
4. After the uninterrupted pass, use the hotspot list only to recheck ambiguous moments. It contains {hotspot_count} takes derived from {warning_count} machine rate signals plus named-pronunciation checks.
5. Decide:
   - `PASS_PERCEPTUAL_REVIEW`: zero critical or major defects; minor issues are below the distraction threshold.
   - `TARGETED_REPAIR`: one or more localized critical/major defects; list exact take IDs. Regenerate only those takes and rerun the existing intake/conform/review chain.
   - `REJECT_VOICE`: only if defects are systemic across chapters and cannot plausibly be repaired take-by-take.

## Required named checks

- `T035` around 03:35.656 — “Jakob Nielsen”.
- `T062` around 06:32.145 — “Spotify”.
- `T065` around 07:01.689 — possessive “Spotify’s”.

## Closed fields

Human decision: `OPEN`

Final master authorized: `NO`  
Upload authorized: `NO`  
Publishable: `NO`  
Release authorized: `NO`
""", encoding="utf-8")


def deterministic_zip(output: Path, files: list[Path]) -> None:
    if output.exists():
        raise FileExistsError(output)
    info_time = (2026, 9, 19, 0, 0, 0)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(files, key=lambda p: p.name):
            info = zipfile.ZipInfo(path.name, info_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, path.read_bytes())


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--film", type=Path, required=True)
    p.add_argument("--cue-sheet", type=Path, required=True)
    p.add_argument("--intake-result", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    args = p.parse_args()
    film_sha = sha256(args.film)
    if film_sha != EXPECTED_FILM_SHA256:
        raise ValueError("full-film candidate SHA-256 mismatch")
    cues = load_cues(args.cue_sheet)
    rates, global_warnings = read_warnings(args.intake_result)
    if not {"Nielsen pronunciation requires human review", "Spotify pronunciation requires human review", "continuous naturalness review remains open"}.issubset(global_warnings):
        raise ValueError("required human-review warnings are missing")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    scorecard = args.output_dir / "Pilot_01_Full_Film_Perceptual_Review_Scorecard_v1.0.csv"
    hotspots = args.output_dir / "Pilot_01_Full_Film_Perceptual_Hotspots_v1.0.csv"
    card = args.output_dir / "Pilot_01_Full_Film_Perceptual_Review_Card_v1.0.md"
    manifest = args.output_dir / "Pilot_01_Full_Film_Perceptual_Review_Manifest_v1.0.json"
    write_scorecard(scorecard, cues, rates)
    write_hotspots(hotspots, cues, rates)
    write_card(card, film_sha, len(rates), len(set(rates) | set(NAMED_PRONUNCIATIONS)))
    manifest.write_text(json.dumps({
        "schema": "pilot-01-perceptual-review-companion-v1.0",
        "film_sha256": film_sha,
        "take_count": len(cues),
        "timeline_seconds": EXPECTED_TIMELINE_SECONDS,
        "final_spoken_cue_end": EXPECTED_CUE_END,
        "machine_rate_signal_count": len(rates),
        "named_pronunciation_take_count": len(NAMED_PRONUNCIATIONS),
        "human_decision": "OPEN",
        "verdict": "PASS_REVIEW_COMPANION_ONLY",
        "final_master_authorized": False,
        "upload_authorized": False,
        "publishable": False,
        "release_authorized": False,
        "files": {x.name: sha256(x) for x in (card, scorecard, hotspots)},
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    deterministic_zip(args.output_dir.parent / "Pilot_01_Full_Film_Perceptual_Review_Companion_Pack_v1.0.zip", [card, scorecard, hotspots, manifest])
    print(json.dumps({"verdict": "PASS_REVIEW_COMPANION_ONLY", "takes": len(cues), "hotspots": len(set(rates) | set(NAMED_PRONUNCIATIONS))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
