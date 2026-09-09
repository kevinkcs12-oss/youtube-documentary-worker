#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

def run(cmd):
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, default=Path("dist/pexels"))
    args = ap.parse_args()

    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    results = []
    for asset in data["assets"]:
        asset_id = asset["id"]
        page_url = asset["page_url"]
        target_tpl = str(out / f"{asset_id}.%(ext)s")

        before = set(out.iterdir())
        run([
            "yt-dlp",
            "--no-playlist",
            "--restrict-filenames",
            "--merge-output-format", "mp4",
            "-f", "bv*+ba/b",
            "-o", target_tpl,
            page_url,
        ])
        after = set(out.iterdir())
        created = sorted(
            p for p in (after - before)
            if p.is_file() and p.name.startswith(asset_id + ".")
        )
        if not created:
            created = sorted(out.glob(asset_id + ".*"))
        if not created:
            raise SystemExit(f"No file produced for {asset_id}")

        media = max(created, key=lambda p: p.stat().st_size)
        probe = out / f"{asset_id}.ffprobe.json"
        with probe.open("w", encoding="utf-8") as f:
            subprocess.run([
                "ffprobe", "-v", "error",
                "-show_format", "-show_streams",
                "-of", "json", str(media)
            ], stdout=f, check=True)

        contact = out / f"{asset_id}.contact-sheet.jpg"
        run([
            "ffmpeg", "-y", "-i", str(media),
            "-vf", "fps=0.5,scale=480:-1,tile=4x4",
            "-frames:v", "1",
            str(contact)
        ])

        digest = sha256(media)
        (out / f"{asset_id}.sha256").write_text(
            f"{digest}  {media.name}\n", encoding="utf-8"
        )

        results.append({
            "id": asset_id,
            "creator": asset["creator"],
            "page_url": page_url,
            "role": asset["role"],
            "file": media.name,
            "bytes": media.stat().st_size,
            "sha256": digest,
            "ffprobe": probe.name,
            "contact_sheet": contact.name,
        })

    (out / "acquisition-report.json").write_text(
        json.dumps({
            "status": "completed",
            "project": data["project"],
            "assets": results
        }, indent=2),
        encoding="utf-8"
    )
    print(json.dumps(results, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
