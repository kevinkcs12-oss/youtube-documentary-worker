#!/usr/bin/env python3
"""Regenerate only the evidence-protected residual Kokoro takes."""
from pathlib import Path
import json, math, re
import numpy as np
import soundfile as sf
from kokoro import KPipeline

SRC=Path("production/pilot-01/final-voice-recording-script-v1.0.md")
OUT=Path("dist/b01-kokoro-surgical-v1.1")
VOICE="am_michael"
SPEEDS=[1.00,1.03,1.06,1.09,1.12,1.15]
HEADROOM=0.100
ACTIVE_DBFS=-45.0
KEEP_HEAD=0.080
KEEP_TAIL=0.120
TAKE_RE=re.compile(r"^### (T\d{3}) · cues .* · (\d\d):(\d\d):(\d\d\.\d{3})–(\d\d):(\d\d):(\d\d\.\d{3})$")
REWRITES={
"T023":"Avoiding rejection rather than earning love appears beyond cars.",
"T027":"Complexity creates interest and identity; familiarity can become boredom.",
"T037":"Navigation needs no tutorial. Familiar patterns can improve digital speed and accessibility.",
"T062":"Spotify researchers describe recommendation systems balancing familiarity, similarity, and discovery."
}

def sec(h,m,s): return int(h)*3600+int(m)*60+float(s)
def slots():
    out={}
    lines=SRC.read_text(encoding="utf-8").splitlines()
    for line in lines:
        m=TAKE_RE.match(line)
        if m: out[m.group(1)]=sec(*m.groups()[4:])-sec(*m.groups()[1:4])
    assert len(out)==91
    return out
def safe_duration(wav,rate=24000):
    frame=max(1,round(rate*0.010)); threshold=32767.0*10**(ACTIVE_DBFS/20.0)
    pcm=np.clip(wav,-1,1)*32767.0; active=[]
    for i in range(0,len(pcm),frame):
        chunk=pcm[i:i+frame]; rms=math.sqrt(float(np.mean(chunk*chunk))) if len(chunk) else 0
        if rms>=threshold: active.append((i,min(len(pcm),i+frame)))
    if not active: raise RuntimeError("no active speech")
    leading=active[0][0]/rate; trailing=(len(pcm)-active[-1][1])/rate
    removable=max(0,leading-KEEP_HEAD)+max(0,trailing-KEEP_TAIL)
    return len(wav)/rate-removable,leading,trailing
def main():
    OUT.mkdir(parents=True,exist_ok=True); pipe=KPipeline(lang_code="a"); windows=slots(); rows=[]
    for take,text in REWRITES.items():
        attempts=[]; chosen=None
        for speed in SPEEDS:
            chunks=[a for _,_,a in pipe(text,voice=VOICE,speed=speed,split_pattern=r"\n+")]
            wav=np.concatenate(chunks) if chunks else np.zeros(1,dtype=np.float32)
            safe,lead,tail=safe_duration(wav)
            attempts.append({"speed":speed,"container_seconds":round(len(wav)/24000,3),"safe_seconds":round(safe,3)})
            if safe<=windows[take]-HEADROOM:
                chosen=(speed,wav,safe,lead,tail); break
        if chosen is None: chosen=(SPEEDS[-1],wav,safe,lead,tail)
        speed,wav,safe,lead,tail=chosen
        sf.write(OUT/f"{take}.wav",wav,24000,subtype="PCM_16")
        rows.append({"take":take,"voice":VOICE,"text":text,"slot_seconds":round(windows[take],3),"speed":speed,
          "container_seconds":round(len(wav)/24000,3),"safe_seconds":round(safe,3),"leading_silence":round(lead,3),
          "trailing_silence":round(tail,3),"headroom_seconds":round(windows[take]-safe,3),
          "status":"PASS_SURGICAL_TIMING" if safe<=windows[take]-HEADROOM else "FAIL_SURGICAL_TIMING","attempts":attempts})
    unresolved=[r["take"] for r in rows if r["status"]!="PASS_SURGICAL_TIMING"]
    summary={"schema":"pilot-01-kokoro-surgical-regeneration-v1.1","voice":VOICE,"regenerated_count":len(rows),
      "regenerated_takes":list(REWRITES),"pass_count":len(rows)-len(unresolved),"unresolved_count":len(unresolved),
      "unresolved_takes":unresolved,"max_speed":max(r["speed"] for r in rows),"global_speed_change":False,
      "canonical_unaffected_takes_preserved":91-len(rows),"verdict":"PASS_TIMING_ONLY" if not unresolved else "BLOCKED",
      "publishable":False,"release_authorized":False,"conform_authorized":False}
    (OUT/"manifest.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary))
if __name__=="__main__": main()
