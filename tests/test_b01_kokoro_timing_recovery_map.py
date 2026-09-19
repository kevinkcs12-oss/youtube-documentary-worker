#!/usr/bin/env python3
import csv, hashlib, json, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'timing-recovery-v1.0'

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def check(cond,msg):
    if not cond: raise AssertionError(msg)

def main():
    summary=json.loads((OUT/'Pilot_01_Kokoro_Timing_Recovery_Summary_v1.0.json').read_text())
    rows=list(csv.DictReader((OUT/'Pilot_01_Kokoro_Timing_Recovery_Map_v1.0.csv').open()))
    gaps=list(csv.DictReader((OUT/'Pilot_01_Kokoro_Neighboring_Silence_Map_v1.0.csv').open()))
    checks=[]
    def ok(name,cond): check(cond,name); checks.append(name)
    ok('exact_91_take_rows',len(rows)==91 and rows[0]['take']=='T001' and rows[-1]['take']=='T091')
    ok('all_take_ids_unique',len({r['take'] for r in rows})==91)
    ok('remedy_partition',sum(summary['remedy_counts'].values())==91)
    ok('residual_list_consistent',summary['residual_review_count']==len(summary['residual_review_takes'])==14)
    ok('no_negative_timing',all(float(r['slot_seconds'])>0 and float(r['residual_seconds'])>=0 for r in rows))
    ok('hashes_well_formed',all(len(r['raw_sha256'])==64 and len(r['adaptive_sha256'])==64 for r in rows))
    ok('chapter_gaps_locked',all(float(g['recoverable'])==0 for g in gaps if g['rule']=='LOCK_CHAPTER_OR_MICRO_PAUSE'))
    ok('gap_capacity_not_exceeded',all(-1e-6<=float(g['remaining_unallocated'])<=float(g['recoverable'])+1e-6 for g in gaps))
    allocated=sum(float(r['raw_from_before'])+float(r['raw_from_after'])+float(r['adaptive_from_before'])+float(r['adaptive_from_after']) for r in rows)
    available=sum(float(g['recoverable']) for g in gaps)
    ok('silence_never_double_counted',allocated<=available+1e-6)
    ok('no_global_speed',all(1.0<=float(r['adaptive_speed'])<=1.15 for r in rows))
    ok('required_problem_takes_retained',set(summary['residual_review_takes'])=={r['take'] for r in rows if float(r['residual_seconds'])>1e-6})
    with tempfile.TemporaryDirectory() as td:
        cmd=[sys.executable,str(ROOT/'map_pilot_01_kokoro_timing_recovery_v1_0.py'),'--script',str(ROOT/'production/pilot-01/final-voice-recording-script-v1.0.md'),'--raw-dir',str(ROOT/'b01-kokoro-full'),'--adaptive-dir',str(ROOT/'b01-kokoro-adaptive'),'--out-dir',td]
        subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL)
        for name in ['Pilot_01_Kokoro_Timing_Recovery_Map_v1.0.csv','Pilot_01_Kokoro_Neighboring_Silence_Map_v1.0.csv','Pilot_01_Kokoro_Timing_Recovery_Summary_v1.0.json']:
            ok('deterministic_'+name,digest(OUT/name)==digest(Path(td)/name))
    print(json.dumps({'tests':len(checks),'passed':len(checks),'checks':checks},indent=2))

if __name__=='__main__': main()
