#!/usr/bin/env python3
import csv, hashlib, json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'timing-recovery-v1.1'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    s=json.loads((OUT/'Pilot_01_Kokoro_Timing_Recovery_Summary_v1.1.json').read_text())
    rows=list(csv.DictReader((OUT/'Pilot_01_Kokoro_Timing_Recovery_Map_v1.1.csv').open()))
    gaps=list(csv.DictReader((OUT/'Pilot_01_Kokoro_Neighboring_Silence_Map_v1.1.csv').open()))
    checks={
      'exact_91':len(rows)==91 and len({r['take'] for r in rows})==91,
      'partition':sum(s['remedy_counts'].values())==91,
      'protected_inputs':s['protected_visual_intervals']==26,
      'visual_collisions_locked':all(float(g['recoverable'])==0 for g in gaps if g['protected_collision']),
      'chapter_and_micro_locked':all(float(g['recoverable'])==0 for g in gaps if g['rule']=='LOCK_CHAPTER_OR_MICRO_PAUSE'),
      'capacity_not_exceeded':all(-1e-6<=float(g['remaining_unallocated'])<=float(g['recoverable'])+1e-6 for g in gaps),
      'no_global_speed':all(1.0<=float(r['adaptive_speed'])<=1.15 for r in rows),
      'residual_exact':set(s['residual_review_takes'])=={r['take'] for r in rows if float(r['residual_seconds'])>1e-6},
      'authority_closed':s['schema']=='pilot-01-kokoro-timing-recovery-map-v1.1'
    }
    assert all(checks.values()),checks
    with tempfile.TemporaryDirectory() as td:
      subprocess.run([sys.executable,str(ROOT/'map_pilot_01_kokoro_timing_recovery_v1_0.py'),'--script',str(ROOT/'production/pilot-01/final-voice-recording-script-v1.0.md'),'--raw-dir',str(ROOT/'b01-kokoro-full'),'--adaptive-dir',str(ROOT/'b01-kokoro-adaptive'),'--evidence-overlay-map',str(ROOT/'production/pilot-01/v1.2d-evidence-safezone-overlay-map.csv'),'--chapter-transition-map',str(ROOT/'production/pilot-01/chapter-transition-sound-design-timing-map-v1.0.csv'),'--out-dir',td],check=True,stdout=subprocess.DEVNULL)
      for n in ['Pilot_01_Kokoro_Timing_Recovery_Map_v1.1.csv','Pilot_01_Kokoro_Neighboring_Silence_Map_v1.1.csv','Pilot_01_Kokoro_Timing_Recovery_Summary_v1.1.json']:
        checks['deterministic_'+n]=sha(OUT/n)==sha(Path(td)/n)
    assert all(checks.values()),checks
    print(json.dumps({'tests':len(checks),'passed':sum(checks.values()),'checks':checks},indent=2))
if __name__=='__main__': main()
