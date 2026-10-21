#!/bin/bash
# Final loudness pass for upload. The video stream is copied; only the audio changes.
#   ./master.sh <in.mp4> <out.mp4> [target_lufs=-15.9] [limit_dbfs=-2]
# The narration is levelled low per clip (-24.5 LUFS in our series). YouTube turns down audio above
# about -14 LUFS but does not turn quiet audio up (third-party guides; check "Stats for nerds" after
# upload). Plain gain would push the peaks over 0 dBFS, so a limiter holds them. Two passes: the
# limiter takes some loudness away, so pass 2 adds back what pass 1 missed. Prints before/after figures.
set -e
IN=$1; OUT=$2; T=${3:--15.9}; L=${4:--2}
meas() { ffmpeg -hide_banner -i "$1" -af "${2:-anull},loudnorm=print_format=json" -f null - 2>&1 \
  | python3 -c "import sys,json,re; d=json.loads(re.search(r'\{[^{}]*\}',sys.stdin.read()).group()); print(d['input_i'],d['input_tp'])"; }
chain() { echo "volume=${1}dB,alimiter=limit=$(python3 -c "print(round(10**($L/20),4))"):attack=5:release=50:level=false"; }
read I0 TP0 <<< "$(meas "$IN")"
G=$(python3 -c "print(round($T-($I0),2))")
read I1 TP1 <<< "$(meas "$IN" "$(chain $G)")"
G=$(python3 -c "print(round($G+$T-($I1),2))")
ffmpeg -v error -y -i "$IN" -map 0:v -map 0:a -c:v copy -af "$(chain $G)" -c:a aac -b:a 256k -ar 48000 \
  -movflags +faststart "$OUT"
read I2 TP2 <<< "$(meas "$OUT")"
echo "$(basename "$IN"): $I0 LUFS / $TP0 dBTP -> gain +$G dB, limit $L dBFS -> $(basename "$OUT"): $I2 LUFS / $TP2 dBTP"
