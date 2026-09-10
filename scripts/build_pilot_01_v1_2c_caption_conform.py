#!/usr/bin/env python3
"""Build the exact 10:02 caption conform and editorial time map for Pilot 01.

The script deliberately preserves locked subtitle text where timing did not
change, replaces only the two rewritten narration regions, and regenerates the
shortened conclusion from its v1.2 source text.
"""

from __future__ import annotations

import csv
import re
import textwrap
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT_SRT = ROOT / "Pilot_01_Animatic_00m00_10m02_v1.2c_caption_conform.srt"
OUT_EDL = ROOT / "Pilot_01_v1.2c_Caption_Conform_EDL.csv"


@dataclass
class Cue:
    start: float
    end: float
    text: str
    source: str


def ts_to_seconds(value: str) -> float:
    h, m, rest = value.split(":")
    s, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def seconds_to_ts(value: float) -> str:
    millis = round(value * 1000)
    h, millis = divmod(millis, 3_600_000)
    m, millis = divmod(millis, 60_000)
    s, millis = divmod(millis, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{millis:03d}"


def parse_srt(path: Path, source: str) -> list[Cue]:
    raw = path.read_text(encoding="utf-8").strip()
    cues: list[Cue] = []
    for block in re.split(r"\n\s*\n", raw):
        lines = block.splitlines()
        timing_i = next(i for i, line in enumerate(lines) if " --> " in line)
        a, b = lines[timing_i].split(" --> ")
        cues.append(Cue(ts_to_seconds(a), ts_to_seconds(b), "\n".join(lines[timing_i + 1 :]), source))
    return cues


def shift(cues: list[Cue], offset: float) -> list[Cue]:
    return [Cue(c.start + offset, c.end + offset, c.text, c.source) for c in cues]


def words(text: str) -> int:
    return len(re.findall(r"\b[\w’'-]+\b", text, flags=re.UNICODE))


def caption_chunks(text: str, width: int = 42, max_lines: int = 2) -> list[str]:
    """Split prose into semantic, two-line caption chunks."""
    sentences = re.split(r"(?<=[.!?;:])\s+", " ".join(text.split()))
    chunks: list[str] = []
    for sentence in sentences:
        wrapped = textwrap.wrap(sentence, width=width, break_long_words=False, break_on_hyphens=False)
        # Avoid an unreadable sub-second orphan when a legacy sentence misses
        # the 42-character convention by a single character.
        if len(wrapped) == 3 and len(wrapped[-1]) < 8:
            relaxed = textwrap.wrap(sentence, width=width + 1, break_long_words=False, break_on_hyphens=False)
            if len(relaxed) == 2:
                wrapped = relaxed
        for i in range(0, len(wrapped), max_lines):
            chunks.append("\n".join(wrapped[i : i + max_lines]))
    return [c for c in chunks if c]


def timed_chunks(text: str, start: float, end: float, source: str) -> list[Cue]:
    chunks = caption_chunks(text)
    # Character-weighted allocation keeps reading speed stable when wrapping
    # leaves a short final phrase (word-weighting can create sub-second spikes).
    counts = [max(1, len(" ".join(c.splitlines()))) for c in chunks]
    total = sum(counts)
    cursor = start
    result: list[Cue] = []
    for i, (chunk, count) in enumerate(zip(chunks, counts)):
        cue_end = end if i == len(chunks) - 1 else cursor + (end - start) * count / total
        result.append(Cue(cursor, cue_end, chunk, source))
        cursor = cue_end
    return result


def normalize_cue(cue: Cue) -> list[Cue]:
    """Reflow legacy captions without changing their aggregate screen time."""
    return timed_chunks(" ".join(cue.text.splitlines()), cue.start, cue.end, cue.source)


def use_available_caption_gaps(cues: list[Cue], target_cps: float = 19.5) -> list[Cue]:
    """Use existing silent caption gaps to reduce inherited reading spikes."""
    adjusted: list[Cue] = []
    for i, cue in enumerate(cues):
        if i + 1 < len(cues):
            chars = len(" ".join(cue.text.splitlines()))
            needed_end = cue.start + chars / target_cps
            latest_end = cues[i + 1].start - 0.08
            if needed_end > cue.end and latest_end > cue.end:
                cue = Cue(cue.start, min(needed_end, latest_end), cue.text, cue.source)
        adjusted.append(cue)
    return adjusted


def rebalance_touching_pairs(cues: list[Cue], target_cps: float = 20.0) -> list[Cue]:
    """Rebalance a legacy hard boundary when the two-cue block is readable."""
    cues = list(cues)
    for i in range(len(cues) - 1):
        a, b = cues[i], cues[i + 1]
        chars_a = len(" ".join(a.text.splitlines()))
        chars_b = len(" ".join(b.text.splitlines()))
        cps_a = chars_a / (a.end - a.start)
        block_end = b.end
        if i + 2 < len(cues) and cues[i + 2].start - b.end > 0.16:
            block_end = cues[i + 2].start - 0.08
        block_cps = (chars_a + chars_b) / (block_end - a.start)
        if cps_a > 20 and abs(a.end - b.start) < 0.002 and a.source == b.source and block_cps <= target_cps:
            boundary = a.start + (block_end - a.start) * chars_a / (chars_a + chars_b)
            cues[i] = Cue(a.start, boundary, a.text, a.source)
            cues[i + 1] = Cue(boundary, block_end, b.text, b.source)
    return cues


def build() -> tuple[list[Cue], list[dict[str, str]]]:
    first = parse_srt(ROOT / "materialized/Pilot_01_Animatic_00m00_02m22_v1.2_rights_safe.srt", "locked first block")
    seq3 = parse_srt(next((ROOT / "subtitle_sources/seq3").glob("*.srt")), "sequence 3 v1.0")
    seq4 = parse_srt(next((ROOT / "subtitle_sources/seq4").glob("*.srt")), "sequence 4 v1.0")
    seq5 = parse_srt(next((ROOT / "subtitle_sources/seq5").glob("*.srt")), "sequence 5 v1.0")
    seq6 = parse_srt(next((ROOT / "subtitle_sources/seq6").glob("*.srt")), "sequence 6 v1.0")
    seq7 = parse_srt(next((ROOT / "subtitle_sources/seq7").glob("*.srt")), "sequence 7 v1.0")

    a_text = (ROOT / "Pilot_01_v1.2b_segment_A.txt").read_text(encoding="utf-8").strip()
    b_text = (ROOT / "Pilot_01_v1.2b_segment_B.txt").read_text(encoding="utf-8").strip()
    seq8_text = (ROOT / "work_retention2/Pilot_01_Scratch_Voice_Sequence_8_v1.2_retention_test.txt").read_text(encoding="utf-8").strip()

    cues: list[Cue] = []
    cues.extend(first)
    cues.extend(shift(seq3[:1], 142.0))
    cues.extend(timed_chunks(a_text, 148.0, 161.35, "replacement A v1.2c"))
    cues.extend(shift(seq3[4:], 136.0))
    cues.extend(shift(seq4, 212.0))
    cues.extend(shift(seq5, 289.0))
    cues.extend(shift(seq6[:2], 369.0))
    cues.extend(timed_chunks(b_text, 376.0, 428.765, "replacement B corrected v1.2c"))
    cues.extend(shift(seq6[20:], 359.0))
    cues.extend(shift(seq7, 444.0))

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", seq8_text) if p.strip()]
    speech_total = words(seq8_text) * 60 / 145
    gap = (82.0 - speech_total - 1.6) / (len(paragraphs) - 1)
    cursor = 520.8
    for i, paragraph in enumerate(paragraphs):
        duration = words(paragraph) * 60 / 145
        cues.extend(timed_chunks(paragraph, cursor, cursor + duration, "sequence 8 v1.2 retention conclusion"))
        cursor += duration
        if i < len(paragraphs) - 1:
            cursor += gap

    cues.sort(key=lambda c: (c.start, c.end))
    cues = [normalized for cue in cues for normalized in normalize_cue(cue)]
    cues = rebalance_touching_pairs(cues)
    cues = use_available_caption_gaps(cues)

    edl = [
        {"sequence": "1-2", "new_start": "00:00.000", "new_end": "02:22.000", "duration_s": "142.000", "source_treatment": "rights-safe first block v1.2 unchanged", "cumulative_shift_s": "0", "protected_claims": "opening thesis; museum/Axalta evidence; sample and causality caveats"},
        {"sequence": "3", "new_start": "02:22.000", "new_end": "03:32.000", "duration_s": "70.000", "source_treatment": "replace 02:28-02:42; remove six seconds; remainder shifted", "cumulative_shift_s": "-6", "protected_claims": "processing fluency remains probabilistic"},
        {"sequence": "4", "new_start": "03:32.000", "new_end": "04:49.000", "duration_s": "77.000", "source_treatment": "unchanged sequence shifted", "cumulative_shift_s": "-6", "protected_claims": "function versus aesthetic imitation; Jakob's Law boundary"},
        {"sequence": "5", "new_start": "04:49.000", "new_end": "06:09.000", "duration_s": "80.000", "source_treatment": "unchanged sequence shifted", "cumulative_shift_s": "-6", "protected_claims": "McDonald's case bounded; scale mechanism"},
        {"sequence": "6", "new_start": "06:09.000", "new_end": "07:24.000", "duration_s": "75.000", "source_treatment": "replace 06:16-07:10 with corrected 128-word passage; retain original close", "cumulative_shift_s": "-16", "protected_claims": "Spotify limited to music recommendation trade-off; loop labeled documentary model"},
        {"sequence": "7", "new_start": "07:24.000", "new_end": "08:40.000", "duration_s": "76.000", "source_treatment": "unchanged sequence shifted", "cumulative_shift_s": "-16", "protected_claims": "named counterexamples; no frequency inference"},
        {"sequence": "8", "new_start": "08:40.000", "new_end": "10:02.000", "duration_s": "82.000", "source_treatment": "retention conclusion v1.2 regenerated at native cadence", "cumulative_shift_s": "-20", "protected_claims": "case-linked synthesis; defensibility test; no universal causality"},
    ]
    return cues, edl


def validate(cues: list[Cue]) -> list[str]:
    errors: list[str] = []
    previous_end = 0.0
    for i, cue in enumerate(cues, 1):
        if cue.start < previous_end - 0.001:
            errors.append(f"cue {i}: overlap {cue.start:.3f} < {previous_end:.3f}")
        if cue.end <= cue.start:
            errors.append(f"cue {i}: non-positive duration")
        if cue.end > 602.0 + 0.001:
            errors.append(f"cue {i}: ends after master")
        lines = cue.text.splitlines()
        if len(lines) > 2:
            errors.append(f"cue {i}: {len(lines)} lines")
        if max(map(len, lines), default=0) > 43:
            errors.append(f"cue {i}: line over 43 chars")
        previous_end = max(previous_end, cue.end)
    return errors


def main() -> None:
    cues, edl = build()
    errors = validate(cues)
    if errors:
        raise SystemExit("\n".join(errors))
    with OUT_SRT.open("w", encoding="utf-8") as f:
        for i, cue in enumerate(cues, 1):
            f.write(f"{i}\n{seconds_to_ts(cue.start)} --> {seconds_to_ts(cue.end)}\n{cue.text}\n\n")
    with OUT_EDL.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=edl[0].keys())
        writer.writeheader()
        writer.writerows(edl)
    max_cps = max(sum(len(line) for line in c.text.splitlines()) / (c.end - c.start) for c in cues)
    print(f"cues={len(cues)} first={cues[0].start:.3f} last={cues[-1].end:.3f} max_cps={max_cps:.2f}")
    print(OUT_SRT)
    print(OUT_EDL)


if __name__ == "__main__":
    main()
