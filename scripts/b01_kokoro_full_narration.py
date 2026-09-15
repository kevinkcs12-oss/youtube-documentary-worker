#!/usr/bin/env python3
from pathlib import Path
import re, json
import numpy as np
import soundfile as sf
from kokoro import KPipeline

SRC=Path("production/pilot-01/final-voice-recording-script-v1.0.md")
OUT=Path("dist/b01-kokoro-full")
VOICE="am_michael"
TAKE_RE=re.compile(r"^### (T\d{3}) · cues .* · (\d\d):(\d\d):(\d\d\.\d{3})–(\d\d):(\d\d):(\d\d\.\d{3})$")

def sec(h,m,s): return int(h)*3600+int(m)*60+float(s)

def parse():
    lines=SRC.read_text(encoding="utf-8").splitlines()
    takes=[]
    for i,line in enumerate(lines):
        m=TAKE_RE.match(line)
        if not m: continue
        text=lines[i+2].strip()
        start=sec(m.group(2),m.group(3),m.group(4)); end=sec(m.group(5),m.group(6),m.group(7))
        takes.append((m.group(1),start,end,text))
    assert len(takes)==91, len(takes)
    return takes

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    pipe=KPipeline(lang_code="a")
    rows=[]
    for take,start,end,text in parse():
        chunks=[audio for _,_,audio in pipe(text,voice=VOICE,speed=1.0,split_pattern=r"\n+")]
        wav=np.concatenate(chunks) if chunks else np.zeros(1,dtype=np.float32)
        p=OUT/f"{take}.wav"; sf.write(p,wav,24000,subtype="PCM_16")
        dur=len(wav)/24000
        rows.append({"take":take,"start":start,"slot_seconds":round(end-start,3),"generated_seconds":round(dur,3),"overflow_seconds":round(max(0,dur-(end-start)),3),"text":text})
    (OUT/"manifest.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
    over=[r for r in rows if r["overflow_seconds"]>0]
    summary={"voice":VOICE,"takes":len(rows),"overflow_count":len(over),"max_overflow":max([r["overflow_seconds"] for r in over],default=0)}
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary))
if __name__=="__main__": main()
