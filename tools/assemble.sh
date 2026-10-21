#!/bin/bash
# Join rendered beats into one video, in order. Re-run after re-rendering any beat.
#   ./assemble.sh [-d <beat folder>] <out.mp4> <beat> [<beat> ...]
#   ./assemble.sh -d renders draft1.mp4 card-title intro build card-end
# Each <beat> is <beat folder>/<beat>.mp4 (default folder: the current one). A silent part (a card)
# gets a silent audio track, so every part has the same streams. Prints each beat's length and the
# total: the total must equal the sum of the beats.
set -e
H=.
[ "$1" = "-d" ] && { H=$2; shift 2; }
[ $# -lt 2 ] && { sed -n '2,7p' "$0"; exit 1; }
OUT=$1; shift
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
in=(); f=""; i=0
for b in "$@"; do
  p=$H/$b.mp4
  if [ -z "$(ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$p")" ]; then
    ffmpeg -v error -y -i "$p" -f lavfi -i anullsrc=r=48000:cl=stereo -shortest -c:v copy -c:a aac "$TMP/$b.silent.mp4"
    p=$TMP/$b.silent.mp4
  fi
  in+=(-i "$p"); f+="[$i:v][$i:a]"; i=$((i+1))
done
ffmpeg -v error -y "${in[@]}" -filter_complex "${f}concat=n=$i:v=1:a=1[v][a]" -map "[v]" -map "[a]" \
  -r 30 -c:v libx264 -pix_fmt yuv420p -crf 18 -c:a aac -ar 48000 -ac 2 -movflags +faststart "$OUT"
for b in "$@"; do printf "%-22s %6.1fs\n" "$b" "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$H/$b.mp4")"; done
printf "%-22s %6.1fs\n" "$(basename "$OUT")" "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")"
