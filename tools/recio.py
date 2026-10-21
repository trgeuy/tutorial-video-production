"""Read, cut and compose macOS `script -r` recordings.

A record is (t, dir, bytes): t = epoch seconds, dir = "i" (keys), "o" (output), "s"/"e" (start/end).
A compose script cuts REAL records out of captures and joins them, adding typed commands only where
a capture lost them -- list each addition in the beat's notes.
"""
import struct

def _header(b, i, prev_sec):
    if i + 24 > len(b): return None
    ln, sec, usec, d = struct.unpack("<QQII", b[i:i + 24])
    ok = (ln <= len(b) - i - 24 and usec < 1_000_000 and d in (0x69, 0x6f, 0x73, 0x65)
          and (prev_sec is None or 0 <= sec - prev_sec < 3600))
    return (ln, sec, usec, d) if ok else None

def read(path, start=0, report=True):
    """Records from byte offset `start`. Stray bytes (a header that does not fit: bad length,
    direction, or a time going backwards) are skipped up to the next plausible header."""
    b, i, prev, recs = open(path, "rb").read(), start, None, []
    while i + 24 <= len(b):
        h = _header(b, i, prev)
        if h is None:
            j = i + 1
            while j + 24 <= len(b) and _header(b, j, prev) is None: j += 1
            if report: print(f"{path.rsplit('/', 1)[-1]}: skipped {j - i} stray bytes at {i}")
            i = j; continue
        ln, sec, usec, d = h; i += 24
        recs.append((sec + usec / 1e6, chr(d), b[i:i + ln])); i += ln; prev = sec
    return recs

def write(path, recs):
    with open(path, "wb") as f:
        for t, d, data in recs:
            sec = int(t); usec = int(round((t - sec) * 1e6))
            if usec >= 1_000_000: sec += 1; usec -= 1_000_000
            f.write(struct.pack("<QQII", len(data), sec, usec, ord(d)) + data)

def between(recs, t0, t1):
    """Records with t0 <= t < t1 (epoch seconds)."""
    return [r for r in recs if t0 <= r[0] < t1]

def typed(text, t, cps=12.0):
    """Keys + shell echo for `text` typed at `cps` characters per second, starting at t.
    Returns (records, end time). Ends without Enter; add enter() for that."""
    out, dt = [], 1.0 / cps
    for ch in text:
        out.append((t, "i", ch.encode())); out.append((t + 0.001, "o", ch.encode())); t += dt
    return out, t

def enter(t):
    """Return key as zsh echoes it with bracketed paste on (ESC[?2004l). Another shell or line
    editor echoes Enter differently: copy its bytes from one of your own captures."""
    return [(t, "i", b"\r"), (t + 0.001, "o", b"\x1b[?2004l\r\r\n")], t + 0.01

def zsh_prefix(line, cmd, cols, cps=18, start=0.8, enter_lag=0.35):
    """zsh's prompt + a typed command, to put in front of a capture that `script -r <file> <program>`
    started directly (it has no prompt and no command). `line` = your prompt's bytes, copied from one
    of your own captures; zsh's PROMPT_SP mark is padded to cols-1 spaces. Typing at `cps` keys/s from
    `start` s, Enter `enter_lag` s after the last key. Returns (records, P): the capture's own first
    record goes at P s after the prefix starts (times from 0: shift() both to place them)."""
    sp = b"\x1b[1m\x1b[7m%\x1b[27m\x1b[1m\x1b[0m" + b" " * (cols - 1) + b"\r \r"
    pre, t = [(0.0, "o", sp), (0.001, "o", line + b"\x1b[?2004h")], start
    for ch in cmd:
        pre += [(t, "i", bytes([ch])), (t + 0.001, "o", bytes([ch]))]; t += 1 / cps
    t += enter_lag - 1 / cps
    pre += [(t, "i", b"\r"), (t + 0.001, "o", b"\x1b[?2004l\r\r\n")]
    return pre, round(t + 0.05, 3)

def shift(recs, dt):
    return [(t + dt, d, x) for t, d, x in recs]

# ---------- pacing: steady typing inside chosen stretches ----------
import re as _re
_REDRAW = _re.compile(rb"(\r[^\r\x1b]*\x1b\[K)")          # a line editor's per-key redraw: \r<prompt><text>ESC[K

def _split_echo(x):
    """An echo record -> one piece per typed key: plain printable text is split per byte; a run of line-editor
    redraws (\\r...ESC[K, as some line editors draw each key) per redraw. Anything else stays whole."""
    if x and all(32 <= c < 127 for c in x): return [bytes([c]) for c in x]
    parts = [p for p in _REDRAW.split(x) if p]
    if len(parts) > 1 and all(_REDRAW.fullmatch(p) for p in parts): return parts
    return [x]

def pace(recs, windows, cps=18, enter_lag=0.35, max_pause=0.6, max_out=1.5):
    """Re-time typing inside `windows` [(t0, t1)] (epoch seconds) at a steady `cps`:
      - a typed key comes 1/cps after the previous key (pauses while typing a line are dropped);
      - a paste's echo is spread one key per 1/cps, so a pasted line looks typed like the rest;
      - Enter comes `enter_lag` after the last key; any other pause is capped at `max_pause` (before an
        input) or `max_out` (before output that is not an echo, e.g. a program's run).
    Characters and their order never change -- only times. Everything after a window shifts with it.
    Returns (new records, timemap); timemap = [(old t, new t)] per input record, for spec segments."""
    recs = sorted(recs, key=lambda r: r[0])
    out, tmap = [], []
    prev_old = prev_new = None
    last_key = spreading = False
    for t, d, x in recs:
        inside = any(a <= t < b for a, b in windows)
        if prev_old is None or not inside:
            new = t if prev_old is None else prev_new + (t - prev_old)
            out.append((new, d, x)); tmap.append((t, new))
            prev_old, prev_new, last_key, spreading = t, new, False, False
            continue
        g = t - prev_old
        if d == "i":
            if x == b"\r": step = enter_lag
            elif len(x) == 1 and 32 <= x[0] < 127: step = 1 / cps if last_key else min(g, max_pause)
            else: step = min(g, max_pause)                    # a paste, ^E, an arrow key ...
            prev_new += step
            out.append((prev_new, d, x)); tmap.append((t, prev_new))
            paste = len(x) > 1 and (x.startswith(b"\x1b[200~") or not x.startswith(b"\x1b"))  # bracketed or raw
            last_key = x != b"\r" and (len(x) == 1 or paste)
            spreading = paste
        elif g < 0.05:                                          # an echo of the last input
            for n, p in enumerate(_split_echo(x)):
                prev_new += (1 / cps) if spreading else (g if n == 0 else 0.0)
                out.append((prev_new, d, p))
            tmap.append((t, prev_new))
        else:                                                   # other output: keep, pauses capped
            prev_new += min(g, max_out)
            out.append((prev_new, d, x)); tmap.append((t, prev_new))
            last_key = spreading = False
        prev_old = t
    return out, tmap

def remap(tmap, t):
    """Old time -> new time by a pace() timemap (linear between entries; same zero as the map)."""
    import bisect
    olds = [a for a, b in tmap]
    i = bisect.bisect_right(olds, t) - 1
    if i < 0: return tmap[0][1] + (t - tmap[0][0])
    if i + 1 >= len(tmap): return tmap[-1][1] + (t - tmap[-1][0])
    (a0, b0), (a1, b1) = tmap[i], tmap[i + 1]
    return b0 if a1 == a0 else b0 + (b1 - b0) * (t - a0) / (a1 - a0)
