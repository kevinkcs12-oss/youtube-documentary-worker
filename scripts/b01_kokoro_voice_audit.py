#!/usr/bin/env python3
from pathlib import Path
import json
import soundfile as sf
from kokoro import KPipeline

TEXT = """Walk through almost any new part of a city and something feels strangely familiar.
The cars arrive in the same narrow palette. The cafés share pale wood, black metal, and a careful amount of green.
The logos use clean letters with space around them. New apartment blocks repeat the same grids of glass, concrete, and muted cladding.
It can feel as if all of it came from one invisible catalog.
But that first impression creates a problem. The world does not literally look the same."""

VOICES = ["am_adam", "am_michael", "bm_george", "bm_lewis"]

def main():
    out = Path("dist/voice-kokoro")
    out.mkdir(parents=True, exist_ok=True)
    pipe = KPipeline(lang_code="a")
    rows=[]
    for idx, voice in enumerate(VOICES, start=1):
        chunks=[]
        for _, _, audio in pipe(TEXT, voice=voice, speed=1.0, split_pattern=r"\n+"):
            chunks.append(audio)
        import numpy as np
        wav=np.concatenate(chunks) if chunks else np.zeros(1,dtype=np.float32)
        path=out/f"candidate_{idx}.wav"
        sf.write(path, wav, 24000, subtype="PCM_16")
        rows.append({"candidate": idx, "voice": voice, "samples": int(len(wav)), "seconds": round(len(wav)/24000,3)})
    (out/"manifest_private.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    (out/"review_instructions.txt").write_text(
        "Blind review: listen to candidate_1.wav through candidate_4.wav without opening manifest_private.json. "
        "Reject any voice that sounds robotic, synthetic, over-acted, or obviously unsuitable for a premium documentary.\n",
        encoding="utf-8")
if __name__=="__main__":
    main()
