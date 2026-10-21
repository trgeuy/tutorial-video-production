# Video project: instructions for Claude Code

This folder makes tutorial videos as a list of beats: real terminal recordings and title cards,
timed by cue phrases in the narration, rendered with HyperFrames and joined with ffmpeg. The
method is in `../WORKFLOW.md`. The details of each step are in the skills: install
`../skills/video-narration`, `../skills/video-beats` and `../skills/video-publish` into
`.claude/skills/` of this folder.

## Rules

The reasons are in `../WORKFLOW.md`, "The rules we set first".

1. Every character on screen comes from a real capture. Never type a terminal screen by hand.
2. No personal data in any frame. `personal.txt` lists the names; the build stops if one shows.
   Never publish `personal.txt`.
3. Capture on a clean computer or account.
4. The viewer never waits for nothing: no beat plays on more than about 2 s past its narration.
5. Judge sound by ear and pictures by eye: extract frames and look at them before you call a
   visual change done.

## Folders

| Path | What |
|---|---|
| `scripts/` | Narration scripts, one per video. Narration lines start with `> `. |
| `voice/` | Clip specs (`vN-clips.json`), placeholder clips and recorded takes (`voice/vN/`), raw takes (`voice/rec/`). |
| `captures/` | Real recordings, never edited in place. |
| `beats/<beat>/` | One beat: `spec.json`, `assets/`, the HyperFrames project files. Renders go to `beats/<beat>.mp4`. |
| `drafts/` | Assembled drafts for review. |
| `youtube/` | Upload files only. |

## Start-up checklist

Run this at the start of every session, before any other work. Report what you find.

1. Read `WHERE-WE-LEFT-OFF.md`. Open `WHERE-WE-LEFT-OFF-ARCHIVE.md` only when you need older history.
2. Look for new files since the last entry: narrator takes in `voice/rec/`, recordings in
   `captures/`, screenshots in `beats/*/assets/`. New takes need the steps in the video-narration
   skill before any beat uses them.
3. Check the tools: `ffmpeg -version`, the pyte venv (`.venv/bin/python -c "import pyte"`), and the
   HyperFrames version pinned in each beat's `package.json`.
4. Check free disk space (`df -h .`). Renders and takes are large.
5. Confirm with the person which video and which step of the workflow this session is for.

## Close-out checklist

Run this when the person ends the session.

1. Stop every background render or process this session started.
2. Rebuild every beat whose spec, assets or capture changed, so the personal-name and `expect`
   checks run on the new material.
3. List the backups this session made (`*.pre-*`, backup folders). Ask before you delete any.
4. Check free disk space. Offer to move a finished video's media to an archive.
5. Write a new entry at the top of `WHERE-WE-LEFT-OFF.md`: what is done, the state of the files,
   and the next step. Then move every entry older than the last two to the top of
   `WHERE-WE-LEFT-OFF-ARCHIVE.md`, newest first. Never delete an entry. (The live file is read at
   every start-up, so it stays short. The archive keeps the history.)
