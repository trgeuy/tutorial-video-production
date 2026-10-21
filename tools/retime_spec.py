#!/usr/bin/env python3
"""Map a spec's capture times through a compose's timemap.json (made by recio.pace). Run from a beat folder:

    python3 <repo>/tools/retime_spec.py spec.oldtimes.json timemap.json spec.json [window_id]

spec.oldtimes.json = the spec written in the ORIGINAL capture's times (from inspect_frames.py on the unpaced frames);
every segment from/to and every titles[].at is mapped (for duokit, only the segments/titles of window_id).
Video times (`at`, `after_prev`) are not touched.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recio
src, tm, dst = sys.argv[1:4]
win = sys.argv[4] if len(sys.argv) > 4 else None
spec = json.load(open(src)); tmap = [tuple(p) for p in json.load(open(tm))]
m = lambda t: round(recio.remap(tmap, t), 3)
for s in spec["segments"]:
    if win is None or s.get("win") == win: s["from"], s["to"] = m(s["from"]), m(s["to"])
for w in spec.get("windows", [spec]):
    if win is None or w.get("id") == win:
        for t in w.get("titles", []): t["at"] = m(t["at"])
json.dump(spec, open(dst, "w"), indent=1, ensure_ascii=False)
print(f"{dst}: {sum(1 for s in spec['segments'] if win is None or s.get('win') == win)} segments re-timed")
