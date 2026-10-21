#!/usr/bin/env python3
"""Build index.html for a TWO-WINDOW beat (duokit): two replayed terminal captures on one desktop,
smaller than screenkit's one window, overlapping, with the front window changing on cues -- e.g.
Claude Code in one window and a program's output in the other. Run it from the
beat's own folder:

    cd <beat folder> && python3 <repo>/kits/duokit/build.py

Each window replays a frames file made by tools/rec2frames.py from a REAL capture, exactly as
screenkit does (same colours, substitutions, cursor, timing rules); this script only decides WHEN
each part plays, WHERE each window sits and WHICH one is in front.

spec.json:
  lead_in, clip_gap, min_gap, tail   seconds, as in screenkit/termkit
  clips      [{id, audio, words}] -- narration, played one after another (may be empty: then every
             segment needs `at` or `after_prev`; for tests)
  windows    [{id, frames, title, titles[{at, title}], subs{}, x, y, font, expect[]}]
             x, y = top-left corner on the 1920x1080 page; font = terminal font size in px (the
             window is cols x rows of the capture at that size: 120x30 at 15 px is ~1150x700).
             The LAST window listed starts in front.
  segments   [{win, from, to, speed, cue{clip, phrase, anchor, offset} | at | after_prev | with_prev, fill}]
             `fill: true`: background -- holds back no clip or later segment; its speed is set so it
             ends exactly as the same window's next segment starts (its `to` = that one's `from`).
             as screenkit's, plus `win`. A segment is pushed only by the previous segment of the SAME
             window (min_gap), so the two windows can play at once. `with_prev: true` starts it at the
             previous segment's start (any window) + `offset`.
  focus      [{win, cue{...} | at}] bring a window to the front (as a click would)
  (segment `dip`: seconds -- the whole picture fades to black before that segment and back in from its
   start, as screenkit; a cut both windows share, so give it to one segment only)
  callouts   [{win, row, text, nth | line, cue{...} | at, dur}] a box round text in one window
  captions   [{text, cue{...} | at, dur}] a lower-third bar over the whole page
  stills     [{src, cue{...} | at, dur, x, y, w}] a real screenshot or printout page (a file in the
             beat's assets/) over the windows, w px wide at x, y; fades in, holds dur seconds, fades out
"""
import html, json, os, re, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "screenkit")); import personal

spec = json.load(open("spec.json"))
min_gap = spec.get("min_gap", 0.4)
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

# ---------- colours and substitutions: the same as screenkit/build.py ----------
FG, BG = "#dadcdc", "#1c222c"
NAMED = {"black": "#000000", "red": "#c23621", "green": "#25bc24", "brown": "#adad27",
         "yellow": "#adad27", "blue": "#492ee1", "magenta": "#d338d3", "cyan": "#33bbc8",
         "white": "#cbcccd", "brightblack": "#818383", "brightred": "#fc391f",
         "brightgreen": "#31e722", "brightbrown": "#eaec23", "brightyellow": "#eaec23",
         "brightblue": "#5833ff", "brightmagenta": "#f935f8", "brightcyan": "#14f0f0",
         "brightwhite": "#e9ebeb"}
def blend(a, b, k=0.5):
    return "#" + "".join(f"{round(int(a[i:i+2], 16) * (1 - k) + int(b[i:i+2], 16) * k):02x}" for i in (1, 3, 5))
def colour(c, default):
    if c == "default": return default
    if re.fullmatch(r"[0-9a-fA-F]{6}", c): return "#" + c.lower()
    return NAMED.get(c, default)

def sub_row(runs, subs, cur_x=None):
    text = "".join(r[0] for r in runs)
    shift = 0
    if cur_x is not None:
        for a, b in subs.items():
            for m in re.finditer(re.escape(a), text[:cur_x]): shift += len(b) - len(a)
    out = []
    for r in runs:
        t = r[0]
        for a, b in subs.items(): t = t.replace(a, b)
        out.append([t, *r[1:]])
    for a, b in subs.items():
        if a in text and not any(a in r[0] for r in runs):
            if len(b) > len(a):
                sys.exit(f"substitution {a!r} is split across colour runs and longer; extend sub_row")
            cells = [[ch, i] for i, r in enumerate(out) for ch in r[0]]
            flat = "".join(c[0] for c in cells)
            for m in re.finditer(re.escape(a), flat):
                for k, ch in enumerate(b.ljust(len(a))): cells[m.start() + k][0] = ch
            for i, r in enumerate(out): r[0] = "".join(c[0] for c in cells if c[1] == i)
    return out, shift

def frame_html(f, subs):
    cx, cy, hidden = f["cur"]
    lines = []
    for y, runs in enumerate(f["rows"]):
        runs, shift = sub_row(runs, subs, cx if y == cy else None)
        cells = []
        for text, fg, bg, bold, rev, *more in runs:
            fgc, bgc = colour(fg, FG), colour(bg, BG)
            if more and more[0]: fgc = blend(fgc, bgc)
            if rev: fgc, bgc = bgc, fgc
            st = f"color:{fgc};" + (f"background:{bgc};" if bgc != BG else "") + ("font-weight:700;" if bold else "")
            cells += [(ch, st) for ch in text]
        if y == cy and not hidden:
            x = cx + shift
            while len(cells) <= x: cells.append((" ", f"color:{FG};"))
            cells[x] = (cells[x][0], f"color:{BG};background:{FG};")
        out, cur_st, buf = [], None, ""
        for ch, st in cells:
            if st != cur_st:
                if buf: out.append(f'<span style="{cur_st}">{html.escape(buf)}</span>')
                cur_st, buf = st, ""
            buf += ch
        if buf: out.append(f'<span style="{cur_st}">{html.escape(buf)}</span>')
        lines.append("".join(out))
    return "\n".join(lines)

# ---------- windows ----------
W = {}
for w in spec["windows"]:
    F = json.load(open(w["frames"]))
    W[w["id"]] = dict(w, cols=F["cols"], rows=F["rows"], fr=F["frames"], subs=w.get("subs", {}), placed=[])
ids = list(W)

def frame_at(win, t):
    k = 0
    for i, f in enumerate(W[win]["fr"]):
        if f["t"] <= t: k = i
        else: break
    return k

# ---------- schedule clips and segments ----------
clips = {c["id"]: dict(c, words=json.load(open(c["words"])), dur=duration(c["audio"])) for c in spec.get("clips", [])}
order = [c["id"] for c in spec.get("clips", [])]
if order: clips[order[0]]["start"] = spec["lead_in"]
cur, prev_end, warnings = (order[0] if order else None), None, []

def cue_time(cue):
    global cur
    if cue["clip"] != cur:
        for cid in order[order.index(cur) + 1: order.index(cue["clip"]) + 1]:
            p = clips[cur]
            clips[cid]["start"] = round(max(p["start"] + p["dur"], prev_end or 0) + spec["clip_gap"], 2)
            cur = cid
    c = clips[cue["clip"]]
    return c["start"] + find_cue(c["words"], cue["phrase"], cue.get("anchor", "start")) + cue.get("offset", 0)

def when(x):
    return x["at"] if "at" in x else cue_time(x["cue"])

last_seg = None
for seg in spec["segments"]:
    win = W[seg["win"]]
    if "cue" in seg or "at" in seg: t = when(seg)
    elif seg.get("with_prev"): t = last_seg["v0"] + seg.get("offset", 0)
    else: t = (prev_end or spec["lead_in"]) + seg.get("after_prev", min_gap)
    if win["placed"] and not win["placed"][-1].get("fill") and t < win["placed"][-1]["v1"] + min_gap:
        p = win["placed"][-1]["v1"] + min_gap
        warnings.append(f"{seg['win']} segment {seg['from']}-{seg['to']}: start {t:.2f}s pushed to {p:.2f}s")
        t = p
    end = t + (seg["to"] - seg["from"]) / seg.get("speed", 1.0)
    last_seg = dict(seg, v0=round(t, 3), v1=round(end, 3))
    win["placed"].append(last_seg)
    if not seg.get("fill"): prev_end = max(prev_end or 0, end)

# `fill` segments: in the background (they hold back no clip or later segment); the speed is set so the
# segment ends exactly as the same window's next segment starts -- one steady pace, no pause (a progress line's dots).
for wid in ids:
    pl = W[wid]["placed"]
    for i, sg in enumerate(pl):
        if not sg.get("fill"): continue
        if i + 1 == len(pl): sys.exit(f"{wid}: a fill segment needs a later segment in the same window")
        nxt = pl[i + 1]
        if abs(nxt["from"] - sg["to"]) > 0.01: sys.exit(f"{wid}: fill segment must end (to) where the next one starts (from)")
        if nxt["v0"] <= sg["v0"]: sys.exit(f"{wid}: no time left for the fill segment at {sg['v0']}s")
        sg["v1"] = nxt["v0"]; sg["speed"] = round((sg["to"] - sg["from"]) / (sg["v1"] - sg["v0"]), 4)

for i, cid in enumerate(order[1:], 1):
    if "start" not in clips[cid]:
        p = clips[order[i - 1]]
        clips[cid]["start"] = round(max(p["start"] + p["dur"], prev_end) + spec["clip_gap"], 2)
end_audio = max([clips[c]["start"] + clips[c]["dur"] for c in order] or [0])
total = round(max(end_audio, prev_end) + spec["tail"], 2)

# ---------- per window: frame timeline, frames, titles, checks ----------
out_w = []
for wid in ids:
    w = W[wid]
    if not w["placed"]: sys.exit(f"window {wid} has no segments")
    pl = w["placed"]
    tl = [(0.0, frame_at(wid, pl[0]["from"]))]
    for s in pl:
        sp = s.get("speed", 1.0)
        tl.append((s["v0"], frame_at(wid, s["from"])))
        for i, f in enumerate(w["fr"]):
            if s["from"] < f["t"] <= s["to"]:
                tl.append((round(s["v0"] + (f["t"] - s["from"]) / sp, 3), i))
    tl.sort(key=lambda x: x[0])
    w["tl"] = tl
    used = sorted({k for _, k in tl})
    hf = {k: frame_html(w["fr"][k], w["subs"]) for k in used}
    plain = {k: html.unescape(re.sub(r"<[^>]+>", "", h)) for k, h in hf.items()}
    for e in w.get("expect", []):
        if not any(e in p for p in plain.values()): sys.exit(f"{wid}: expected text not on any frame: {e!r}")
    for p in plain.values():
        for a in w["subs"]:
            if a in p: sys.exit(f"{wid}: substitution source still on screen: {a!r}")
        bad = personal.found(p)
        if bad: sys.exit(f"{wid}: personal name on screen: {bad!r} (add a subs entry)")
    def video_time(ct, pl=pl):
        for s in pl:
            if ct <= s["from"]: return s["v0"]
            if ct <= s["to"]: return s["v0"] + (ct - s["from"]) / s.get("speed", 1.0)
        return pl[-1]["v1"]
    titles = [[0.0, w["title"]]] + [[round(video_time(x["at"]), 3), x["title"]] for x in w.get("titles", [])]
    out_w.append({"id": wid, "x": w["x"], "y": w["y"], "font": w["font"], "cols": w["cols"], "rows": w["rows"],
                  "timeline": tl, "frames": {str(k): v for k, v in hf.items()}, "titles": titles,
                  "used": len(used)})

def shown_row(wid, v, row):
    w = W[wid]; k = w["tl"][0][1]
    for tv, i in w["tl"]:
        if tv <= v: k = i
        else: break
    runs, _ = sub_row(w["fr"][k]["rows"][row], w["subs"])
    return "".join(r[0] for r in runs).rstrip()

callouts = []
for c in spec.get("callouts", []):
    at = when(c)
    line = shown_row(c["win"], at + 0.05, c["row"])
    if c.get("line"):
        if not line.strip(): sys.exit(f"callout at {at:.2f}s: {c['win']} row {c['row']} is empty then")
        c0, c1 = len(line) - len(line.lstrip()), len(line) - 1
    else:
        i = -1
        for _ in range(c.get("nth", 1)):
            i = line.find(c["text"], i + 1)
            if i < 0: sys.exit(f"callout at {at:.2f}s: {c['text']!r} not on {c['win']} row {c['row']}: {line!r}")
        c0, c1 = i, i + len(c["text"]) - 1
    callouts.append({"win": ids.index(c["win"]), "at": round(at, 3), "dur": c["dur"], "r": c["row"], "c0": c0, "c1": c1})

focus = [[0.0, len(ids) - 1]] + sorted([round(when(f), 3), ids.index(f["win"])] for f in spec.get("focus", []))

captions = []
for c in spec.get("captions", []):
    parts = re.split(r"(`[^`]+`)", c["text"])
    h = "".join(f"<code>{html.escape(p[1:-1])}</code>" if p.startswith("`") else html.escape(p) for p in parts if p)
    captions.append({"at": round(when(c), 3), "dur": c["dur"], "html": h})

stills = []
for c in spec.get("stills", []):
    if not os.path.exists(c["src"]): sys.exit(f"still not found: {c['src']}")
    stills.append({"at": round(when(c), 3), "dur": c["dur"], "src": c["src"], "x": c["x"], "y": c["y"], "w": c["w"]})

audio = "\n      ".join(
    f'<audio id="narr-{cid}" src="{clips[cid]["audio"]}" data-start="{clips[cid]["start"]}" '
    f'data-duration="{clips[cid]["dur"]:.2f}" data-track-index="{i + 2}"></audio>'
    for i, cid in enumerate(order))
data = {"windows": out_w, "focus": focus, "callouts": callouts, "captions": captions, "stills": stills,
        "dips": [{"at": s["v0"], "dur": s["dip"]} for w in W.values() for s in w["placed"] if s.get("dip")]}
tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "duo.template")).read()
open("index.html", "w").write(tpl.replace("%%DATA%%", json.dumps(data, ensure_ascii=False))
                              .replace("%%DUR%%", str(total)).replace("%%AUDIO%%", audio))

for cid in order:
    print(f"clip {cid}: {clips[cid]['start']:6.2f}s -> {clips[cid]['start'] + clips[cid]['dur']:6.2f}s")
for wid in ids:
    for s in W[wid]["placed"]:
        print(f"  {wid:>8} {s['v0']:6.2f}-{s['v1']:6.2f}s  capture {s['from']}-{s['to']} x{s.get('speed', 1.0)}")
for v, i in focus: print(f"  front {v:6.2f}s  {ids[i]}")
for c in callouts: print(f"  callout {c['at']:6.2f}s for {c['dur']}s  {ids[c['win']]} row {c['r']}")
for c in captions: print(f"  caption {c['at']:6.2f}s for {c['dur']}s")
for c in stills: print(f"  still   {c['at']:6.2f}s for {c['dur']}s  {c['src']}")
print(", ".join(f"{w['id']} {w['used']} frames" for w in out_w) + f", total {total}s")
for w in warnings: print("WARNING:", w)
