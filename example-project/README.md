# Example project

A small video project set up the way we work: a `CLAUDE.md` with start-up and close-out
checklists, a handoff file, a narration script, one real terminal recording and two beats. Build
it once by hand (below) to see every step work. Then copy the folder to start your own video.
Work in your workspace (repo README, "Getting started"), not in the clone.

| Path | What |
|---|---|
| `CLAUDE.md` | What Claude Code reads first: the rules, the folder map, and the start-up and close-out checklists. |
| `WHERE-WE-LEFT-OFF.md` | The handoff between sessions: the last one or two close-out entries. |
| `WHERE-WE-LEFT-OFF-ARCHIVE.md` | Every older entry, newest first. Nothing is deleted. |
| `personal.example.txt` | Copy to `personal.txt` and list your personal names (see below). |
| `scripts/video1.md` | The narration script. Timing words are in bold. |
| `voice/v1-clips.json` | The placeholder narration, one clip per paragraph, for `tools/tts.py`. |
| `captures/demo.rec` | A real `script -r` recording of a short zsh session, with a placeholder prompt. |
| `beats/card-title/` | A title card (cardkit). |
| `beats/demo-terminal/` | The recording, replayed (screenkit): a segment on a cue phrase, a sped-up wait, a caption, a callout and `expect` lines. |
| `youtube/` | Upload files only. |

## Build the example

You need ffmpeg, Python 3, Node.js (for `npx`) and macOS (for `say`): see "Requirements" in the
repo README. Run every command from this folder. The tools and kits are one folder up.

First, in the same terminal, set three variables for HyperFrames:
```
export HYPERFRAMES_NO_UPDATE_CHECK=1 HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_SKIP_SKILLS=1
```
Without them, HyperFrames tells you to upgrade past the pinned version ("Bump it"). Do not: keep
the pin to the end of the video. `TOOLS.md` tells what each variable does. Set them again in each
new terminal.

1. **Your personal names.** `cp personal.example.txt personal.txt`, then put your own names in
   it. screenkit stops the build if one shows on screen.
2. **The replay library.** `python3 -m venv .venv && .venv/bin/pip install --disable-pip-version-check -r ../tools/requirements.txt`
3. **Placeholder narration.** `python3 ../tools/tts.py voice/v1-clips.json` makes `voice/v1/<id>.wav`.
4. **Word times.** For each clip, from a beat folder (HyperFrames needs its project files):
   ```
   cd beats/card-title
   npx --yes hyperframes@0.8.77 transcribe ../../voice/v1/title-1.wav --engine whisper
   mv ../../voice/v1/transcript.json ../../voice/v1/title-1.words.json
   cd ../..
   ```
   Do the same for `term-1`, `term-2` and `term-3`. Read each transcript: every timing word must
   be there.
5. **Clips into the beats.**
   ```
   mkdir -p beats/card-title/assets beats/demo-terminal/assets
   cp voice/v1/title-1.wav beats/card-title/assets/
   cp voice/v1/term-*.wav voice/v1/term-*.words.json beats/demo-terminal/assets/
   ```
6. **Replay the recording into frames.**
   `.venv/bin/python ../tools/rec2frames.py captures/demo.rec beats/demo-terminal/frames.json 120 30`
7. **Build each beat** from its folder:
   `(cd beats/card-title && python3 ../../../kits/cardkit/build.py)` and
   `(cd beats/demo-terminal && python3 ../../../kits/screenkit/build.py)`.
   The build prints when each part plays, and stops on a missing cue phrase, a missing
   `expect` line, a callout on the wrong text, or a personal name.
8. **Render each beat:** `(cd beats/card-title && npx --yes hyperframes@0.8.77 render -o ../card-title.mp4 --quiet)`,
   the same for `demo-terminal`.
9. **Look at frames:** `ffmpeg -ss 17.8 -i beats/demo-terminal.mp4 -frames:v 1 frame.png`, then open the PNG.
10. **Join the draft:** `mkdir -p drafts && bash ../tools/assemble.sh -d beats drafts/video1-draft1.mp4 card-title demo-terminal`.
    The draft is about 26.5 s; its length must equal the sum of the beats.
11. **Dead air:** `ffmpeg -i drafts/video1-draft1.mp4 -af silencedetect=n=-45dB:d=2.5 -f null -`
    must find no silence.

Everything these steps make is in `.gitignore`: the sources are the only files to keep.

## Start your own video

1. **Copy this folder in your workspace:** from the workspace folder,
   `cp -R example-project my-video`. The new folder must be next to `tools/` and `kits/`, so that
   `../tools` and `../kits` work. (Anywhere else: change those paths in the commands and in
   `CLAUDE.md`.)
2. **Clear out the example:** in `my-video/`, delete the example's beats, recording, voice clips,
   drafts and script, and the sample entries of both `WHERE-WE-LEFT-OFF` files, and replace this
   README:
   ```
   cd my-video
   rm -rf beats captures voice drafts scripts/video1.md && mkdir beats captures voice
   sed -i '' '/^## /,$d' WHERE-WE-LEFT-OFF.md WHERE-WE-LEFT-OFF-ARCHIVE.md
   echo '# My video' > README.md
   ```
   `drafts/` is there only after the example build; `rm -rf` does not mind. The `sed` keeps each
   file's heading and deletes everything from the first `##` entry down. The new `README.md` is a
   heading only, so that nothing in the folder still describes the example. Keep `CLAUDE.md`,
   `.gitignore`, `personal.example.txt` and `youtube/README.md`.
3. **Your personal names and the replay library.** These are steps 1 and 2 of "Build the
   example", done again in `my-video/`. Without the example build, neither is there, because the
   repo does not track them:
   - `cp personal.example.txt personal.txt`, then put your own names in it. If `personal.txt` is
     already there from the example build, keep it.
   - `rm -rf .venv && python3 -m venv .venv && .venv/bin/pip install --disable-pip-version-check -r ../tools/requirements.txt`.
     The `rm` removes a venv that `cp -R` copied from the example. Make a new one in each folder.
4. **Install the skills:** `mkdir -p .claude/skills && cp -R ../skills/video-* .claude/skills/`.
   Check the "Your project" table at the top of each `SKILL.md`; its values already match this
   folder layout. The skills name our tools as one way to do a step: replace any with yours.
5. **Copy a beat to start each new beat:** a beat needs `hyperframes.json`, `meta.json` and
   `package.json` next to its `spec.json`, or it builds but never renders. Copy them from
   `../example-project/beats/card-title/`, and change the name in `meta.json` and `package.json`.
6. **Open Claude Code in `my-video/` and say "start up".** It reads `CLAUDE.md` and runs the
   start-up checklist. Tell it which video and step to work on. Say "close out" when you stop: it
   runs the close-out checklist and writes the handoff entry for next time.
