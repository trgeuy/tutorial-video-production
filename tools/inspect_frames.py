#!/usr/bin/env python3
"""Look inside a frames file made by rec2frames.py -- the checks that kept being re-typed.

    python3 inspect_frames.py keys   <frames.json> [t0 t1]    key records (Enter, pastes, typing)
    python3 inspect_frames.py screen <frames.json> <t> [...]  screen text at capture time(s) t
    python3 inspect_frames.py times  <frames.json> <t0> <t1>  frame times + first changed row
    python3 inspect_frames.py find   <frames.json> <text>     first capture time the text shows

All times are capture seconds (from the first record). Row numbers printed by `screen` are 0-based.
"""
import bisect, json, sys

def load(p): return json.load(open(p))
def text(f): return ["".join(r[0] for r in row).rstrip() for row in f["rows"]]
def at(d, t):
    ts = [f["t"] for f in d["frames"]]
    return d["frames"][max(0, bisect.bisect_right(ts, t) - 1)]

if len(sys.argv) < 3:
    sys.exit(__doc__)
cmd, arg = sys.argv[1], sys.argv[2]
if cmd == "keys":
    d = load(arg); t0, t1 = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (0, 1e9)
    for k in d["keys"]:
        if t0 <= k["t"] <= t1: print(f"{k['t']:8.3f}  {k['keys'][:70]!r}")
elif cmd == "screen":
    d = load(arg)
    for t in map(float, sys.argv[3:]):
        f = at(d, t); print(f"===== t={t} (frame at {f['t']}) cursor={f['cur']}")
        for i, l in enumerate(text(f)):
            if l.strip(): print(f"{i:2}|{l}")
elif cmd == "times":
    d = load(arg); t0, t1 = float(sys.argv[3]), float(sys.argv[4]); prev = None
    for f in d["frames"]:
        if t0 <= f["t"] <= t1:
            rows = text(f); ch = next((l for i, l in enumerate(rows) if not prev or prev[i] != l), "")
            print(f"{f['t']:8.3f}  {ch.strip()[:90]}"); prev = rows
        elif f["t"] < t0: prev = text(f)
elif cmd == "find":
    d = load(arg); want = sys.argv[3]
    f = next((f for f in d["frames"] if any(want in l for l in text(f))), None)
    print(f"{f['t']:.3f}" if f else "not found")
else:
    sys.exit(__doc__)
