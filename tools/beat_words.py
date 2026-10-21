#!/usr/bin/env python3
"""One words.json for a whole assembled video, from its HyperFrames beats. Output feeds make_srt.py.

  python3 beat_words.py [--beats-dir DIR] <out.words.json> <beat> [<beat> ...]

Each beat is DIR/<beat>/index.html plus its render DIR/<beat>.mp4. The index.html places its
narration clips (<audio src=... data-start=...>); each clip has a whisper words.json next to its
.wav (<clip>.words.json). Beat offsets = the summed durations of the beat .mp4s in the order given
(as assemble.sh joins them). Prints each beat's offset (= chapter times) and the total, to check
against the final video's duration."""
import argparse, json, re, subprocess

p = argparse.ArgumentParser(description="One words.json for a whole video, from its beats.")
p.add_argument("--beats-dir", default=".", help="folder that holds the beat folders and their .mp4 renders")
p.add_argument("out")
p.add_argument("beats", nargs="+")
a = p.parse_args()
H, out, beats = a.beats_dir, a.out, a.beats
dur = lambda p: float(subprocess.check_output(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).decode())
words, t0 = [], 0.0
for b in beats:
    html = open(f"{H}/{b}/index.html").read()
    for src, start in re.findall(r'<audio[^>]*src="([^"]+)\.wav"[^>]*data-start="([\d.]+)"', html):
        for w in json.load(open(f"{H}/{b}/{src}.words.json")):
            words.append({"text": w["text"], "start": round(t0 + float(start) + w["start"], 3),
                          "end": round(t0 + float(start) + w["end"], 3)})
    m, s = divmod(int(t0), 60)
    print(f"{m}:{s:02d}  {t0:7.2f}  {b}")
    t0 += dur(f"{H}/{b}.mp4")
words.sort(key=lambda w: w["start"])
json.dump(words, open(out, "w"), indent=0)
print(f"total {t0:.2f}s, {len(words)} words -> {out}")
