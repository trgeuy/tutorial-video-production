#!/usr/bin/env python3
"""Build index.html for a title card. Run it from the card's own folder:

    cd <card folder> && python3 <repo>/kits/cardkit/build.py

spec.json: title, subtitle, clips [{id, audio}] (optional; they play back to back, clip_gap apart,
from lead_in), lines [{text, clip | at}] (each line appears when its clip starts, or at `at` s; `backticks` = code),
compact (true: smaller, tighter lines for a long list), hold (seconds after
the last clip, or the whole card length when there are no clips).
"""
import html, json, subprocess

spec = json.load(open("spec.json"))
def code(text):  # `backticks` = code, as screenkit captions
    parts = html.escape(text).split("`")
    return "".join(f"<code>{p}</code>" if i % 2 else p for i, p in enumerate(parts))
def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    return float(out.stdout)

t, starts, audio = spec.get("lead_in", 0.8), {}, []
for i, c in enumerate(spec.get("clips", [])):
    d = duration(c["audio"])
    starts[c["id"]] = round(t, 2)
    audio.append(f'<audio id="narr-{c["id"]}" src="{c["audio"]}" data-start="{starts[c["id"]]}" '
                 f'data-duration="{d:.2f}" data-track-index="{i + 1}"></audio>')
    t += d + spec.get("clip_gap", 0.6)
total = round((t - spec.get("clip_gap", 0.6) if audio else 0) + spec["hold"], 2)
lines = spec.get("lines", [])
# compact: smaller, tighter lines and a higher box, for a card with many lines (a folder tree)
COMPACT = ("#box { top: 120px; } #title { font-size: 64px; } #sub { margin-top: 16px; font-size: 36px; } "
           "#rule { margin-top: 28px; } .line { margin-top: 14px; font-size: 30px; white-space: pre; } "
           ".line code { font-size: 28px; }")
out = (open(__file__.rsplit("/", 1)[0] + "/card.template").read()
       .replace("%%TITLE%%", html.escape(spec["title"]))
       .replace("%%SUB%%", html.escape(spec.get("subtitle", "")))
       .replace("%%LINES%%", "\n        ".join(f'<div class="line" id="line{i}">{code(l["text"])}</div>' for i, l in enumerate(lines)))
       .replace("%%LINE_TIMES%%", json.dumps([starts[l["clip"]] if "clip" in l else l.get("at", spec.get("lead_in", 0.8)) for l in lines]))
       .replace("%%EXTRA_CSS%%", COMPACT if spec.get("compact") else "")
       .replace("%%AUDIO%%", "\n      ".join(audio))
       .replace("%%DUR%%", str(total)))
open("index.html", "w").write(out)
print(f"total {total}s", starts)
