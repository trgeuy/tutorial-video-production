#!/usr/bin/env python3
"""Captions (.srt) from a whisper transcript of a final video.

Automatic captions mis-spell product names. This builds an .srt from your own whisper words
(timing) and fixes the words whisper also gets wrong, from a fixes file.

  python3 make_srt.py <transcript.json> <out.srt> [--fixes FILE ...] [--lead "<words>@<start>"]

transcript.json: [{"text": "word", "start": 1.23, "end": 1.45}, ...] (beat_words.py makes one).
--fixes: a text file, one fix per line: <regex> TAB <replacement> (# starts a comment line). Fixes
apply in order, to the whole transcript as one text, so a fix can span two captions. The
replacement is a Python re.sub() replacement (\\1 = group 1). Give --fixes more than once to use a
general file and a per-video file. See whisper-fixes.example.tsv.
--lead: words whisper dropped at the very start (it can drop the first few words); they go in
front of the first word, starting at <start> seconds.
Check the result: grep the .srt for anything the fixes missed, then word-diff it against the
script with srt_vs_script.py and judge each difference by ear.
"""
import argparse, json, re

MAX_CHARS, LINE, MAX_DUR, GAP = 84, 42, 6.0, 0.7

def load_fixes(paths):
    fixes = []
    for path in paths:
        for n, line in enumerate(open(path, encoding="utf-8"), 1):
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if line.count("\t") != 1:
                raise SystemExit(f"{path}:{n}: need exactly one TAB between regex and replacement")
            fixes.append(tuple(line.split("\t")))
    return fixes

def cues(words):
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        text = " ".join(x["text"] for x in cur)
        nxt = words[i + 1] if i + 1 < len(words) else None
        end_sent = w["text"][-1:] in ".?!"
        gap = nxt["start"] - w["end"] if nxt else 99
        longer = nxt and len(text) + 1 + len(nxt["text"]) > MAX_CHARS
        if (not nxt or gap > GAP or longer or cur[-1]["end"] - cur[0]["start"] > MAX_DUR
                or (end_sent and len(text) > 25)):
            out.append(cur); cur = []
    # whisper can stamp a sentence's last word late: the gap splits it into a caption of its own after
    # the sentence. Put a lone sentence-final word back on the unfinished caption before it.
    for i in range(len(out) - 1, 0, -1):
        prev, one = out[i - 1], out[i]
        if (len(one) == 1 and one[0]["text"][-1:] in ".?!" and prev[-1]["text"][-1:] not in ".?!,"
                and len(" ".join(x["text"] for x in prev + one)) <= MAX_CHARS):
            out[i - 1] = prev + one; del out[i]
        elif len(one) == 1 and len(prev) >= 6:  # too long to merge: give the lone word a few words of company
            out[i - 1], out[i] = prev[:-3], prev[-3:] + one
    return out

def fix(words, fixes):
    """Apply the fixes to the whole text (a phrase can span two captions), then give the new words the
    times of the old words they replace (difflib alignment; a replaced span shares its time range)."""
    import difflib
    text = " ".join(w["text"] for w in words)
    for pat, rep in fixes: text = re.sub(pat, rep, text)
    new = text.split()
    out = []
    sm = difflib.SequenceMatcher(None, [w["text"] for w in words], new, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            out += [dict(words[i1 + k], text=new[j1 + k]) for k in range(j2 - j1)]
        elif j2 > j1:
            a = words[i1]["start"] if i1 < len(words) else words[-1]["end"]
            b = words[i2 - 1]["end"] if i2 > i1 else a
            step = (b - a) / (j2 - j1)
            out += [{"text": new[j1 + k], "start": a + k * step, "end": a + (k + 1) * step} for k in range(j2 - j1)]
    return out

def wrap(text):
    if len(text) <= LINE: return text
    mid = len(text) // 2  # break at the space nearest the middle
    cands = [m.start() for m in re.finditer(" ", text)]
    k = min(cands, key=lambda c: abs(c - mid))
    return text[:k] + "\n" + text[k + 1:]

def ts(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def main():
    p = argparse.ArgumentParser(description="Captions (.srt) from a whisper transcript.")
    p.add_argument("src", help="whisper words .json")
    p.add_argument("dst", help="output .srt")
    p.add_argument("--fixes", action="append", default=[], metavar="FILE", help="fixes file (repeatable)")
    p.add_argument("--lead", metavar='"WORDS@START"', help="words whisper dropped at the start")
    a = p.parse_args()
    words = [w for w in json.load(open(a.src)) if w["text"].strip()]
    if a.lead:
        lead, at = a.lead.rsplit("@", 1)
        words = [{"text": t, "start": float(at), "end": float(at)} for t in lead.split()] + words
    groups = cues(fix(words, load_fixes(a.fixes)))
    with open(a.dst, "w") as f:
        for n, g in enumerate(groups, 1):
            text = " ".join(x["text"] for x in g)
            start = g[0]["start"]
            end = max(g[-1]["end"], start + 1.0)
            if n < len(groups): end = min(end, groups[n][0]["start"] - 0.05)
            f.write(f"{n}\n{ts(start)} --> {ts(end)}\n{wrap(text)}\n\n")
    print(f"{a.dst}: {len(groups)} captions")

main()
