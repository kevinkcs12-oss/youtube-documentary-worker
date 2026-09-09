#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from urllib.parse import urlparse

def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, check=True)

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("dist/pexels"))
    args = parser.parse_args()

    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    results = []
    for asset in data["assets"]:
        asset_id = asset["id"]
        numeric_id = asset_id.rsplit("-", 1)[-1]
        download_url = f"https://www.pexels.com/download/video/{numeric_id}/"
        media = out / f"{asset_id}.mp4"

        # Use Pexels' own public download endpoint instead of scraping the
        # JavaScript-heavy video page. The endpoint normally redirects to
        # the videos.pexels.com CDN.
        run([
            "curl", "--fail", "--location",
            "--retry", "3", "--retry-delay", "2",
            "--user-agent", "Mozilla/5.0",
            "--output", str(media),
            download_url,
        ])

        # Reject HTML/error bodies masquerading as media.
        probe = out / f"{asset_id}.ffprobe.json"
        with probe.open("w", encoding="utf-8") as handle:
            subprocess.run([
                "ffprobe", "-v", "error",
                "-show_format", "-show_streams",
                "-of", "json", str(media)
            ], stdout=handle, check=True)

        contact = out / f"{asset_id}.contact-sheet.jpg"
        run([
            "ffmpeg", "-y", "-i", str(media),
            "-vf", "fps=0.5,scale=480:-1,tile=4x4",
            "-frames:v", "1",
            str(contact),
        ])

        digest = sha256(media)
        (out / f"{asset_id}.sha256").write_text(
            f"{digest}  {media.name}\n",
            encoding="utf-8",
        )

        results.append({
            "id": asset_id,
            "creator": asset["creator"],
            "page_url": asset["page_url"],
            "download_endpoint": download_url,
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
            "assets": results,
        }, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(results, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
