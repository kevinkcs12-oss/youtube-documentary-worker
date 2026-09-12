#!/usr/bin/env python3
"""Generate the canonical full-film voice recording session pack from v1.2f SRT."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRT = ROOT / "restored/Pilot_01_Animatic_00m00_09m57.760_v1.2f_pacing_trim.srt"
SCRIPT = ROOT / "Pilot_01_Final_Voice_Recording_Script_v1.0.md"
CUES = ROOT / "Pilot_01_Final_Voice_Cue_Sheet_v1.0.csv"
PRON = ROOT / "Pilot_01_Final_Voice_Pronunciation_Flags_v1.0.csv"
MANIFEST = ROOT / "Pilot_01_Final_Voice_Session_Manifest_v1.0.json"

CHAPTERS = [
    (0.0, "S1", "The feeling of sameness"),
    (64.0, "S2", "What the evidence can—and cannot—show"),
    (142.0, "S3", "Why familiarity feels easier"),
    (210.0, "S4", "Interfaces and identities"),
    (285.0, "S5", "Architecture at scale"),
    (364.0, "S6", "The feedback loop"),
    (439.0, "S7", "The exceptions that matter"),
    (515.0, "S8", "A more defensible answer"),
]

FLAGS = [
    ("Axalta", "brand / company name", "verify against first-party pronunciation before recording"),
    ("Mihajlović", "author surname", "verify with an authoritative speaker or author source; do not anglicize silently"),
    ("Reber", "author surname", "confirm preferred author pronunciation"),
    ("Winkielman", "author surname", "confirm preferred author pronunciation"),
    ("Jakob's Law", "named UX principle", "use the established English name; confirm Jakob Nielsen name pronunciation"),
    ("Nielsen", "surname / organization", "confirm English rendering before recording"),
    ("Spotify", "brand", "standard English brand pronunciation"),
    ("Porsche", "brand", "avoid one-syllable English shortcut unless editorially chosen"),
    ("McDonald's", "brand", "standard English brand pronunciation"),
    ("Material Design 3", "design system", "say the numeral as ‘three’"),
    ("IBM Carbon", "design system", "say I-B-M, then Carbon"),
]


def seconds(raw: str) -> float:
    h, m, tail = raw.split(":")
    s, ms = tail.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def tc(value: float) -> str:
    ms = round(value * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def chapter_for(start: float) -> tuple[str, str]:
    chosen = CHAPTERS[0]
    for chapter in CHAPTERS:
        if chapter[0] <= start:
            chosen = chapter
    return chosen[1], chosen[2]


def main() -> None:
    blocks = [b for b in re.split(r"\n\s*\n", SRT.read_text(encoding="utf-8").strip()) if b]
    cues = []
    for block in blocks:
        lines = block.splitlines()
        match = re.fullmatch(r"(\d\d:\d\d:\d\d,\d{3}) --> (\d\d:\d\d:\d\d,\d{3})", lines[1])
        if not match:
            raise ValueError(f"Invalid SRT block {lines[0]}")
        start, end = map(seconds, match.groups())
        text = " ".join(lines[2:]).replace("  ", " ").strip()
        sequence, chapter = chapter_for(start)
        cues.append({"cue": int(lines[0]), "start": start, "end": end, "text": text,
                     "sequence": sequence, "chapter": chapter})
    if len(cues) != 161 or cues[-1]["end"] != 596.960:
        raise ValueError("Canonical SRT identity check failed")
    if any(a["end"] > b["start"] for a, b in zip(cues, cues[1:])):
        raise ValueError("Overlapping cues")

    takes = []
    current = []
    for cue in cues:
        if current and cue["sequence"] != current[-1]["sequence"]:
            takes.append(current); current = []
        current.append(cue)
        text = " ".join(c["text"] for c in current)
        words = re.findall(r"\b[\w’'-]+\b", text)
        if re.search(r"[.!?][\"']?$", cue["text"]) and (len(words) >= 8 or len(current) >= 3):
            takes.append(current); current = []
    if current:
        takes.append(current)

    rows = []
    for index, group in enumerate(takes, 1):
        text = " ".join(c["text"] for c in group)
        word_count = len(re.findall(r"\b[\w’'-]+\b", text))
        duration = group[-1]["end"] - group[0]["start"]
        effective_wpm = word_count / duration * 60
        rows.append({
            "take_id": f"T{index:03d}", "sequence": group[0]["sequence"],
            "chapter": group[0]["chapter"], "cue_first": group[0]["cue"],
            "cue_last": group[-1]["cue"], "start": tc(group[0]["start"]),
            "end": tc(group[-1]["end"]), "available_seconds": f"{duration:.3f}",
            "word_count": word_count, "effective_wpm": f"{effective_wpm:.1f}",
            "timing_flag": "TIGHT_REVIEW" if effective_wpm > 165 else ("EXPANSIVE_WINDOW" if effective_wpm < 100 else "NORMAL"),
            "text": text, "recording_status": "PENDING_HUMAN_VOICE_SELECTION",
        })

    with CUES.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)

    md = [
        "# Pilot 01 — Final voice recording script v1.0", "",
        "> Canonical text derived mechanically from the 161-cue v1.2f SRT. Do not rewrite during recording. The v1.2f timing authority remains unchanged.", "",
        "## Session rules", "",
        "- Record at 48 kHz / 24-bit mono with no music, reverb, denoising artefacts, time stretch, or mastering limiter.",
        "- Preserve wording. Mark pickups by take ID; do not compress delivery merely to fill a subtitle window.",
        "- Deliver one continuous full-timeline narration conform plus isolated pickups.",
        "- Target natural documentary cadence: 138–146 words/minute overall. Chapter/take WPM below is a timing diagnostic, not an instruction to rush.",
        "- Resolve every pronunciation flag before the corresponding take.", "",
    ]
    last_sequence = None
    for row in rows:
        if row["sequence"] != last_sequence:
            md += [f"## {row['sequence']} — {row['chapter']}", ""]
            last_sequence = row["sequence"]
        md += [f"### {row['take_id']} · cues {row['cue_first']}–{row['cue_last']} · {row['start']}–{row['end']}", "",
               row["text"], "",
               f"Timing reference: {row['available_seconds']} s · {row['word_count']} words · {row['effective_wpm']} effective WPM", ""]
    SCRIPT.write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")

    full_text = " ".join(c["text"] for c in cues)
    with PRON.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["term", "function", "instruction", "present_in_canonical_text", "status"])
        for term, function, instruction in FLAGS:
            present = term.casefold() in full_text.casefold()
            w.writerow([term, function, instruction, "YES" if present else "NO", "VERIFY_BEFORE_RECORDING" if present else "REFERENCE_ONLY"])

    sequence_stats = []
    for start, sid, title in CHAPTERS:
        subset = [c for c in cues if c["sequence"] == sid]
        words = len(re.findall(r"\b[\w’'-]+\b", " ".join(c["text"] for c in subset)))
        sequence_stats.append({"sequence": sid, "title": title, "cue_count": len(subset), "word_count": words,
                               "first_cue_start": tc(subset[0]["start"]), "last_cue_end": tc(subset[-1]["end"])})
    result = {
        "schema": "pilot-01-final-voice-session-pack-v1.0", "status": "READY_FOR_HUMAN_VOICE_AFTER_SELECTION",
        "source_srt": str(SRT.relative_to(ROOT)), "source_srt_sha256": sha(SRT),
        "cue_count": len(cues), "take_count": len(rows),
        "word_count": len(re.findall(r"\b[\w’'-]+\b", full_text)),
        "target_speech_seconds_at_142_wpm": round(len(re.findall(r"\b[\w’'-]+\b", full_text)) / 142 * 60, 3),
        "timeline_pause_budget_at_142_wpm": round(597.760 - len(re.findall(r"\b[\w’'-]+\b", full_text)) / 142 * 60, 3),
        "tight_take_ids": [r["take_id"] for r in rows if r["timing_flag"] == "TIGHT_REVIEW"],
        "expansive_take_ids": [r["take_id"] for r in rows if r["timing_flag"] == "EXPANSIVE_WINDOW"],
        "first_cue_start": tc(cues[0]["start"]), "last_cue_end": tc(cues[-1]["end"]),
        "sequence_stats": sequence_stats,
        "gates": ["blind_voice_selection", "pronunciation_verification", "human_performance_direction", "final_audio_conform", "publication_authorization"],
    }
    MANIFEST.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
