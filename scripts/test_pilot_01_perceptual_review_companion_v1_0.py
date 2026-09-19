#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILDER = ROOT / "build_pilot_01_perceptual_review_companion_v1_0.py"
FILM = ROOT / "kokoro-full-film-review-v1.0/Pilot_01_Kokoro_Full_Film_Review_DO_NOT_UPLOAD_v1.0.mp4"
CUES = ROOT / "kokoro-canonical-delivery-v1.0/Pilot_01_Kokoro_Cue_Sheet_v1.0.csv"
INTAKE = ROOT / "kokoro-canonical-delivery-v1.0/Pilot_01_Kokoro_Canonical_Intake_Result_v1.0.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(base: Path, film: Path = FILM, cues: Path = CUES, intake: Path = INTAKE) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(BUILDER), "--film", str(film), "--cue-sheet", str(cues), "--intake-result", str(intake), "--output-dir", str(base / "out")], text=True, capture_output=True)


def main() -> int:
    results = []
    with tempfile.TemporaryDirectory(prefix="b01-perceptual-test-") as raw:
        td = Path(raw)
        a, b = td / "a", td / "b"
        a.mkdir(); b.mkdir()
        pa, pb = run(a), run(b)
        results.append(("happy_path", pa.returncode == 0))
        results.append(("deterministic_zip", pa.returncode == pb.returncode == 0 and digest(a / "Pilot_01_Full_Film_Perceptual_Review_Companion_Pack_v1.0.zip") == digest(b / "Pilot_01_Full_Film_Perceptual_Review_Companion_Pack_v1.0.zip")))

        wrong_film = td / "wrong.mp4"; wrong_film.write_bytes(b"wrong")
        c = td / "c"; c.mkdir()
        results.append(("wrong_film_rejected", run(c, film=wrong_film).returncode != 0))

        rows = list(csv.DictReader(CUES.open(encoding="utf-8-sig")))
        fields = list(rows[0])
        def write_cues(name: str, changed: list[dict[str, str]]) -> Path:
            p = td / name
            with p.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n"); w.writeheader(); w.writerows(changed)
            return p

        for label, changed in [
            ("missing_take_rejected", rows[:-1]),
            ("duplicate_take_rejected", rows[:-1] + [rows[-2]]),
            ("wrong_order_rejected", [rows[1], rows[0]] + rows[2:]),
            ("wrong_final_cue_rejected", rows[:-1] + [{**rows[-1], "end": "00:09:57.760"}]),
        ]:
            base = td / label; base.mkdir()
            results.append((label, run(base, cues=write_cues(label + ".csv", changed)).returncode != 0))

        intake = json.loads(INTAKE.read_text(encoding="utf-8"))
        bad_verdict = td / "bad-verdict.json"; bad_verdict.write_text(json.dumps({**intake, "verdict": "BLOCKED"}))
        base = td / "bad-verdict"; base.mkdir()
        results.append(("bad_intake_verdict_rejected", run(base, intake=bad_verdict).returncode != 0))

        missing_warning = td / "missing-warning.json"
        missing_warning.write_text(json.dumps({**intake, "warnings": [w for w in intake["warnings"] if "Nielsen" not in w]}))
        base = td / "missing-warning"; base.mkdir()
        results.append(("missing_named_warning_rejected", run(base, intake=missing_warning).returncode != 0))

        results.append(("overwrite_rejected", run(a).returncode != 0))
        score_rows = list(csv.DictReader((a / "out/Pilot_01_Full_Film_Perceptual_Review_Scorecard_v1.0.csv").open(encoding="utf-8")))
        manifest = json.loads((a / "out/Pilot_01_Full_Film_Perceptual_Review_Manifest_v1.0.json").read_text())
        closed = all(not r["human_verdict"] and r["repair_authorized"] == "NO" for r in score_rows) and not any(manifest[k] for k in ("final_master_authorized", "upload_authorized", "publishable", "release_authorized"))
        results.append(("human_fields_and_authority_fail_closed", closed))

    output = {"total": len(results), "passed": sum(ok for _, ok in results), "results": [{"test": n, "passed": ok} for n, ok in results]}
    print(json.dumps(output, indent=2))
    return 0 if output["passed"] == output["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
