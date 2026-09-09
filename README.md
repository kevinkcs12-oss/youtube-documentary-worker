# YouTube Documentary Worker — Layer C

Layer C is the deterministic media assembly stage. It turns an approved JSON edit manifest and local assets into a delivery-ready H.264/AAC MP4 plus a machine-readable audit report. It never calls a generation API, reads a secret, or accesses the network.

## Run locally

Requires Python 3.12+, FFmpeg and ffprobe.

```bash
python scripts/run_media_job.py --job examples/layer-c-demo.json --output-dir dist
```

Add `--validate-only` to check a manifest without rendering.

## Job contract (schema version 1)

```json
{
  "schema_version": 1,
  "output": {"filename": "documentary.mp4", "width": 1920, "height": 1080, "fps": 30, "crf": 20, "preset": "medium"},
  "scenes": [
    {"type": "video", "source": "assets/clip.mp4", "start": 2.5, "duration": 8.0},
    {"type": "image", "source": "assets/photo.jpg", "duration": 5.0},
    {"type": "color", "color": "#111827", "duration": 1.5}
  ],
  "audio": {"narration": "assets/narration.wav", "music": "assets/music.mp3", "music_volume": 0.15},
  "subtitles": "assets/captions.srt"
}
```

Asset paths are relative to the manifest. Parent traversal and remote URLs are rejected. Scenes are normalized before concatenation. Music loops to the timeline duration, narration is padded when short, and optional subtitles are burned into the master. Successful runs create the MP4 and `layer-c-report.json`, including ffprobe metadata and an output SHA-256 digest.

## GitHub Actions

- **Layer C CI** runs the unit/integration suite on pushes and pull requests.
- **Layer C Media Job** accepts a repository-relative manifest, runs tests, renders it, and uploads `dist/` as a seven-day artifact.

Both workflows use read-only repository permissions and require no secrets.
