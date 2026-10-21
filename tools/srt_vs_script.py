#!/usr/bin/env python3
"""Word-diff an .srt against the narration script: lists every place where the caption words differ
from the script, so each one can be judged (whisper error vs reworded line).
  python3 srt_vs_script.py <file.srt> <script.md> [--say]

Script format: narration lines start with "> " (a Markdown quote). Text in _(...)_ or *(...)* on
those lines is a stage note and is ignored. --say: only "> " lines inside blocks whose heading line
starts with **SAY (any other **... line ends the block); without it, every "> " line counts."""
import re, sys, difflib
srt, md = sys.argv[1], sys.argv[2]
cap = " ".join(l for l in open(srt).read().split("\n") if l and not l.isdigit() and "-->" not in l)
lines, on = [], "--say" not in sys.argv
for l in open(md):
    if l.startswith("**SAY"): on = True; continue
    if l.startswith("**") and "--say" in sys.argv: on = False
    if on and l.startswith("> "): lines.append(re.sub(r"_\(.*?\)_|\*\(.*?\)\*", "", l[2:]))
norm = lambda s: [w.strip(".,?:") for w in re.sub(r"[^\w./'+-]+", " ", s.lower().replace("—", " ")).split()]
a, b = norm(" ".join(lines)), norm(cap)
for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
    if op != "equal":
        ctx = " ".join(b[max(0, j1 - 4):j1])
        print(f"{op:7} script: {' '.join(a[i1:i2])!r:40} captions: {' '.join(b[j1:j2])!r:40} ...{ctx}")
