"""Edits that compose scripts make again and again on `script -r` captures of zsh + Claude Code. Each one asserts what it expects, so a different capture fails loudly.
Records are recio's (t, dir, bytes) with absolute times.
"""
import re

PROMPT_START = b"\r\x1b[0m\x1b[27m\x1b[24m\x1b[J"          # zsh's prompt line starts with this
_TOKEN = re.compile(rb"\x1b\[[0-9;?]*[A-Za-z]|\r\r\n|.", re.S)

def drop_restored(recs, required=True):
    """Drop Terminal's "Restored session: <date>" line at the start (start after it).
    required=False: a capture from a NEW Terminal window has no such line; return it unchanged."""
    k = [i for i, (t, d, x) in enumerate(recs[:4]) if d == "o" and x.startswith(b"Restored session: ")]
    if not k and not required: return recs
    assert len(k) == 1, recs[:4]
    return recs[:k[0]] + recs[k[0] + 1:]

def plain_pastes(recs, expect=None):
    """zsh's reverse-video paste echo -> plain text, one record per key, so recio.pace types it (series rule 3).
    `expect`: the list of pasted texts, in order (asserted; a line break as "\\n")."""
    out, seen = [], []
    for t, d, x in recs:
        if d == "o" and x.startswith(b"\x1b[7m"):
            x = x.replace(b"\x1b[7m", b"").replace(b"\x1b[27m", b"")
            seen.append(x)
            out += [(t + n * 1e-5, d, p) for n, p in enumerate(_TOKEN.findall(x))]
        else: out.append((t, d, x))
    if expect is not None:     # compared as text: zsh's ESC[K dropped, CR CR LF read as a newline
        norm = lambda b: b.replace(b"\x1b[K", b"").replace(b"\r\r\n", b"\n")
        assert [norm(s) for s in seen] == expect, [norm(s) for s in seen]
    return out

def claude_exit(recs, t0, prompt_line):
    """Claude Code's /exit as the viewer's terminal shows it. /exit leaves the ALTERNATE screen; pyte has none, so the
    replay garbles the "Resume this session with" lines over Claude's last frame. Here: clear, draw the normal screen
    (the prompt line where `claude` was typed), the REAL resume lines, then zsh's REAL next prompt. Everything after
    that prompt (the user's `exit`) is dropped. prompt_line = the prompt text, e.g. b"user@Macbook demo % "."""
    k = next(i for i, (t, d, x) in enumerate(recs) if d == "o" and b"Resume this session with:" in x)
    assert any(d == "o" and b"\x1b[?1049l" in x for t, d, x in recs[k - 8:k]), "no alternate-screen exit before it"
    j = next(i for i in range(k + 1, len(recs)) if recs[i][1] == "o" and PROMPT_START + prompt_line in recs[i][2])
    tail = recs[k + 1:j + 1]
    while j + 1 < len(recs) and recs[j + 1][1] == "o" and recs[j + 1][2].startswith(b"\x1b[K"):   # \e[K \e[?2004h
        j += 1; tail.append(recs[j])
    assert not any(d == "i" for t, d, x in tail), tail
    rt = recs[k][0]
    return recs[:k] + [(rt, "o", b"\x1b[H\x1b[2J\x1b[0m" + prompt_line + b"claude\r\n"), (rt + 0.0005, "o", recs[k][2])] + tail

def stop_before(recs, t_abs, want_keys=None):
    """Drop every record from t_abs on; if want_keys, assert the dropped keys are exactly those bytes."""
    if want_keys is not None:
        got = b"".join(x for t, d, x in recs if d == "i" and t >= t_abs)
        assert got == want_keys, got
    return [r for r in recs if r[0] < t_abs]

def keys_between(recs, a_abs, b_abs):
    return b"".join(x for t, d, x in recs if d == "i" and a_abs <= t <= b_abs)

def merge_paste_ends(recs):
    """zsh records a multi-line paste as TWO input records: the text (starting ESC[200~) and a separate ESC[201~.
    recio.pace saw the lone ESC[201~ as a new key and stopped spreading the paste's echo, so a multi-line paste
    appeared at once (seen in a real capture). Join each lone ESC[201~ onto the input record before it.
    Inputs are never drawn, so the screen does not change -- only the pacing."""
    out = []
    for r in recs:
        if r[1] == "i" and r[2] == b"\x1b[201~":
            k = max(i for i, q in enumerate(out) if q[1] == "i")
            assert out[k][2].startswith(b"\x1b[200~") and b"\x1b[201~" not in out[k][2], out[k]
            out[k] = (out[k][0], "i", out[k][2] + r[2]); continue
        out.append(r)
    return out

def rename_paste(recs, old, new):
    """Show a pasted command as `new` in place of `old` (an approved edit, e.g. `mirror-watch serial` ->
    `serial-watch` after the tool's rename; its output is byte-identical). Rewrites the three records zsh makes for one
    pasted line -- the keys (ESC[200~ old ESC[201~), the reverse-video echo, and Enter's redraw (ESC[nD, then each
    character after ESC[27m) -- and asserts each is found exactly once."""
    pairs = [(b"\x1b[200~" + old + b"\x1b[201~", b"\x1b[200~" + new + b"\x1b[201~", "i"),
             (b"\x1b[7m" + old + b"\x1b[27m", b"\x1b[7m" + new + b"\x1b[27m", "o"),
             (b"\x1b[%dD" % len(old) + b"".join(b"\x1b[27m" + bytes([c]) for c in old),
              b"\x1b[%dD" % len(new) + b"".join(b"\x1b[27m" + bytes([c]) for c in new), "o")]
    out = list(recs)
    for a, b, d in pairs:
        ks = [i for i, r in enumerate(out) if r[1] == d and a in r[2]]
        assert len(ks) == 1, (a, ks)
        out[ks[0]] = (out[ks[0]][0], d, out[ks[0]][2].replace(a, b))
    return out

def drop_paste_line(recs, line):
    """Remove one line from a multi-line zsh paste (an approved edit, e.g. `-e SERIAL_MCP_PACED=1 \\` after
    pacing became the server's default in v0.2.5; `claude mcp add` prints no settings, so its output is unchanged).
    Run on the RAW records, before merge_paste_ends / plain_pastes. Edits the paste's keys (the line + its CR) and its
    reverse-video echo (the line + ESC[K CR CR LF), and drops zsh's Enter redraw of that paste: it rewrites every line
    after moving up by the OLD line count, so it would draw the removed line back. plain_pastes already shows the
    paste as plain text, so the redraw changes nothing visible -- the cursor is already at the paste's end."""
    out = list(recs)
    key = [i for i, r in enumerate(out) if r[1] == "i" and r[2].startswith(b"\x1b[200~") and line + b"\r" in r[2]]
    assert len(key) == 1, key
    k = key[0]
    out[k] = (out[k][0], "i", out[k][2].replace(line + b"\r", b""))
    echo = b"\x1b[7m" + line + b"\x1b[27m\x1b[K\r\r\n"
    e = [i for i, r in enumerate(out) if r[1] == "o" and echo in r[2]]
    assert len(e) == 1, e
    out[e[0]] = (out[e[0]][0], "o", out[e[0]][2].replace(echo, b""))
    enter = next(i for i in range(k + 1, len(out)) if out[i][1] == "i" and out[i][2] != b"\x1b[201~")
    assert out[enter][2] == b"\r", out[enter]
    rd = enter + 1
    assert out[rd][1] == "o" and out[rd][2].startswith(b"\x1b[") and b"A\x1b[3C\x1b[27m" in out[rd][2][:16], out[rd][2][:20]
    assert out[rd + 1][2] == b"\x1b[?2004l\r\r\n", out[rd + 1]
    del out[rd]
    return out
