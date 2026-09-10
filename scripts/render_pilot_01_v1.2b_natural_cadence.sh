#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${PILOT_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
FIRST="${FIRST_BLOCK_INPUT:-$REPO_ROOT/inputs/Pilot_01_Animatic_Scratch_Voice_00m00_02m22_v1.2_rights_safe.mp4}"
TIMING="${RETENTION_TEST_INPUT:-$REPO_ROOT/inputs/Pilot_01_Animatic_Scratch_Voice_00m00_10m02_v1.2_retention_test_delivery_exact.mp4}"
SEG_A="${SEGMENT_A_TEXT:-$REPO_ROOT/production/pilot-01/v1.2b-segment-A.txt}"
SEG_B="${SEGMENT_B_TEXT:-$REPO_ROOT/production/pilot-01/v1.2b-segment-B.txt}"
WORK="${WORK_DIR:-$REPO_ROOT/work/v12b}"
DELIVERY_DIR="${DELIVERY_DIR:-$REPO_ROOT/output}"
OUT="$DELIVERY_DIR/Pilot_01_Animatic_Scratch_Voice_00m00_10m02_v1.2b_natural_cadence.mp4"

mkdir -p "$WORK" "$DELIVERY_DIR"

printf '%s  %s\n' \
  '97e14b3d2d64bdb54c188ed4c5276c560dfd2af9d3078c0641af5d009cabad14' "$FIRST" \
  '53167e363cd9256a62d9720eafacf36539c0ee432c7a7899dea89559af7c42bd' "$TIMING" \
  > "$WORK/input.sha256"
sha256sum -c "$WORK/input.sha256"

# Local Flite is only a timing instrument. These files are generated at the
# synthesizer's native cadence, then padded—not sped up—to their edit slots.
ffmpeg -y -loglevel error -f lavfi \
  -i "flite=textfile=$SEG_A:voice=slt" \
  -ar 48000 -ac 1 "$WORK/A_raw.wav"
ffmpeg -y -loglevel error -f lavfi \
  -i "flite=textfile=$SEG_B:voice=slt" \
  -ar 48000 -ac 1 "$WORK/B_raw.wav"

ffmpeg -y -loglevel error -i "$WORK/A_raw.wav" \
  -af 'apad,atrim=0:14' -ar 48000 -ac 1 -c:a pcm_s16le "$WORK/A_14s.wav"
ffmpeg -y -loglevel error -i "$WORK/B_raw.wav" \
  -af 'apad,atrim=0:54' -ar 48000 -ac 1 -c:a pcm_s16le "$WORK/B_54s.wav"

# v1.2 timing map after the first six-second reduction:
# replacement A 148–162; replacement B 376–430.
ffmpeg -y -loglevel error -threads 1 \
  -i "$FIRST" -i "$TIMING" -i "$WORK/A_14s.wav" -i "$WORK/B_54s.wav" \
  -filter_complex \
  "[0:v]trim=start_frame=0:end_frame=3550,setpts=PTS-STARTPTS[v0];
   [1:v]trim=start_frame=3550:end_frame=15050,setpts=PTS-STARTPTS[v1];
   [v0][v1]concat=n=2:v=1:a=0[v];
   [0:a]atrim=0:142,asetpts=PTS-STARTPTS[a0];
   [1:a]atrim=142:148,asetpts=PTS-STARTPTS[a1];
   [2:a]atrim=0:14,asetpts=PTS-STARTPTS[a2];
   [1:a]atrim=162:376,asetpts=PTS-STARTPTS[a3];
   [3:a]atrim=0:54,asetpts=PTS-STARTPTS[a4];
   [1:a]atrim=430:602,asetpts=PTS-STARTPTS[a5];
   [a0][a1][a2][a3][a4][a5]concat=n=6:v=0:a=1[a]" \
  -map '[v]' -map '[a]' -frames:v 15050 -r 25 \
  -c:v libx264 -threads 1 -preset ultrafast -crf 21 -pix_fmt yuv420p \
  -c:a aac -b:a 160k -ar 48000 -ac 1 -movflags +faststart "$OUT.tmp.mp4"
mv "$OUT.tmp.mp4" "$OUT"

duration=$(ffprobe -v error -show_entries stream=duration -select_streams v:0 -of default=nw=1:nk=1 "$OUT")
frames=$(ffprobe -v error -count_frames -show_entries stream=nb_read_frames -select_streams v:0 -of default=nw=1:nk=1 "$OUT")
test "$duration" = '602.000000'
test "$frames" = '15050'
ffmpeg -v error -i "$OUT" -f null -

ffmpeg -y -loglevel error -ss 140 -i "$OUT" -t 24 \
  -vf 'fps=1/2,scale=480:-1,tile=4x3:padding=4:margin=4:color=white' \
  -frames:v 1 "$DELIVERY_DIR/Pilot_01_v1.2b_Boundary_A_QA.jpg"
ffmpeg -y -loglevel error -ss 372 -i "$OUT" -t 62 \
  -vf 'fps=1/5,scale=480:-1,tile=4x3:padding=4:margin=4:color=white' \
  -frames:v 1 "$DELIVERY_DIR/Pilot_01_v1.2b_Boundary_B_QA.jpg"
ffmpeg -y -loglevel error -i "$OUT" \
  -vf 'fps=1/20,scale=480:-1,tile=6x6:nb_frames=36:padding=4:margin=4:color=white' \
  -frames:v 1 "$DELIVERY_DIR/Pilot_01_v1.2b_Full_Contact_Sheet.jpg"

sha256sum "$OUT" "$WORK/A_14s.wav" "$WORK/B_54s.wav" "$SEG_A" "$SEG_B" \
  > "$DELIVERY_DIR/Pilot_01_v1.2b_SHA256SUMS.txt"
