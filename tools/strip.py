#!/usr/bin/env python3
"""Show where the words are in a narration clip: loud, quiet and silent stretches, 10 ms at a time.

Usage: python3 strip.py <clip.wav> <t0> <t1>

Prints two views of t0..t1 (seconds):
  runs:  LOUD / low / sil stretches with their times, e.g. "LOUD6.55-6.76 low6.76-6.88"
  strip: one character per 10 ms, "." silent, 1-2 quiet, 3-5 loud, with a | every 100 ms

Use it to find a word's real edges: for a rec_prep.py --start/--end cut, to shorten a pause inside
a take, or to cut one word out. Whisper word times are not edges: ours were 0.15-0.6 s off.
Count the stretches from a KNOWN word on each side (a silence, a stop like the "t" in "at", the next
sentence), never from whisper's times alone. A word with a stop consonant inside has a short dip in
the middle: do not take that dip for the edge. When one stretch is ambiguous, cut short excerpts and
transcribe them to see which words they hold. Words that run together with no dip have no clean
edge: pick a time and judge it by ear.
"""
import math, subprocess, sys
from array import array

RATE = 48000


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", str(RATE), "-"],
                         capture_output=True, check=True).stdout
    return array("h", raw)


def rms(a, i, j):
    j = max(j, i + 1)
    return math.sqrt(sum(x * x for x in a[i:j]) / (j - i))


def levels(path, t0, t1):
    a, n, out = load(path), int(0.01 * RATE), ""
    for k in range(int(round((t1 - t0) / 0.01))):
        i = int((t0 + k * 0.01) * RATE)
        r = rms(a, i, i + n)
        out += next(c for lim, c in ((100, "."), (300, "1"), (700, "2"), (1200, "3"), (2000, "4"), (1e9, "5")) if r < lim)
    return out


def runs(s, t0):
    segs, cur = [], None
    for k, c in enumerate(s):
        cls = "sil" if c == "." else ("low" if c in "12" else "LOUD")
        if cur and cur[0] == cls:
            cur[2] = k
        else:
            cur = [cls, k, k]
            segs.append(cur)
    return " ".join(f"{c}{t0 + a * 0.01:.2f}-{t0 + (b + 1) * 0.01:.2f}" for c, a, b in segs if b > a or c == "sil")


if len(sys.argv) != 4:
    sys.exit(__doc__)
path, t0, t1 = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
s = levels(path, t0, t1)
print("runs: ", runs(s, t0))
print("strip:", s)
print("      ", "".join("|" if k % 10 == 0 else " " for k in range(len(s))))
