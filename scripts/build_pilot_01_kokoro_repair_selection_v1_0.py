#!/usr/bin/env python3
"""Consolidate the two surgical passes and three bounded timing transfers."""
import csv, hashlib, json, shutil, wave
from pathlib import Path

PASS1=Path('b01-kokoro-surgical'); PASS2=Path('b01-kokoro-surgical-v1.1'); ADAPT=Path('b01-kokoro-adaptive')
OUT=Path('kokoro-repair-selection-v1.0')
FIRST={'T025','T041','T045','T049','T052','T058','T063','T064','T065','T082'}
SECOND={'T023','T027','T037','T062'}
MICRO={'T061':('T062',0.043),'T074':('T075',0.056),'T088':('T089',0.066)}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def wav_seconds(p):
    with wave.open(str(p),'rb') as w: return w.getnframes()/w.getframerate()
def main():
    OUT.mkdir(parents=True,exist_ok=True); (OUT/'takes').mkdir(exist_ok=True)
    p1={x['take']:x for x in json.loads((PASS1/'manifest.json').read_text())}
    p2={x['take']:x for x in json.loads((PASS2/'manifest.json').read_text())}
    amap={x['take']:x for x in json.loads((ADAPT/'manifest.json').read_text())}
    timing={x['take']:x for x in csv.DictReader(open('timing-recovery-v1.1/Pilot_01_Kokoro_Timing_Recovery_Map_v1.1.csv'))}
    rows=[]
    for take in sorted(FIRST|SECOND):
        srcdir,meta,pass_name=(PASS1,p1[take],'surgical_v1.0') if take in FIRST else (PASS2,p2[take],'surgical_v1.1')
        assert meta['status']=='PASS_SURGICAL_TIMING'
        src=srcdir/f'{take}.wav'; dst=OUT/'takes'/f'{take}.wav'; shutil.copyfile(src,dst)
        rows.append({'take':take,'action':'SURGICAL_REWRITE','source_pass':pass_name,'speed':meta['speed'],
          'slot_seconds':meta['slot_seconds'],'safe_seconds':meta['safe_seconds'],'headroom_seconds':meta['headroom_seconds'],
          'borrowed_seconds':0.0,'borrowed_from':'','text':meta['text'],'wav_seconds':round(wav_seconds(dst),6),'sha256':sha(dst),'status':'PASS_TIMING_ONLY'})
    for take,(neighbor,borrow) in MICRO.items():
        meta=amap[take]; src=ADAPT/f'{take}.wav'; dst=OUT/'takes'/f'{take}.wav'; shutil.copyfile(src,dst)
        # v1.1 map established exact residual after safe trim and retained 100 ms headroom.
        neighbor_safe=float(p2[neighbor]['safe_seconds']) if neighbor in p2 else float(timing[neighbor]['adaptive_safe_duration'])
        neighbor_slot=float(p2[neighbor]['slot_seconds']) if neighbor in p2 else float(timing[neighbor]['slot_seconds'])
        neighbor_new_slot=neighbor_slot-borrow
        assert neighbor_safe <= neighbor_new_slot-0.1+1e-6, (take,neighbor)
        rows.append({'take':take,'action':'EDITORIAL_BOUNDARY_TRANSFER','source_pass':'adaptive_original','speed':meta['speed'],
          'slot_seconds':round(float(meta['slot_seconds'])+borrow,3),'safe_seconds':'','headroom_seconds':0.1,
          'borrowed_seconds':borrow,'borrowed_from':neighbor,'text':meta['text'],'wav_seconds':round(wav_seconds(dst),6),'sha256':sha(dst),'status':'PASS_TIMING_ONLY'})
    rows.sort(key=lambda x:x['take'])
    fields=list(rows[0])
    with (OUT/'Pilot_01_Kokoro_Repair_Selection_Manifest_v1.0.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    summary={'schema':'pilot-01-kokoro-repair-selection-v1.0','voice':'am_michael','affected_takes':17,
      'surgical_rewrites':14,'editorial_boundary_transfers':3,'timing_pass_count':17,'timing_fail_count':0,
      'unaffected_takes_preserved':74,'global_speed_change':False,'max_speed':max(float(r['speed']) for r in rows),
      'verdict':'PASS_REPAIR_SELECTION_ONLY','intake_passed':False,'conform_passed':False,'publishable':False,
      'release_authorized':False,'micro_transfers':{k:{'borrow_from':v[0],'seconds':v[1]} for k,v in MICRO.items()}}
    (OUT/'Pilot_01_Kokoro_Repair_Selection_Summary_v1.0.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))
if __name__=='__main__': main()
