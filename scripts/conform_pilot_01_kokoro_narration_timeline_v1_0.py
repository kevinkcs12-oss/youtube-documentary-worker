#!/usr/bin/env python3
"""Deterministically conform the validated Kokoro delivery to 597.760 seconds."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import wave
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

RATE=48000
WIDTH=3
TARGET=Decimal("597.760")
TARGET_SAMPLES=int(TARGET*RATE)


def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()


def samples(ts:str)->int:
    h,m,s=ts.split(":")
    return int(((Decimal(h)*3600+Decimal(m)*60+Decimal(s))*RATE).to_integral_value(rounding=ROUND_HALF_UP))


def conform(delivery:Path,validator:Path,outdir:Path)->dict:
    outdir.mkdir(parents=True,exist_ok=True)
    intake_path=outdir/"Pilot_01_Kokoro_Canonical_Intake_Recheck_v1.0.json"
    subprocess.run([sys.executable,str(validator),"--delivery",str(delivery),"--result",str(intake_path)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    intake=json.loads(intake_path.read_text())
    if intake.get("verdict")!="PASS_INTAKE_ONLY" or intake.get("takes_validated")!=91 or intake.get("failures"):
        raise ValueError("canonical Kokoro intake did not pass 91/91")
    if intake.get("release_authorized") is not False or intake.get("publishable") is not False:
        raise ValueError("intake improperly claims release authority")
    manifest_path=delivery/"Pilot_01_Kokoro_Delivery_Manifest_v1.0.json"
    cue_path=delivery/"Pilot_01_Kokoro_Cue_Sheet_v1.0.csv"
    manifest=json.loads(manifest_path.read_text())
    if manifest.get("cue_sheet_sha256")!=sha256(cue_path): raise ValueError("cue-sheet lineage mismatch")
    by={x["take_id"]:x for x in manifest["takes"]}
    cues=list(csv.DictReader(cue_path.open()))
    if [r["take_id"] for r in cues] != [f"T{i:03d}" for i in range(1,92)]: raise ValueError("cue sheet is not ordered T001-T091")
    output=outdir/"Pilot_01_Kokoro_Narration_Timeline_597p760s_DO_NOT_PUBLISH_v1.0.wav"
    placements=outdir/"Pilot_01_Kokoro_Narration_Placements_v1.0.csv"
    zero=b"\0"*(RATE*WIDTH)
    rows=[]
    with wave.open(str(output),"wb") as w:
        w.setnchannels(1);w.setsampwidth(WIDTH);w.setframerate(RATE)
        cursor=0
        for cue in cues:
            take=cue["take_id"]; start=samples(cue["start"]); end=samples(cue["end"])
            if start<cursor or end<=start: raise ValueError(f"{take}: invalid placement window")
            gap=start-cursor
            while gap:
                n=min(gap,RATE);w.writeframesraw(zero[:n*WIDTH]);gap-=n
            path=delivery/"takes"/f"{take}.wav"
            if sha256(path)!=by[take]["sha256"]: raise ValueError(f"{take}: WAV hash changed after intake")
            with wave.open(str(path),"rb") as src:
                if (src.getnchannels(),src.getsampwidth(),src.getframerate())!=(1,WIDTH,RATE): raise ValueError(f"{take}: format changed after intake")
                take_samples=src.getnframes(); audio=src.readframes(take_samples)
            capacity=end-start
            if take_samples>capacity: raise ValueError(f"{take}: exceeds revised window")
            w.writeframesraw(audio)
            pad=capacity-take_samples
            while pad:
                n=min(pad,RATE);w.writeframesraw(zero[:n*WIDTH]);pad-=n
            cursor=end
            rows.append({"take_id":take,"start_sample":start,"end_sample":end,"window_samples":capacity,"take_samples":take_samples,"silence_pad_samples":capacity-take_samples,"take_sha256":by[take]["sha256"],"time_stretch":"NONE"})
        tail=TARGET_SAMPLES-cursor
        if tail<0: raise ValueError("timeline exceeds 597.760 seconds")
        while tail:
            n=min(tail,RATE);w.writeframesraw(zero[:n*WIDTH]);tail-=n
    with wave.open(str(output),"rb") as w:
        if (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes())!=(1,WIDTH,RATE,TARGET_SAMPLES): raise ValueError("conformed WAV format/sample count mismatch")
    with placements.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    result={
        "schema":"pilot-01-kokoro-narration-conform-v1.0","verdict":"PASS_NARRATION_CONFORM_ONLY",
        "voice":"am_michael","takes_placed":len(rows),"duration_seconds":float(TARGET),"samples":TARGET_SAMPLES,
        "sample_rate_hz":RATE,"bit_depth":24,"channels":1,"time_stretch_applied":False,"music_present":False,
        "pronunciation_review_open":True,"naturalness_review_open":True,"publishable":False,"release_authorized":False,
        "validator_sha256":sha256(validator),"intake_recheck_sha256":sha256(intake_path),"manifest_sha256":sha256(manifest_path),
        "cue_sheet_sha256":sha256(cue_path),"output_sha256":sha256(output),"placements_sha256":sha256(placements),
        "intake_warnings":intake.get("warnings",[]),
    }
    result_path=outdir/"Pilot_01_Kokoro_Narration_Conform_Result_v1.0.json"
    result_path.write_text(json.dumps(result,indent=2)+"\n")
    return result


def main()->int:
    root=Path(__file__).resolve().parent
    p=argparse.ArgumentParser();p.add_argument("--delivery",type=Path,required=True);p.add_argument("--validator",type=Path,default=root/"validate_pilot_01_kokoro_canonical_delivery_v1_0.py");p.add_argument("--outdir",type=Path,required=True);a=p.parse_args()
    try:
        result=conform(a.delivery,a.validator,a.outdir);print(json.dumps(result,indent=2));return 0
    except Exception as exc:
        a.outdir.mkdir(parents=True,exist_ok=True);blocked={"schema":"pilot-01-kokoro-narration-conform-v1.0","verdict":"BLOCKED","error":str(exc),"publishable":False,"release_authorized":False};(a.outdir/"Pilot_01_Kokoro_Narration_Conform_Result_v1.0.json").write_text(json.dumps(blocked,indent=2)+"\n");print(json.dumps(blocked,indent=2),file=sys.stderr);return 2


if __name__=="__main__":sys.exit(main())
