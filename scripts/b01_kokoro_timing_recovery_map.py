#!/usr/bin/env python3
"""Map exact Kokoro take timing and conservatively allocatable timeline silence.

This is a planning/audit tool only. It never edits, stretches, or regenerates audio.
"""
from __future__ import annotations

import argparse, csv, hashlib, json, math, re, wave
from pathlib import Path

TAKE_RE = re.compile(r"^### (T\d{3}) · cues .* · (\d\d):(\d\d):(\d\d\.\d{3})–(\d\d):(\d\d):(\d\d\.\d{3})$")
FILM_SECONDS = 597.760
HEADROOM = 0.100
FRAME_MS = 10
ACTIVE_DBFS = -45.0
KEEP_HEAD = 0.080
KEEP_TAIL = 0.120

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()

def seconds(h: str, m: str, s: str) -> float:
    return int(h) * 3600 + int(m) * 60 + float(s)

def parse_script(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    out, chapter = [], ""
    for i, line in enumerate(lines):
        if line.startswith("## "):
            chapter = line[3:]
        m = TAKE_RE.match(line)
        if m:
            out.append({
                "take": m.group(1), "chapter": chapter,
                "start": seconds(*m.groups()[1:4]),
                "end": seconds(*m.groups()[4:]),
                "text": lines[i + 2].strip(),
            })
    if len(out) != 91:
        raise ValueError(f"expected 91 takes, got {len(out)}")
    return out

def wav_activity(path: Path):
    with wave.open(str(path), "rb") as w:
        if w.getnchannels() != 1 or w.getsampwidth() != 2:
            raise ValueError(f"{path}: expected mono PCM16")
        rate, n = w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    import array
    samples = array.array("h")
    samples.frombytes(raw)
    if samples.itemsize != 2:
        raise RuntimeError("unexpected sample width")
    frame = max(1, round(rate * FRAME_MS / 1000))
    threshold = 32767.0 * 10 ** (ACTIVE_DBFS / 20.0)
    active = []
    for i in range(0, n, frame):
        chunk = samples[i:i + frame]
        rms = math.sqrt(sum(float(x) * x for x in chunk) / max(1, len(chunk)))
        if rms >= threshold:
            active.append((i, min(n, i + frame)))
    if not active:
        raise ValueError(f"{path}: no active speech detected")
    first, last = active[0][0], active[-1][1]
    leading, trailing = first / rate, (n - last) / rate
    keep_start = max(0.0, leading - KEEP_HEAD)
    keep_end = max(0.0, trailing - KEEP_TAIL)
    return {
        "sample_rate": rate, "samples": n, "duration": n / rate,
        "leading_silence": leading, "trailing_silence": trailing,
        "safe_trim_lead": keep_start, "safe_trim_tail": keep_end,
        "safe_duration": (n / rate) - keep_start - keep_end,
    }

def recoverable_gap(gap: float, crosses_chapter: bool):
    if crosses_chapter or gap < 0.200:
        return 0.0, gap, "LOCK_CHAPTER_OR_MICRO_PAUSE"
    reserve = 0.250 if gap < 0.800 else (0.450 if gap < 1.500 else 0.750)
    return max(0.0, gap - reserve), min(gap, reserve), "PROVISIONAL_INTRA_CHAPTER"

def allocate(rows, gap_available, demand_key, prefix):
    allocations = [{"before": 0.0, "after": 0.0} for _ in rows]
    demands = {i: max(0.0, rows[i][demand_key]) for i in range(len(rows))}
    # Smallest repairs first maximizes the number of takes cleared, while every gap is consumed once.
    for i in sorted(demands, key=lambda k: (demands[k], k)):
        need = demands[i]
        if need <= 1e-9:
            continue
        for gi, side in ((i - 1, "before"), (i, "after")):
            if gi < 0 or gi >= len(gap_available):
                continue
            used = min(need, gap_available[gi])
            gap_available[gi] -= used
            need -= used
            allocations[i][side] += used
            if need <= 1e-9:
                break
        rows[i][f"{prefix}_residual"] = max(0.0, need)
    for i in range(len(rows)):
        rows[i][f"{prefix}_from_before"] = allocations[i]["before"]
        rows[i][f"{prefix}_from_after"] = allocations[i]["after"]
        rows[i].setdefault(f"{prefix}_residual", demands[i])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", type=Path, required=True)
    ap.add_argument("--raw-dir", type=Path, required=True)
    ap.add_argument("--adaptive-dir", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows = parse_script(args.script)
    raw_manifest = {x["take"]: x for x in json.loads((args.raw_dir / "manifest.json").read_text())}
    adaptive_manifest = {x["take"]: x for x in json.loads((args.adaptive_dir / "manifest.json").read_text())}
    for r in rows:
        raw = wav_activity(args.raw_dir / f"{r['take']}.wav")
        adaptive = wav_activity(args.adaptive_dir / f"{r['take']}.wav")
        r.update({
            "slot_seconds": r["end"] - r["start"],
            "raw_duration": raw["duration"],
            "raw_leading_silence": raw["leading_silence"],
            "raw_trailing_silence": raw["trailing_silence"],
            "raw_safe_duration": raw["safe_duration"],
            "raw_overflow": max(0.0, raw["duration"] - (r["end"] - r["start"])),
            "raw_safe_demand": max(0.0, raw["safe_duration"] - ((r["end"] - r["start"]) - HEADROOM)),
            "adaptive_speed": float(adaptive_manifest[r["take"]]["speed"]),
            "adaptive_duration": adaptive["duration"],
            "adaptive_safe_duration": adaptive["safe_duration"],
            "adaptive_safe_demand": max(0.0, adaptive["safe_duration"] - ((r["end"] - r["start"]) - HEADROOM)),
            "raw_sha256": sha256(args.raw_dir / f"{r['take']}.wav"),
            "adaptive_sha256": sha256(args.adaptive_dir / f"{r['take']}.wav"),
        })
    gaps = []
    for i in range(len(rows) - 1):
        gap = rows[i + 1]["start"] - rows[i]["end"]
        rec, reserve, rule = recoverable_gap(gap, rows[i]["chapter"] != rows[i + 1]["chapter"])
        gaps.append({"left": rows[i]["take"], "right": rows[i + 1]["take"], "gap": gap,
                     "recoverable": rec, "reserved": reserve, "rule": rule})
    gap_available = [g["recoverable"] for g in gaps]
    allocate(rows, gap_available, "raw_safe_demand", "raw")
    # Adaptive pass reuses only silence that the natural-speed-first phase did not already consume.
    for r in rows:
        r["adaptive_post_raw_demand"] = 0.0 if r.get("raw_residual", r["raw_safe_demand"]) <= 1e-9 else r["adaptive_safe_demand"]
    allocate(rows, gap_available, "adaptive_post_raw_demand", "adaptive")
    for r in rows:
        raw_res = r.get("raw_residual", r["raw_safe_demand"])
        adapt_res = r.get("adaptive_residual", r["adaptive_post_raw_demand"])
        if raw_res <= 1e-6:
            remedy = "SAFE_TRIM_PLUS_UNIQUE_SILENCE_AT_1_00"
        elif adapt_res <= 1e-6:
            remedy = "SAFE_TRIM_PLUS_UNIQUE_SILENCE_AT_ADAPTIVE_SPEED"
        elif r["adaptive_speed"] < 1.15:
            remedy = "REGENERATE_AT_TESTED_ADAPTIVE_SPEED_AND_RECHECK"
        else:
            remedy = "SURGICAL_TEXT_OR_EDITORIAL_REVIEW"
        r["recommended_remedy"] = remedy
        r["residual_seconds"] = adapt_res if raw_res > 1e-6 else 0.0
    fields = [
        "take","chapter","start","end","slot_seconds","raw_duration","raw_leading_silence","raw_trailing_silence",
        "raw_safe_duration","raw_overflow","raw_safe_demand","raw_from_before","raw_from_after","raw_residual",
        "adaptive_speed","adaptive_duration","adaptive_safe_duration","adaptive_safe_demand",
        "adaptive_from_before","adaptive_from_after","adaptive_residual","recommended_remedy","residual_seconds",
        "raw_sha256","adaptive_sha256","text"
    ]
    with (args.out_dir / "Pilot_01_Kokoro_Timing_Recovery_Map_v1.0.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 6) if isinstance(v, float) else v) for k, v in r.items()})
    with (args.out_dir / "Pilot_01_Kokoro_Neighboring_Silence_Map_v1.0.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["left","right","gap","recoverable","reserved","rule","remaining_unallocated"]); w.writeheader()
        for g, remain in zip(gaps, gap_available):
            w.writerow({**{k:(round(v,6) if isinstance(v,float) else v) for k,v in g.items()}, "remaining_unallocated":round(remain,6)})
    counts = {}
    for r in rows: counts[r["recommended_remedy"]] = counts.get(r["recommended_remedy"], 0) + 1
    unresolved = [r for r in rows if r["residual_seconds"] > 1e-6]
    summary = {
        "schema":"pilot-01-kokoro-timing-recovery-map-v1.0", "voice":"am_michael", "takes":91,
        "film_seconds":FILM_SECONDS, "headroom_seconds":HEADROOM,
        "activity_detection":{"frame_ms":FRAME_MS,"threshold_dbfs":ACTIVE_DBFS,"keep_head_seconds":KEEP_HEAD,"keep_tail_seconds":KEEP_TAIL},
        "timeline_silence_total":round(sum(g["gap"] for g in gaps) + rows[0]["start"] + (FILM_SECONDS-rows[-1]["end"]),6),
        "timeline_silence_conservatively_recoverable":round(sum(g["recoverable"] for g in gaps),6),
        "remedy_counts":counts,
        "residual_review_count":len(unresolved),
        "residual_review_takes":[r["take"] for r in unresolved],
        "residual_review_seconds_total":round(sum(r["residual_seconds"] for r in unresolved),6),
        "limitations":[
            "Intra-chapter silence reserves are conservative planning rules, not editorial approval.",
            "Chapter-boundary gaps and sub-200ms micro-pauses are fully locked.",
            "No audio was edited, stretched, regenerated, conformed, mixed, or approved for release."
        ],
        "source_hashes":{"script":sha256(args.script),"raw_manifest":sha256(args.raw_dir/'manifest.json'),"adaptive_manifest":sha256(args.adaptive_dir/'manifest.json')}
    }
    (args.out_dir / "Pilot_01_Kokoro_Timing_Recovery_Summary_v1.0.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
