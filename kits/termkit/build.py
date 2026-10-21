#!/usr/bin/env python3
"""Build index.html for a simulated-Terminal beat. Run it from the beat's own folder:

    cd <beat folder> && python3 <repo>/kits/termkit/build.py

Reads spec.json there and term.template next to this file.

spec.json keys: user, host, cps, enter_lag, lead_in, clip_gap, min_gap, tail, final_dir,
clips [{id, audio, words}], steps [...].

A step:
  cmd        text typed (may be "")
  dir        shell directory for the default prompt "user@host dir % "
  prompt     overrides the default prompt ("A>", "mysim> ", "" for a BASIC line, "Password:")
  out        lines printed after Return
  late       {"after": s, "lines": [...]} lines printed s seconds after out (boot delays)
  hidden     true: typing is not shown (a password)
  title      window title from this step on (default: "<dir> — -zsh — 120×30")
  key        a keycap caption shown on screen at the step's start ("Control-E", "Return")
  cue        {"clip", "phrase", "anchor": "start"|"end", "offset"} start time from narration
  after_prev seconds after the previous step finished (default min_gap)
Each step's start comes from its cue, or from after_prev. Clips play one after another: a clip
starts clip_gap seconds after the previous clip AND its last step have finished.
"""
import json, re, subprocess, sys

spec = json.load(open("spec.json"))
cps, lag, min_gap = spec["cps"], spec["enter_lag"], spec["min_gap"]
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())

def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    return float(out.stdout)

def find_cue(words, phrase, anchor):
    want = [norm(w) for w in phrase.split()]
    toks = [norm(w["text"]) for w in words]
    for i in range(len(toks) - len(want) + 1):
        if toks[i:i + len(want)] == want:
            return words[i]["start"] if anchor == "start" else words[i + len(want) - 1]["end"]
    sys.exit(f"cue phrase not found: {phrase!r}\n  transcript: {' '.join(w['text'] for w in words)}")

def step_done(s):
    end = s["at"] + len(s["cmd"]) / cps + lag
    return end + (s["late"]["after"] if "late" in s else 0)

clips = {c["id"]: dict(c, words=json.load(open(c["words"])), dur=duration(c["audio"])) for c in spec["clips"]}
order = [c["id"] for c in spec["clips"]]
clips[order[0]]["start"] = spec["lead_in"]
steps, prev, cur, warnings = [], None, order[0], []

for raw in spec["steps"]:
    s = {k: raw[k] for k in ("cmd", "dir", "prompt", "out", "late", "hidden", "key", "title") if k in raw}
    s.setdefault("out", [])
    cue = raw.get("cue")
    if cue and cue["clip"] != cur:
        # Move on to the cued clip. It, and any uncued clips before it, each start after the
        # clip before them and after the last step so far.
        for cid in order[order.index(cur) + 1: order.index(cue["clip"]) + 1]:
            prev_clip = clips[cur]
            clips[cid]["start"] = round(max(prev_clip["start"] + prev_clip["dur"],
                                            step_done(prev) if prev else 0) + spec["clip_gap"], 2)
            cur = cid
    if cue:
        c = clips[cue["clip"]]
        t = c["start"] + find_cue(c["words"], cue["phrase"], cue.get("anchor", "start")) + cue.get("offset", 0)
    else:
        t = (step_done(prev) if prev else spec["lead_in"]) + raw.get("after_prev", min_gap)
    if prev and t < step_done(prev) + min_gap:
        warnings.append(f"{(s.get('prompt','') + s['cmd'])[:30]!r}: cue at {t:.2f}s pushed to {step_done(prev) + min_gap:.2f}s")
        t = step_done(prev) + min_gap
    s["at"] = round(t, 2)
    steps.append(s); prev = s

# Clips that no step cues still play, in order, after the one before them.
for i, cid in enumerate(order[1:], 1):
    if "start" not in clips[cid]:
        p = clips[order[i - 1]]
        clips[cid]["start"] = round(max(p["start"] + p["dur"], step_done(prev)) + spec["clip_gap"], 2)
last_clip = clips[order[-1]]
total = round(max(last_clip["start"] + last_clip["dur"], step_done(prev)) + spec["tail"], 2)

audio = "\n      ".join(
    f'<audio id="narr-{cid}" src="{clips[cid]["audio"]}" data-start="{clips[cid]["start"]}" '
    f'data-duration="{clips[cid]["dur"]:.2f}" data-track-index="{i + 1}"></audio>'
    for i, cid in enumerate(order))
tpl = open(__file__.rsplit("/", 1)[0] + "/term.template").read()
html = (tpl.replace("%%AUDIO%%", audio)
        .replace("%%STEPS%%", json.dumps(steps, ensure_ascii=False, indent=2).replace("\n", "\n      "))
        .replace("%%DUR%%", str(total))
        .replace("%%FINAL_DIR%%", json.dumps(spec.get("final_dir")))
        .replace("%%CPS%%", str(cps)).replace("%%LAG%%", str(lag))
        .replace("%%USER%%", json.dumps(spec["user"]))
        .replace("%%HOST%%", json.dumps(spec["host"])))
open("index.html", "w").write(html)

for cid in order:
    print(f"clip {cid}: {clips[cid]['start']:6.2f}s -> {clips[cid]['start'] + clips[cid]['dur']:6.2f}s")
for s in steps:
    print(f"  {s['at']:6.2f}s  {s.get('prompt', '$ ')}{s['cmd']}{'   [' + s['key'] + ']' if 'key' in s else ''}")
print(f"total {total}s")
for w in warnings: print("WARNING:", w)
