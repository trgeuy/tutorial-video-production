#!/usr/bin/env python3
"""Build index.html for a replayed-terminal beat (screenkit). Run it from the beat's own folder:

    cd <beat folder> && python3 <repo>/kits/screenkit/build.py

The screen content is a frames file made by rec2frames.py from a REAL `script -r` capture (or a
compose.py join of real captures). This script only decides WHEN each part plays and applies the
spec's substitutions; it never changes what the capture drew.

spec.json:
  frames     frames file (rec2frames.py output)
  title      window title, e.g. "user — -zsh — 120×30"
  subs       {"from": "to"} applied to screen text (names, e-mail, paths)
  lead_in, clip_gap, min_gap, tail   seconds, as in termkit
  clips      [{id, audio, words}] -- play one after another (see termkit/build.py). May be empty:
             then segments, callouts and captions take a fixed video time `at` instead of a `cue`
  segments   [{from, to, speed, dip, cue{clip, phrase, anchor, offset} | after_prev}]
             dip = seconds: fade the picture to black for that long BEFORE the segment, switch to it while
             black, fade back in over the same time (a visible cut, e.g. inside a long wait). Give the
             segment after_prev >= dip so the fade-out has room.
             from/to = capture seconds. The segment's frames play from its start time at `speed`
             (1 = real time). Between segments the last frame holds. Before the first segment the
             screen shows the capture's state at the first segment's `from`.
  callouts   [{..., cue{...} | at_segment, dur}] a box round cells, given EITHER as
             {row, text, nth} (found on the frame showing at that moment, after subs -- preferred),
             {row, line: true} (the whole line), or {row0, row1, col0, col1} (raw numbers)
  expect     [text] strings that must appear on some frame of the result (checked at build)
  captions   [{text, cue{...}, dur}] a lower-third caption bar; `text` may hold `code` in backticks
  overlays   [{img, width, cue{...}, until{clip, phrase} | dur}] a still (a real screenshot) centred over
             the window from the cue until the `until` phrase ends (+0.3 s), with short fades
  titles     [{at, title}] window title from capture time `at` on (default: spec "title"), e.g.
             the prompt's "user — -zsh — 120×30", then "user — claude — 120×30" once it runs
"""
import html, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import personal

spec = json.load(open("spec.json"))
F = json.load(open(spec["frames"]))
COLS, ROWS = F["cols"], F["rows"]
frames = F["frames"]
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

# ---------- colours (Terminal.app-like; default fg/bg match termkit) ----------
FG, BG = "#dadcdc", "#1c222c"
NAMED = {"black": "#000000", "red": "#c23621", "green": "#25bc24", "brown": "#adad27",
         "yellow": "#adad27", "blue": "#492ee1", "magenta": "#d338d3", "cyan": "#33bbc8",
         "white": "#cbcccd", "brightblack": "#818383", "brightred": "#fc391f",
         "brightgreen": "#31e722", "brightbrown": "#eaec23", "brightyellow": "#eaec23",
         "brightblue": "#5833ff", "brightmagenta": "#f935f8", "brightcyan": "#14f0f0",
         "brightwhite": "#e9ebeb"}
def blend(a, b, k=0.5):              # colour a, k of the way to colour b (#rrggbb)
    return "#" + "".join(f"{round(int(a[i:i+2], 16) * (1 - k) + int(b[i:i+2], 16) * k):02x}" for i in (1, 3, 5))
def colour(c, default):
    if c == "default": return default
    if re.fullmatch(r"[0-9a-fA-F]{6}", c): return "#" + c.lower()
    return NAMED.get(c, default)

# ---------- substitutions: text, with the cursor shifted on its own row ----------
subs = spec.get("subs", {})
def sub_row(runs, cur_x=None):
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
    for a, b in subs.items():                         # a match split across colour runs (e.g. Claude
        if a in text and not any(a in r[0] for r in runs):  # Code's own reverse-video cursor cell)
            if len(b) > len(a):
                sys.exit(f"substitution {a!r} is split across colour runs and longer; extend sub_row")
            cells = [[ch, i] for i, r in enumerate(out) for ch in r[0]]
            flat = "".join(c[0] for c in cells)        # cell by cell, padded with spaces: each cell
            for m in re.finditer(re.escape(a), flat):  # keeps its own run's colours
                for k, ch in enumerate(b.ljust(len(a))): cells[m.start() + k][0] = ch
            for i, r in enumerate(out): r[0] = "".join(c[0] for c in cells if c[1] == i)
    return out, shift

def frame_html(f):
    cx, cy, hidden = f["cur"]
    lines, carry = [], []
    for y, runs in enumerate(f["rows"]):
        runs, shift = sub_row(runs, cx if y == cy else None)
        cells = []                                     # (char, style) per column
        for text, fg, bg, bold, rev, *more in runs:
            fgc, bgc = colour(fg, FG), colour(bg, BG)
            if more and more[0]: fgc = blend(fgc, bgc)          # faint (SGR 2): half intensity
            if rev: fgc, bgc = bgc, fgc
            st = f"color:{fgc};" + (f"background:{bgc};" if bgc != BG else "") + ("font-weight:700;" if bold else "")
            cells += [(ch, st) for ch in text]
        # A longer substitution (jo@Mac -> user@Macbook) on a FULL row of a soft-wrapped line pushes
        # its end past the last column; a real terminal would have wrapped it one cell earlier. Carry the
        # overflow to the start of the next row (the wrapped continuation), as the terminal would draw it.
        if carry:
            cells = carry + cells
            if y == cy: shift += len(carry)
            carry = []
        if len(cells) > COLS:
            over = cells[COLS:]
            if "".join(c for c, _ in over).strip():
                carry = over
                while carry and carry[-1][0] == " ": carry.pop()
            cells = cells[:COLS]
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

def frame_at(t):
    k = 0
    for i, f in enumerate(frames):
        if f["t"] <= t: k = i
        else: break
    return k

# ---------- schedule clips and segments (termkit's rules) ----------
clips = {c["id"]: dict(c, words=json.load(open(c["words"])), dur=duration(c["audio"])) for c in spec.get("clips", [])}
order = [c["id"] for c in spec.get("clips", [])]
if order: clips[order[0]]["start"] = spec["lead_in"]
cur, prev_end, warnings, placed = (order[0] if order else None), None, [], []

def cue_time(cue):
    global cur
    if cue["clip"] != cur:
        for cid in order[order.index(cur) + 1: order.index(cue["clip"]) + 1]:
            p = clips[cur]
            clips[cid]["start"] = round(max(p["start"] + p["dur"], prev_end or 0) + spec["clip_gap"], 2)
            cur = cid
    c = clips[cue["clip"]]
    return c["start"] + find_cue(c["words"], cue["phrase"], cue.get("anchor", "start")) + cue.get("offset", 0)

def when(x):                         # a fixed video time (`at`, for beats with no narration yet) or a cue
    return x["at"] if "at" in x else cue_time(x["cue"])

for seg in spec["segments"]:
    t = when(seg) if ("cue" in seg or "at" in seg) else (prev_end or spec["lead_in"]) + seg.get("after_prev", min_gap)
    if prev_end is not None and t < prev_end + min_gap:
        warnings.append(f"segment {seg['from']}-{seg['to']}: cue at {t:.2f}s pushed to {prev_end + min_gap:.2f}s")
        t = prev_end + min_gap
    sp = seg.get("speed", 1.0)
    end = t + (seg["to"] - seg["from"]) / sp
    placed.append(dict(seg, v0=round(t, 3), v1=round(end, 3)))
    prev_end = end

for i, cid in enumerate(order[1:], 1):
    if "start" not in clips[cid]:
        p = clips[order[i - 1]]
        clips[cid]["start"] = round(max(p["start"] + p["dur"], prev_end) + spec["clip_gap"], 2)
end_audio = max([clips[c]["start"] + clips[c]["dur"] for c in order] or [0])
total = round(max(end_audio, prev_end) + spec["tail"], 2)

# ---------- frame timeline: [(video time, frame index)] ----------
timeline = [(0.0, frame_at(placed[0]["from"]))]
for s in placed:
    sp = s.get("speed", 1.0)
    timeline.append((s["v0"], frame_at(s["from"])))
    for i, f in enumerate(frames):
        if s["from"] < f["t"] <= s["to"]:
            timeline.append((round(s["v0"] + (f["t"] - s["from"]) / sp, 3), i))
used = sorted({k for _, k in timeline})
html_frames = {k: frame_html(frames[k]) for k in used}

for e in spec.get("expect", []):
    if not any(e in re.sub(r"<[^>]+>", "", html.unescape(h)) or e in html.unescape(re.sub(r"<[^>]+>", "", h))
               for h in html_frames.values()):
        sys.exit(f"expected text not on any frame: {e!r}")
for h in html_frames.values():
    plain = html.unescape(re.sub(r"<[^>]+>", "", h))
    for a in subs:
        if a in plain: sys.exit(f"substitution source still on screen: {a!r}")
    bad = personal.found(plain)
    if bad: sys.exit(f"personal name on screen: {bad!r} (add a subs entry)")

def video_time(ct):
    """Video time at which capture time ct shows (held stretches map to the next segment start)."""
    for s in placed:
        if ct <= s["from"]: return s["v0"]
        if ct <= s["to"]: return s["v0"] + (ct - s["from"]) / s.get("speed", 1.0)
    return placed[-1]["v1"]

titles = [[0.0, spec["title"]]] + [[round(video_time(x["at"]), 3), x["title"]] for x in spec.get("titles", [])]

def shown_row(v, row):
    """Screen text of `row` (after subs) on the frame showing at video time v."""
    k = timeline[0][1]
    for tv, i in timeline:
        if tv <= v: k = i
        else: break
    runs, _ = sub_row(frames[k]["rows"][row])
    return "".join(r[0] for r in runs).rstrip()

callouts = []
for c in spec.get("callouts", []):
    at = when(c) if ("cue" in c or "at" in c) else placed[c["at_segment"]]["v1"]
    if "text" in c or c.get("line"):
        line = shown_row(at + 0.05, c["row"])
        if c.get("line"):
            if not line.strip(): sys.exit(f"callout at {at:.2f}s: row {c['row']} is empty then")
            c0, c1 = len(line) - len(line.lstrip()), len(line) - 1
        else:
            i = -1
            for _ in range(c.get("nth", 1)):
                i = line.find(c["text"], i + 1)
                if i < 0: sys.exit(f"callout at {at:.2f}s: {c['text']!r} not on row {c['row']}: {line!r}")
            c0, c1 = i, i + len(c["text"]) - 1
        r0 = r1 = c["row"]
    else:
        r0, r1, c0, c1 = c["row0"], c["row1"], c["col0"], c["col1"]
    callouts.append({"at": round(at, 3), "dur": c["dur"], "r0": r0, "r1": r1, "c0": c0, "c1": c1})

captions = []
for c in spec.get("captions", []):
    parts = re.split(r"(`[^`]+`)", c["text"])
    h = "".join(f"<code>{html.escape(p[1:-1])}</code>" if p.startswith("`") else html.escape(p) for p in parts if p)
    captions.append({"at": round(when(c), 3), "dur": c["dur"], "html": h})

overlays = []                        # a real screenshot over the window, from a cue until a phrase ends
for o in spec.get("overlays", []):
    at = cue_time(o["cue"])
    dur = cue_time({**o["until"], "anchor": "end"}) + 0.3 - at if "until" in o else o["dur"]
    if dur <= 0: sys.exit(f"overlay {o['img']}: 'until' ends before the cue")
    overlays.append({"img": o["img"], "at": round(at, 3), "dur": round(dur, 3), "width": o["width"]})

audio = "\n      ".join(
    f'<audio id="narr-{cid}" src="{clips[cid]["audio"]}" data-start="{clips[cid]["start"]}" '
    f'data-duration="{clips[cid]["dur"]:.2f}" data-track-index="{i + 1}"></audio>'
    for i, cid in enumerate(order))
# not 120x30: scale the 22 px font by the smaller of the two ratios (fits inside the 1700x960 window), and
# let the template size the window to the grid. `font` in spec.json overrides the size.
fit = None if (COLS, ROWS) == (120, 30) else {"font": spec.get("font", int(min(22 * 120 / COLS, 22 * 30 / ROWS)))}
data = {"titles": titles, "cols": COLS, "rows": ROWS, "timeline": timeline, "fit": fit,
        "frames": {str(k): v for k, v in html_frames.items()}, "callouts": callouts,
        "dips": [{"at": s["v0"], "dur": s["dip"]} for s in placed if s.get("dip")],
        "captions": captions, "overlays": overlays}
tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "screen.template")).read()
ov_html = "".join(f'<img class="overlay" id="ov{i}" src="{o["img"]}" style="width:{o["width"]}px" />'
                  for i, o in enumerate(overlays))
open("index.html", "w").write(tpl.replace("%%DATA%%", json.dumps(data, ensure_ascii=False))
                              .replace("%%OVERLAYS%%", ov_html)
                              .replace("%%DUR%%", str(total)).replace("%%AUDIO%%", audio))

for cid in order:
    print(f"clip {cid}: {clips[cid]['start']:6.2f}s -> {clips[cid]['start'] + clips[cid]['dur']:6.2f}s")
for s in placed:
    print(f"  {s['v0']:6.2f}-{s['v1']:6.2f}s  capture {s['from']}-{s['to']} x{s.get('speed', 1.0)}")
for c in callouts: print(f"  callout {c['at']:6.2f}s for {c['dur']}s rows {c['r0']}-{c['r1']}")
for v, ttl in titles: print(f"  title {v:6.2f}s  {ttl}")
for c in captions: print(f"  caption {c['at']:6.2f}s for {c['dur']}s")
for o in overlays: print(f"  overlay {o['at']:6.2f}s for {o['dur']}s  {o['img']}")
print(f"{len(used)} frames used, total {total}s")
for w in warnings: print("WARNING:", w)
