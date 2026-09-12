#!/usr/bin/env python3
"""Build a deterministic, anonymous Flite audition pack without network or paid calls."""

from __future__ import annotations

import ctypes
import csv
import hashlib
import json
import subprocess
from pathlib import Path


class CstVoice(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_void_p),
        ("features", ctypes.c_void_p),
        ("ffunctions", ctypes.c_void_p),
        ("utt_init", ctypes.c_void_p),
    ]


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "pilot_01_free_voice_audition_v1_0"
RAW = OUT / "raw"
WAV = OUT / "wav"
MP3 = OUT / "review"

EXCERPTS = {
    "01_HOOK_SCOPE": (
        "Walk through almost any new part of a city and something feels strangely familiar. "
        "The cars arrive in the same narrow palette. The cafes share pale wood, black metal, and green. "
        "Logos use clean letters. New apartment blocks repeat grids of glass, concrete, and muted cladding. "
        "It can feel as if all of it came from one invisible catalog. But the world does not literally look the same."
    ),
    "02_NUMBERS_BOUNDARY": (
        "In twenty twenty-five: white twenty-nine percent, black twenty-three percent, gray twenty-two percent, "
        "and silver seven percent. White, black, and gray together: seventy-four percent. Add silver, and the "
        "grayscale share reaches eighty-one percent. In Europe, gray alone led at twenty-six percent. That proves "
        "dominance. It does not prove why. Several forces may contribute. The report does not isolate or rank them."
    ),
    "03_MODEL_BOUNDARY": (
        "Spotify researchers describe balancing familiarity and similarity against discovery. The platform does "
        "not simply maximize sameness; it manages competing objectives. Algorithms did not invent visual "
        "convergence. They can accelerate a loop that already exists. This loop is our model, not Spotify's finding."
    ),
    "04_FINAL_LANDING": (
        "The world does not have to become identical for difference to become harder to defend. And perhaps that "
        "is the hidden cost of frictionless design. We notice fewer bad surprises, but also fewer good ones. "
        "Sameness is rarely imposed all at once. It accumulates, one reasonable decision at a time. And difference "
        "returns the same way: one defensible exception at a time."
    ),
}

# Deterministic blind labels. Keep this mapping out of the listener review folder.
CANDIDATES = {
    # duration_stretch was calibrated from a rejected native-rate pass so every
    # retained candidate lands near 142 WPM before encoding.
    "Candidate_A": ("slt", "/usr/lib/x86_64-linux-gnu/libflite_cmu_us_slt.so.2.2", 1.106),
    "Candidate_B": ("rms", "/usr/lib/x86_64-linux-gnu/libflite_cmu_us_rms.so.2.2", 0.992),
    "Candidate_C": ("awb", "/usr/lib/x86_64-linux-gnu/libflite_cmu_us_awb.so.2.2", 1.063),
    "Candidate_D": ("kal16", "/usr/lib/x86_64-linux-gnu/libflite_cmu_us_kal16.so.2.2", 1.126),
}


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def ffprobe(path: Path) -> dict:
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-show_entries", "stream=codec_name,sample_rate,channels", "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    )
    return json.loads(p.stdout)


def synthesize(text: str, voice_key: str, voice_lib: str, duration_stretch: float, target: Path) -> None:
    target.unlink(missing_ok=True)
    ctypes.CDLL("libflite.so.2.2", mode=ctypes.RTLD_GLOBAL).flite_init()
    lib = ctypes.CDLL(voice_lib, mode=ctypes.RTLD_GLOBAL)
    register = getattr(lib, f"register_cmu_us_{voice_key}")
    register.argtypes = [ctypes.c_char_p]
    register.restype = ctypes.c_void_p
    voice = register(None)
    core = ctypes.CDLL("libflite.so.2.2", mode=ctypes.RTLD_GLOBAL)
    core.flite_feat_set_float.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_float]
    core.flite_feat_set_float.restype = None
    voice_struct = ctypes.cast(voice, ctypes.POINTER(CstVoice)).contents
    core.flite_feat_set_float(
        voice_struct.features,
        b"duration_stretch",
        ctypes.c_float(duration_stretch),
    )
    core.flite_text_to_speech.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.c_char_p]
    core.flite_text_to_speech.restype = ctypes.c_float
    seconds = core.flite_text_to_speech(text.encode("utf-8"), voice, str(target).encode("utf-8"))
    if seconds <= 0 or not target.exists():
        raise RuntimeError(f"Flite synthesis failed for {voice_key}: {seconds}")


def main() -> None:
    for folder in (RAW, WAV, MP3):
        folder.mkdir(parents=True, exist_ok=True)

    silence = RAW / "silence_1p5s.wav"
    run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", "1.5", "-c:a", "pcm_s16le", str(silence))

    rows = []
    mapping = []
    for blind, (voice_key, voice_lib, duration_stretch) in CANDIDATES.items():
        segments = []
        for idx, (excerpt_id, text) in enumerate(EXCERPTS.items(), 1):
            raw = RAW / f"{blind}_{excerpt_id}_native.wav"
            normalized = RAW / f"{blind}_{excerpt_id}_48k.wav"
            normalized_tmp = Path("/tmp") / f"b01_{blind}_{idx}_48k.wav"
            synthesize(text, voice_key, voice_lib, duration_stretch, raw)
            normalized.unlink(missing_ok=True)
            normalized_tmp.unlink(missing_ok=True)
            run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(raw),
                "-af", "loudnorm=I=-20:TP=-3:LRA=7", "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(normalized_tmp))
            normalized_tmp.replace(normalized)
            segments.append(normalized)

        concat = RAW / f"{blind}_concat.txt"
        concat.write_text("\n".join(f"file '{p.as_posix()}'\nfile 'silence_1p5s.wav'" for p in segments) + "\n", encoding="utf-8")
        final_wav = WAV / f"{blind}_Blind_Audition_v1.0.wav"
        final_wav.unlink(missing_ok=True)
        run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
            "-ar", "48000", "-ac", "1", "-c:a", "pcm_s24le", str(final_wav))
        final_mp3 = MP3 / f"{blind}_Blind_Audition_v1.0.mp3"
        final_mp3.unlink(missing_ok=True)
        run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(final_wav), "-c:a", "libmp3lame", "-b:a", "192k", str(final_mp3))
        run("ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(final_wav), "-f", "null", "-")
        run("ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(final_mp3), "-f", "null", "-")
        wav_meta = ffprobe(final_wav)
        mp3_meta = ffprobe(final_mp3)
        duration = float(wav_meta["format"]["duration"])
        mp3_duration = float(mp3_meta["format"]["duration"])
        if not 103.8 <= duration <= 104.2:
            raise RuntimeError(f"Unexpected audition duration for {blind}: {duration:.3f}s")
        if abs(mp3_duration - duration) > 0.1:
            raise RuntimeError(
                f"Container mismatch for {blind}: WAV={duration:.3f}s MP3={mp3_duration:.3f}s"
            )
        effective_wpm = 232 / (duration - 6.0) * 60
        rows.append({
            "candidate": blind,
            "duration_seconds": f"{duration:.3f}",
            "effective_wpm": f"{effective_wpm:.2f}",
            "wav_sha256": sha256(final_wav),
            "mp3_sha256": sha256(final_mp3),
        })
        mapping.append({"candidate": blind, "engine": "CMU Flite", "voice": voice_key, "voice_library": voice_lib, "duration_stretch": duration_stretch})

    with (OUT / "blind_manifest.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    (OUT / "sealed_candidate_mapping.json").write_text(json.dumps(mapping, indent=2) + "\n", encoding="utf-8")
    (OUT / "audition_texts.json").write_text(json.dumps(EXCERPTS, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "candidates": rows}, indent=2))


if __name__ == "__main__":
    main()
