#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VALIDATOR = ROOT / "validate_pilot_01_perceptual_review_v1_0.py"
SOURCE = ROOT / "perceptual-review-companion-v1.0/Pilot_01_Full_Film_Perceptual_Review_Scorecard_v1.0.csv"
FILM_SHA = "8076d795c25f2fef0f377fd4abacaa72ad3a22b6f7dddb0cedfb47c7b413c580"
ATTEST = "I REVIEWED THE FULL 09:57.760 FILM AT NORMAL SPEED"


def base_decision(overall: str) -> dict:
    return {"schema":"pilot-01-perceptual-review-decision-v1.0","film_sha256":FILM_SHA,"reviewer_id":"Kevin","review_completed_at":"2026-09-20T00:00:00+02:00","continuous_watch_completed":True,"normal_speed":True,"hotspots_opened_after_first_pass":True,"overall_decision":overall,"systemic_failure_confirmed":False,"attestation":ATTEST}


def rows() -> list[dict[str, str]]:
    with SOURCE.open(newline="", encoding="utf-8") as f:
        data = list(csv.DictReader(f))
    for r in data:
        r["human_verdict"]="PASS"; r["severity"]="NONE"; r["issue_type"]=""; r["notes"]=""; r["repair_authorized"]="NO"
    return data


def execute(td: Path, name: str, score_rows: list[dict[str, str]], decision: dict) -> tuple[int, dict]:
    sc=td/f"{name}.csv"; dj=td/f"{name}.json"; out=td/f"{name}-out.json"
    with sc.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(score_rows[0]),lineterminator="\n"); w.writeheader(); w.writerows(score_rows)
    dj.write_text(json.dumps(decision),encoding="utf-8")
    p=subprocess.run([sys.executable,str(VALIDATOR),"--scorecard",str(sc),"--decision",str(dj),"--output",str(out)],capture_output=True,text=True)
    return p.returncode,json.loads(out.read_text())


def main() -> int:
    tests=[]
    with tempfile.TemporaryDirectory(prefix="b01-review-validator-") as raw:
        td=Path(raw)
        code,res=execute(td,"pass",rows(),base_decision("PASS_PERCEPTUAL_REVIEW")); tests.append(("complete_pass",code==0 and res["verdict"]=="PASS_PERCEPTUAL_REVIEW_ONLY" and res["human_perceptual_gate_passed"]))
        rr=rows(); rr[34].update(human_verdict="DEFECT",severity="MAJOR",issue_type="PRONUNCIATION",notes="Nielsen unclear")
        code,res=execute(td,"repair",rr,base_decision("TARGETED_REPAIR")); tests.append(("targeted_repair",code==0 and res["targeted_repair_take_ids"]==["T035"]))
        rr=rows(); rr[0]["human_verdict"]=""; code,res=execute(td,"incomplete",rr,base_decision("PASS_PERCEPTUAL_REVIEW")); tests.append(("incomplete_blocked",code==2))
        rr=rows(); rr[34].update(human_verdict="DEFECT",severity="MAJOR",notes="bad"); code,res=execute(td,"contradict",rr,base_decision("PASS_PERCEPTUAL_REVIEW")); tests.append(("major_cannot_pass",code==2))
        d=base_decision("PASS_PERCEPTUAL_REVIEW"); d["film_sha256"]="0"*64; code,_=execute(td,"wronghash",rows(),d); tests.append(("wrong_film_blocked",code==2))
        d=base_decision("PASS_PERCEPTUAL_REVIEW"); d["continuous_watch_completed"]=False; code,_=execute(td,"nowatch",rows(),d); tests.append(("no_continuous_watch_blocked",code==2))
        d=base_decision("PASS_PERCEPTUAL_REVIEW"); d["attestation"]="yes"; code,_=execute(td,"badattest",rows(),d); tests.append(("bad_attestation_blocked",code==2))
        rr=rows(); rr[0]["repair_authorized"]="YES"; code,_=execute(td,"authority",rr,base_decision("PASS_PERCEPTUAL_REVIEW")); tests.append(("repair_authority_blocked",code==2))
        rr=rows(); rr[0].update(human_verdict="DEFECT",severity="MAJOR",notes="systemic 1"); rr[20].update(human_verdict="DEFECT",severity="MAJOR",notes="systemic 2"); d=base_decision("REJECT_VOICE"); d["systemic_failure_confirmed"]=True; code,res=execute(td,"reject",rr,d); tests.append(("systemic_reject",code==0 and res["verdict"]=="VOICE_REJECTED_BY_HUMAN_REVIEW"))
        rr=rows(); rr[0].update(human_verdict="DEFECT",severity="MINOR",notes="small"); code,res=execute(td,"minorpass",rr,base_decision("PASS_PERCEPTUAL_REVIEW")); tests.append(("minor_below_threshold_can_pass",code==0 and res["defect_count"]==1))
        tests.append(("all_release_authority_false",not any(res[k] for k in ("final_master_authorized","upload_authorized","publishable","release_authorized"))))
    report={"total":len(tests),"passed":sum(ok for _,ok in tests),"results":[{"test":n,"passed":ok} for n,ok in tests]}
    print(json.dumps(report,indent=2)); return 0 if report["passed"]==report["total"] else 1


if __name__=="__main__": raise SystemExit(main())
