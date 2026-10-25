# Tools

## Third-party tools

| Tool | What we use it for | Notes |
|---|---|---|
| [HyperFrames](https://github.com/heygen-com/hyperframes) (`npx hyperframes`) | Renders a beat's HTML page to MP4. Its `transcribe --engine whisper` command gives the time of every word. | [npm package](https://www.npmjs.com/package/hyperframes), Apache-2.0. We pinned version 0.8.77 for the whole series; check the current one before you start, then keep that pin to the end of the video. No install step: `npx` downloads the pinned version (and HyperFrames its headless Chrome) the first time a command runs. Set `HYPERFRAMES_NO_UPDATE_CHECK=1` (no "Bump it" line), `HYPERFRAMES_NO_TELEMETRY=1` (no anonymous usage data) and `HYPERFRAMES_SKIP_SKILLS=1` (no skill install) for every command. `npx hyperframes@<pin> doctor` checks Node, ffmpeg, Chrome and whisper; its Version, Docker, TTS and BGM lines are not needed. HyperFrames' own skills are not needed; they assume a different workflow (they bump the pin, add stock media, send feedback). |
| [ffmpeg / ffprobe](https://ffmpeg.org/) | Trim, level, join, master, silence and freeze detection, frame grabs. | Every step uses it. |
| [Python 3](https://www.python.org/) | All our build and audio scripts. | |
| [pyte](https://github.com/selectel/pyte) | Replays a terminal recording into screen frames (a terminal emulator in Python). | Has no alternate screen and no faint text: work around both. We used 0.8.2. |
| [Pillow](https://pypi.org/project/pillow/) | Crops screenshots, paints over personal data. | |
| [Puppeteer](https://pptr.dev/) (`puppeteer-core`) + headless Chrome | Screenshots of public web pages. | HyperFrames brings its own headless Chrome. |
| `script -r` (macOS) | Records a terminal session with the timing of every byte. | Built into macOS; see `man script`. Linux `script` has a different format and options. |
| `say` (macOS) | Free placeholder narration. | Built into macOS; see `man say`. Voice "Reed" at rate 175 was closest to our narrator's pace. |
| [ocenaudio](https://www.ocenaudio.com/) | The narrator records and edits takes. | It can re-record part of a take; QuickTime cannot. Any recorder that writes WAV works. |
| [Open Markdown](https://ptheofan.github.io/open-markdown/) | Reading the scripts and notes while the AI edits them. | It refreshes when a file changes and marks the changed lines, so you see each edit as it happens. Ask the AI to edit files in place, not to rewrite them, so the marks stay useful. |
| `pdftoppm` ([poppler](https://poppler.freedesktop.org/)) | Turns PDF pages into images for a beat. | |
| [ElevenLabs](https://elevenlabs.io/) | Tried for a cloned voice; dropped. | See "What did not work" in `WORKFLOW.md`. `tools/tts.py` still supports it. |

## Our tools in `tools/`

Each tool tells how to use it at the top of the file (`--help` for `rec_prep.py`). Settings you
are likely to change are arguments or spec keys, with our values as the defaults.

| Tool | Does |
|---|---|
| `tts.py` | Makes placeholder clips with `say` (or ElevenLabs), one per paragraph, levelled to one loudness. Makes again only the clips whose text changed, and never touches a clip marked as recorded. |
| `rec_prep.py` | Trims recorded takes by frame energy, adds short fades, sets one gain to the clip level. Prints each cut so you can move it by ear (`--start`, `--end`). |
| `master.sh` | Raises the final video to the target loudness with a limiter, in two passes. Copies the video stream. |
| `srt_vs_script.py` | Word-diffs the captions against the script. |
| `strip.py` | Shows loud and quiet stretches of a clip, 10 ms at a time, to find word edges. |
| `assemble.sh` | Joins rendered beats; gives silent cards a silent audio track. |
| `beat_words.py` | Makes one word list for the whole video from the HyperFrames beats' clips. |
| `make_srt.py` | Makes captions from the word list and fixes known whisper errors from a fixes file (see `whisper-fixes.example.tsv`). |
| `recio.py` | A Python module: reads, cuts, joins and writes `script -r` files, re-paces typing to a steady rate, and puts a zsh prompt and command in front of a recording that has neither. |
| `rec2frames.py` | Replays a `script -r` file through pyte into timed, coloured frames. Needs `pip install -r tools/requirements.txt`. |
| `inspect_frames.py` | Shows the keys, the screen at a time, or the first time a text shows, in a frames file. |
| `shelledit.py` | A Python module of edits on `script -r` records of zsh: drop the "Restored session" line, show pastes as plain text, rename or drop a pasted line. Each edit asserts what it expects, so a different capture fails loudly. |
| `retime_spec.py` | Maps a spec written in a capture's original times through the time map that `recio.pace()` makes. |
| `pty_capture.py` | Runs a program in a pseudo-terminal and types a list of keys, waiting for a prompt after each. |
| `pty_rec.py` | Records a watch-only program's output in the same format as `script -r`. |
| `capture-pages.mjs` | Screenshots public web pages headless, signed out. Needs `puppeteer-core`. |

## Our kits in `kits/`

A kit builds a beat's `index.html` from the `spec.json` in the beat's folder. Run the kit's
`build.py` from that folder. Every spec key is listed at the top of each `build.py`. The templates
use Apple's SF fonts with Helvetica and Menlo as fallbacks; on Linux, check the font in a frame.

| Kit | Makes |
|---|---|
| `termkit` | A shell session typed live (prompt, command, output), from a list of steps. For short commands. |
| `cardkit` | A title or section card, with optional narration and lines that appear on cue phrases. |
| `screenkit` | A replayed terminal recording in its real colours: segments at set speeds, callouts, captions, window title changes. The build fails if a personal name is on screen or an expected line is missing. |
| `duokit` | Two or more replayed recordings as windows on one desktop. Cues bring a window to the front. Screenshots and PDF pages can fade in over them. |

screenkit and duokit read your personal names from a `personal.txt` file (see
`kits/screenkit/personal.py`). Keep that file out of any repo you publish.
