#!/usr/bin/env bash
set -euo pipefail

OPENING=${OPENING:-github_artifacts/opening-v1.2-run34434585813/pilot-01-opening-picture-v1.2.mp4}
EVIDENCE=${EVIDENCE:-materialized/Pilot_01_Evidence_Graphics_01m04_02m22_v1.0.mp4}
SCRATCH_MASTER=${SCRATCH_MASTER:-Pilot_01_Animatic_Scratch_Voice_00m00_10m22_v1.1_repaired.mp4}
SUBTITLES=${SUBTITLES:-materialized/animatic_pack/Pilot_01_Animatic_00m00_02m22_v1.0.srt}
OUTPUT_PREFIX=${OUTPUT_PREFIX:-Pilot_01_Animatic_00m00_02m22_v1.2_rights_safe}
SCRATCH_OUTPUT=${SCRATCH_OUTPUT:-Pilot_01_Animatic_Scratch_Voice_00m00_02m22_v1.2_rights_safe.mp4}
SUBTITLE_OUTPUT=${SUBTITLE_OUTPUT:-Pilot_01_Animatic_00m00_02m22_v1.2_rights_safe.srt}
CONTACT_OUTPUT=${CONTACT_OUTPUT:-Pilot_01_Animatic_00m00_02m22_v1.2_contact_sheet_4s.jpg}
BOUNDARY_OUTPUT=${BOUNDARY_OUTPUT:-Pilot_01_Animatic_00m00_02m22_v1.2_boundary_01m04.jpg}

for input in "$OPENING" "$EVIDENCE" "$SCRATCH_MASTER" "$SUBTITLES"; do
  test -s "$input"
done

tmp_dir=$(mktemp -d)
trap 'rm -rf "$tmp_dir"' EXIT

picture="$tmp_dir/picture.mp4"
narrated="$tmp_dir/narrated.mp4"

ffmpeg -hide_banner -loglevel warning -y \
  -i "$OPENING" -i "$EVIDENCE" \
  -filter_complex \
  "[0:v]trim=start=0:end=64,setpts=PTS-STARTPTS,fps=25,scale=1920:1080:flags=lanczos,setsar=1,format=yuv420p[v0];\
[1:v]trim=start=0:end=78,setpts=PTS-STARTPTS,fps=25,scale=1920:1080:flags=lanczos,setsar=1,format=yuv420p[v1];\
[v0][v1]concat=n=2:v=1:a=0[outv]" \
  -map "[outv]" -an \
  -c:v libx264 -preset medium -crf 18 -profile:v high -level 4.1 \
  -pix_fmt yuv420p -r 25 -video_track_timescale 12800 -movflags +faststart \
  "$picture"

ffmpeg -hide_banner -loglevel warning -y \
  -i "$picture" -i "$SCRATCH_MASTER" \
  -map 0:v:0 -map 1:a:0 -c:v copy \
  -af "atrim=start=0:end=142,asetpts=PTS-STARTPTS" \
  -c:a aac -b:a 192k -t 142 -movflags +faststart "$narrated"

python - "$picture" "$narrated" <<'PY'
import json
import subprocess
import sys

for path in sys.argv[1:]:
    raw = subprocess.check_output([
        "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,nb_read_frames",
        "-show_entries", "format=duration", "-of", "json", path,
    ])
    probe = json.loads(raw)
    stream = probe["streams"][0]
    assert probe["format"]["duration"] == "142.000000", probe
    assert stream["nb_read_frames"] == "3550", probe
    assert stream["width"] == 1920 and stream["height"] == 1080, probe
    assert stream["r_frame_rate"] == "25/1", probe
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-f", "null", "-"],
        check=True,
    )
PY

install -m 0644 "$picture" "${OUTPUT_PREFIX}_picture.mp4"
install -m 0644 "$narrated" "$SCRATCH_OUTPUT"
install -m 0644 "$SUBTITLES" "$SUBTITLE_OUTPUT"

ffmpeg -hide_banner -loglevel error -y -i "$picture" \
  -vf "fps=1/4,scale=480:-1:flags=lanczos,tile=6x6:padding=4:margin=4:color=0x11161b" \
  -frames:v 1 "$CONTACT_OUTPUT"

ffmpeg -hide_banner -loglevel error -y -ss 63.4 -t 1.2 -i "$picture" \
  -vf "fps=5,scale=640:-1:flags=lanczos,tile=6x1:padding=4:margin=4:color=0x11161b" \
  -frames:v 1 "$BOUNDARY_OUTPUT"

sha256sum \
  "${OUTPUT_PREFIX}_picture.mp4" \
  "$SCRATCH_OUTPUT" \
  "$SUBTITLE_OUTPUT" \
  "$CONTACT_OUTPUT" \
  "$BOUNDARY_OUTPUT" \
  > "${OUTPUT_PREFIX}_sha256.txt"
