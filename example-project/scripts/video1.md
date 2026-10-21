# Video 1: the example video

Two beats: a title card, then one replayed terminal recording (`captures/demo.rec`).
Narration lines start with `> `: `tools/srt_vs_script.py` reads them. The **timing words** of each
line are in bold: a beat's cue phrase. If a recording changes them, change the cue in the beat's
`spec.json` too.

## Beat 1: card-title (cardkit)

Clip `title-1`:

> This example video shows the whole method on **two short beats**.

## Beat 2: demo-terminal (screenkit)

Clip `term-1`:

> First we run a **short command**, and it prints one line of text.

Clip `term-2`:

> Next, a **slow job** runs for eight seconds. We **speed up the wait**, so you never watch the
> screen for nothing.

Clip `term-3`:

> At the end, **the green line** tells us that all checks passed.
