#!/usr/bin/env python3
"""Replay a macOS `script -r` recording into timed, coloured screen frames.

    python3 rec2frames.py <capture.rec> <frames.json> <cols> <rows>

Needs pyte (pip install -r requirements.txt) and recio.py next to this file.

The screen size must be the size the capture was drawn at (look for full-width rules or zsh's
PROMPT_SP padding). Every output record is fed to pyte; a frame is kept whenever the screen or
cursor changed. Times are seconds from the first record. Input records (keys typed) are kept
too, as {"t", "keys"}, so a spec can find "the moment Enter was pressed".

Frame rows are runs: [text, fg, bg, bold, reverse, faint]; fg/bg are "default" or a 6-digit hex/name as
pyte reports them. faint = SGR 2 (e.g. Claude Code's grey hints and suggested replies): pyte has no
faint attribute, so Screen below keeps it in pyte's `blink` slot (so a program that blinks shows as
faint). No substitutions happen here: replace personal names when you build the beat, so the frames
file stays a faithful copy of the capture.
"""
import json, os, re, sys
import pyte

REC, OUT, COLS, ROWS = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])

class Screen(pyte.Screen):
    def report_device_status(self, *a, **k): pass          # no reply channel in a replay
    def select_graphic_rendition(self, *a, **k):
        k.pop("private", None)                              # ESC[>4m etc. (kitty keyboard modes)
        faint, i = None, 0                                  # SGR 2 on, 22 / 0 / bare off; skip the
        while i < len(a):                                   # arguments of 38/48 colours (38;2;r;g;b)
            v = a[i]
            if v in (38, 48) and i + 1 < len(a): i += 3 if a[i + 1] == 5 else 5; continue
            if v == 2: faint = True
            elif v in (0, 22): faint = False
            i += 1
        if not a: faint = False
        rest = [v for j, v in enumerate(a) if v != 2 or self._in_colour(a, j)]
        r = super().select_graphic_rendition(*rest, **k) if rest or not a else None
        if faint is not None: self.cursor.attrs = self.cursor.attrs._replace(blink=faint)
        return r
    @staticmethod
    def _in_colour(a, j):                                   # is a[j] inside a 38/48 colour's arguments?
        i = 0
        while i < len(a):
            if a[i] in (38, 48) and i + 1 < len(a):
                n = 3 if a[i + 1] == 5 else 5
                if i < j < i + n: return True
                i += n; continue
            i += 1
        return False

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recio
recs = recio.read(REC)
# Kitty keyboard-protocol sequences (ESC[<u, ESC[>1u, ESC[=..u, ESC[?u) are not in pyte's
# table; it would print their final "u" as text. A real Terminal.app ignores them.
KITTY = re.compile(rb"\x1b\[[<>=?][0-9;]*u")
t0 = recs[0][0]

scr = Screen(COLS, ROWS)
stream = pyte.ByteStream(scr)

def grab():
    rows = []
    for y in range(ROWS):
        line, runs = scr.buffer[y], []
        for x in range(COLS):
            c = line[x]
            key = (c.fg, c.bg, c.bold, c.reverse, c.blink)
            if runs and tuple(runs[-1][1:]) == key: runs[-1][0] += c.data
            else: runs.append([c.data, *key])
        # drop a trailing all-default blank run
        if runs and runs[-1][0].strip() == "" and runs[-1][2] == "default" and not runs[-1][4]:
            runs.pop()
        rows.append(runs)
    return {"rows": rows, "cur": [scr.cursor.x, scr.cursor.y, bool(scr.cursor.hidden)]}

frames, keys, last = [], [], None
for t, d, data in recs:
    if d == "o":
        stream.feed(KITTY.sub(b"", data))
        f = grab()
        sig = json.dumps(f)
        if sig != last:
            f["t"] = round(t - t0, 3); frames.append(f); last = sig
    elif d == "i":
        keys.append({"t": round(t - t0, 3), "keys": data.decode("utf-8", "replace")})

json.dump({"source": REC.rsplit("/", 1)[-1], "cols": COLS, "rows": ROWS,
           "span": round(recs[-1][0] - t0, 3), "frames": frames, "keys": keys},
          open(OUT, "w"), ensure_ascii=False)
print(f"{len(recs)} records, {len(frames)} frames, {len(keys)} key records, "
      f"{recs[-1][0] - t0:.1f} s")
