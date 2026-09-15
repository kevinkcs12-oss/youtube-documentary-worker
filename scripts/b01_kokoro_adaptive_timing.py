#!/usr/bin/env python3
from pathlib import Path
import re, json, math
import numpy as np
import soundfile as sf
from kokoro import KPipeline

SRC=Path("production/pilot-01/final-voice-recording-script-v1.0.md")
OUT=Path("dist/b01-kokoro-adaptive")
VOICE="am_michael"
TAKE_RE=re.compile(r"^### (T\d{3}) · cues .* · (\d\d):(\d\d):(\d\d\.\d{3})–(\d\d):(\d\d):(\d\d\.\d{3})$")
SPEEDS=[1.00,1.03,1.06,1.09,1.12,1.15]
MAX_SPEED=1.15
HEADROOM=0.10

def sec(h,m,s): return int(h)*3600+int(m)*60+float(s)
def parse():
    lines=SRC.read_text(encoding="utf-8").splitlines(); out=[]
    for i,line in enumerate(lines):
        m=TAKE_RE.match(line)
        if m:
            out.append((m.group(1),sec(m.group(2),m.group(3),m.group(4)),sec(m.group(5),m.group(6),m.group(7)),lines[i+2].strip()))
    assert len(out)==91
    return out

def synth(pipe,text,speed):
    chunks=[a for _,_,a in pipe(text,voice=VOICE,speed=speed,split_pattern=r"\n+")]
    return np.concatenate(chunks) if chunks else np.zeros(1,dtype=np.float32)

def main():
    OUT.mkdir(parents=True,exist_ok=True); pipe=KPipeline(lang_code="a"); rows=[]
    for take,start,end,text in parse():
        slot=end-start; chosen=None; attempts=[]
        for speed in SPEEDS:
            wav=synth(pipe,text,speed); dur=len(wav)/24000
            attempts.append({"speed":speed,"seconds":round(dur,3)})
            if dur <= slot-HEADROOM:
                chosen=(speed,wav,dur); break
        if chosen is None:
            speed,wav,dur=SPEEDS[-1],wav,dur
            status="NEEDS_SURGICAL_REVIEW"
        else:
            speed,wav,dur=chosen; status="PASS_ADAPTIVE"
        sf.write(OUT/f"{take}.wav",wav,24000,subtype="PCM_16")
        rows.append({"take":take,"slot_seconds":round(slot,3),"speed":speed,"generated_seconds":round(dur,3),
                     "remaining_headroom":round(slot-dur,3),"status":status,"attempts":attempts,"text":text})
    unresolved=[r for r in rows if r["status"]!="PASS_ADAPTIVE"]
    summary={"voice":VOICE,"takes":91,"max_speed":MAX_SPEED,"headroom_seconds":HEADROOM,
             "pass_count":91-len(unresolved),"unresolved_count":len(unresolved),
             "unresolved_takes":[r["take"] for r in unresolved]}
    (OUT/"manifest.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary))
if __name__=="__main__": main()
