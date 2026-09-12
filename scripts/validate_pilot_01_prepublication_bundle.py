#!/usr/bin/env python3
"""Deterministic, offline pre-publication validator for Pilot 01."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "Pilot_01_Prepublication_Validation_v1.0.json"

FILES = {
    "master": ROOT / "Pilot_01_Animatic_Scratch_Voice_00m00_09m57.760_v1.2g_progressive_focus.mp4",
    "captions": ROOT / "restored/Pilot_01_Animatic_00m00_09m57.760_v1.2f_pacing_trim.srt",
    "description": ROOT / "Pilot_01_Description_With_Sources_v1.0.txt",
    "sources": ROOT / "Pilot_01_Final_Source_Registry_v1.0.csv",
    "metadata": ROOT / "Pilot_01_Metadata_Variants_v1.0.csv",
    "metrics": ROOT / "Pilot_01_Launch_Metrics_Log_v1.0.csv",
    "voice_review": ROOT / "Pilot_01_Free_Voice_Blind_Audition_Review_Pack_v1.0.zip",
}
THUMBS = sorted((ROOT / "pilot_01_launch_instrumentation_v1_0").glob("*.png"))
EXPECTED_MASTER_SHA = "3d1643246c066f377e841edc0f8653fec3c1bd9910d15151fb53732039259d27"
EXPECTED_CHAPTERS = ["00:00", "01:04", "02:22", "03:30", "04:45", "06:04", "07:19", "08:35"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def probe(path: Path) -> dict:
    p = subprocess.run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,nb_frames,duration",
        "-show_entries", "format=duration", "-of", "json", str(path)
    ], check=True, capture_output=True, text=True)
    return json.loads(p.stdout)


def srt_time(value: str) -> float:
    h, m, rest = value.split(":")
    s, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def check(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "status": "PASS" if passed else "FAIL", "detail": detail}


def main() -> int:
    checks = []
    manifest = []
    for role, path in FILES.items():
        exists = path.is_file()
        checks.append(check(f"required_file:{role}", exists, str(path.relative_to(ROOT))))
        if exists:
            manifest.append({"role": role, "path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path)})

    if not all(p.is_file() for p in FILES.values()):
        OUT.write_text(json.dumps({"overall": "FAIL", "checks": checks}, indent=2) + "\n")
        return 1

    master = probe(FILES["master"])
    stream = master["streams"][0]
    duration = float(master["format"]["duration"])
    frames = int(stream.get("nb_frames", 0))
    master_sha = sha256(FILES["master"])
    checks += [
        check("master_duration", abs(duration - 597.760) < 0.001, f"{duration:.3f}s"),
        check("master_frames", frames == 14944, str(frames)),
        check("master_geometry", (stream["width"], stream["height"]) == (1920, 1080), f"{stream['width']}x{stream['height']}"),
        check("master_fps", stream["r_frame_rate"] == "25/1", stream["r_frame_rate"]),
        check("master_identity", master_sha == EXPECTED_MASTER_SHA, master_sha),
    ]

    text = FILES["captions"].read_text(encoding="utf-8")
    blocks = [b for b in re.split(r"\n\s*\n", text.strip()) if b]
    cues = []
    max_lines = 0
    max_cps = 0.0
    for block in blocks:
        lines = block.splitlines()
        times = re.match(r"(\d\d:\d\d:\d\d,\d{3}) --> (\d\d:\d\d:\d\d,\d{3})", lines[1])
        if not times:
            raise ValueError(f"Bad SRT block: {block[:80]}")
        start, end = map(srt_time, times.groups())
        payload = lines[2:]
        cps = len(" ".join(payload)) / max(end - start, 0.001)
        max_lines = max(max_lines, len(payload))
        max_cps = max(max_cps, cps)
        cues.append((start, end))
    overlaps = sum(1 for left, right in zip(cues, cues[1:]) if left[1] > right[0])
    checks += [
        check("captions_count", len(cues) == 161, str(len(cues))),
        check("captions_no_overlap", overlaps == 0, f"{overlaps} overlaps"),
        check("captions_two_lines", max_lines <= 2, f"max {max_lines}"),
        check("captions_cps", max_cps <= 20.001, f"max {max_cps:.2f}"),
        check("captions_within_master", cues[-1][1] <= duration, f"last end {cues[-1][1]:.3f}s"),
    ]

    description = FILES["description"].read_text(encoding="utf-8")
    chapter_times = re.findall(r"(?m)^(\d\d:\d\d) ", description)
    checks += [
        check("description_chapters", chapter_times == EXPECTED_CHAPTERS, ",".join(chapter_times)),
        check("description_bounded_claim", "not that everything is literally identical" in description, "scope disclaimer present"),
        check("description_visual_rights", "do not grant visual-use rights" in description, "rights disclaimer present"),
    ]

    with FILES["sources"].open(newline="", encoding="utf-8") as f:
        sources = list(csv.DictReader(f))
    families = {r["id"] for r in sources if re.fullmatch(r"F[1-7]", r["id"])}
    counters = {r["id"] for r in sources if re.fullmatch(r"CE[1-3]", r["id"])}
    checks += [
        check("source_rows", len(sources) == 10, str(len(sources))),
        check("evidence_families", families == {f"F{i}" for i in range(1, 8)}, ",".join(sorted(families))),
        check("counterexamples", counters == {"CE1", "CE2", "CE3"}, ",".join(sorted(counters))),
        check("source_boundaries", all(r["claim_not_supported"].strip() for r in sources), "all 10 rows bounded"),
    ]

    with FILES["metadata"].open(newline="", encoding="utf-8") as f:
        variants = list(csv.DictReader(f))
    checks.append(check("metadata_variants", len(variants) == 3 and {r["cell"] for r in variants} == {"A", "B", "C"}, f"{len(variants)} variants"))

    with FILES["metrics"].open(newline="", encoding="utf-8") as f:
        windows = [r["read_window"] for r in csv.DictReader(f)]
    checks.append(check("measurement_windows", windows == ["6h", "24h", "72h", "7d", "14d_or_completion"], ",".join(windows)))

    for path in THUMBS:
        info = probe(path)["streams"][0]
        ok = (info["width"], info["height"]) == (1280, 720)
        checks.append(check(f"thumbnail:{path.name}", ok, f"{info['width']}x{info['height']}"))
        manifest.append({"role": "thumbnail", "path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path)})
    checks.append(check("thumbnail_count", len(THUMBS) == 3, str(len(THUMBS))))

    with zipfile.ZipFile(FILES["voice_review"]) as zf:
        bad = zf.testzip()
        mp3s = [n for n in zf.namelist() if n.lower().endswith(".mp3")]
    checks += [
        check("voice_pack_integrity", bad is None, bad or "zip CRC clean"),
        check("voice_candidate_count", len(mp3s) == 4, f"{len(mp3s)} MP3 candidates"),
    ]

    failed = [c for c in checks if c["status"] != "PASS"]
    result = {
        "schema": "pilot-01-prepublication-validation-v1.0",
        "overall": "PASS_WITH_HUMAN_GATES" if not failed else "FAIL",
        "technical_checks": {"passed": len(checks) - len(failed), "failed": len(failed)},
        "human_gates": [
            "retain_or_revert_v1.2g_progressive_focus",
            "select_final_voice_after_blind_listening",
            "authorize_music_or_no-music_mix_and_external_publication",
        ],
        "checks": checks,
        "manifest": manifest,
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"overall": result["overall"], "passed": len(checks) - len(failed), "failed": len(failed), "output": str(OUT)}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
