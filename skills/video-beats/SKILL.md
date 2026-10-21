---
name: video-beats
description: Capture, build, render and assemble the picture of a tutorial video -- beats made from real terminal recordings, AI sessions, title cards, screenshots and PDF pages; timing by cue phrases in the narration; personal-data checks; frame checks; dead-air checks; joining the beats into a draft. Use for a new beat, a re-capture, re-timing after new narration, a render that fails, a frame that looks wrong, or a new draft of the whole video. The voice is the video-narration skill; the upload is the video-publish skill.
---

# Video beats

The voice is the **video-narration** skill. The upload is the **video-publish** skill.

A video is a list of **beats**. A beat is one HTML page with timed parts, rendered to an MP4.
A beat plays narration clips, and every action on screen waits for a **cue phrase** in them.

## Your project (edit this table)

| Setting | Our value | Yours |
|---|---|---|
| Beat folders | `beats/<beat>/` with `spec.json`, `assets/`, `index.html`; renders in `beats/<beat>.mp4` | |
| Renderer | HyperFrames: `npx --yes hyperframes@0.8.77 render -o ../<beat>.mp4 --quiet` | |
| Kits (spec -> HTML) | termkit, cardkit, screenkit, duokit (see `TOOLS.md`) | |
| Captures | `captures/`, one `.rec` per recording | |
| Drafts | `drafts/videoN-draftM.mp4` | |
| Placeholder identity | prompt `user@Macbook`, home `/Users/user`, `user@example.com` | |
| Terminal | 120x30; background `#1c222c`, text `#dadcdc` | |
| Typing speed | 18 keys/s, Enter 0.35 s after the last key | |
| Gap between clips | at least 1.1 s | |

## Rules

1. **Every character on screen comes from a real capture.** The beat controls the pacing, not the
   content. Allowed changes, each written in the beat's notes:
   - the placeholder identity;
   - re-creating a command the capture lost, when its exact text is on record;
   - dropping something the viewer will not have (a personal plug-in, an account line);
   - cutting the user's slips (stray keys, wrong menu moves).
   Never invent output. Capture it.
2. **No personal data in any frame.** List every real user name, host name, home folder and
   e-mail of every capture computer. Make the build fail if one shows after the substitutions.
3. **Commands show as plain text.** A shell shows a paste in reverse video until Enter. That is a
   copy-paste artifact: remove it. Output keeps its real colours.
4. **Check frames before you call a visual change done.** Extract frames and look at them. A
   build log is not a check. Expect review notes from whoever watches the draft.
5. **No dead air.** A beat does not play on more than about 2 s after its last clip. Speed up
   quiet stretches (an AI that is thinking, a progress wait).

## Build, render, check

1. Build the beat: run its kit from the beat's folder.
2. Render it in the background. A render takes from seconds to minutes.
3. Grab frames: `ffmpeg -ss <t> -i <beat>.mp4 -frames:v 1 x.png`, then look at the PNG.
   For several frames, scale each to 960 px and join them in a grid with ffmpeg `xstack`.
4. Back up a beat folder and its MP4 before you overwrite them.

A renderer project often needs its own project files next to `index.html`. Copy them from a beat
that renders. A beat without them builds but never renders.

## Timing

- Each action has a cue phrase. The build finds the phrase in the clip's whisper words and places
  the action at that time. New narration re-times the beat by itself.
- Clips play one after another. A clip starts the clip gap after the previous clip AND after the
  last action placed before it.
- A cue that comes too soon after the previous action is pushed later. The build reports it.
  Small pushes are fine. A large push means the action before it runs too long.
- **Make the build stop on a missing cue phrase.** Never let it guess a time.
- Check every cue phrase after every recording. Look in every place a phrase can hide: card
  lines, list items, segment cues, front-window switches, screenshot times.
- If two actions land less than 1 s apart, split the narration into two clips. Do not move the
  cues off their words.
- Whisper traps: an AI's name, words glued to file names, short commands. Cue on plain words.

## Capturing real screens

- **A shell or AI session:** record with `script -r <file>.rec` (macOS) at the fixed window size.
  The person does every step. Copy the files to the captures folder.
- **A program's output:** run it in a pseudo-terminal from a script and send keys from a list.
  - Run it on a scratch copy of its files: a program can change its own data files.
  - Wait about 1.5 s after the first prompt. A key sent at once can be lost.
  - Write the key list with Python, not `echo`: zsh's `echo` turns `\r` into a real carriage return.
  - Stop on an empty read. macOS reports a closed pty as readable forever.
- **A watch-only program** (a log, a monitor): record its output in a pty, in the same format.
- **An AI session:** see "Recording an AI session" below.
- **Public web pages:** screenshot them headless, signed out. Crop to what the narration talks
  about. A page that shows a relative date ("yesterday") ages: capture it again on publish day.
- **Pages that need a sign-in:** real window screenshots. Paint over the personal spot only, with
  the page's own background colour, and draw the placeholder in the page's font at the same width.
- **Clean computer:** capture on a fresh account or a second computer. Do only read-only checks
  over SSH there. On a clean Mac, the first `python3`, `git` or `cc` opens an "install developer
  tools" dialog on that computer's screen, which changes what a new user sees.
- Screenshot file names on macOS have a narrow no-break space before AM/PM. Copy them with a
  wildcard.

## Recording an AI session

We recorded Claude Code like any other program and replayed it with screenkit, or with duokit next
to a second window. An early version redrew the screen from the session log instead; a recording
is simpler and shows exactly what the viewer would see.

- **Record:** `script -r <file>.rec claude` at the fixed window size. Keep the AI's session log as
  well: it has the exact text of every message and tool call.
- **Open on a prompt:** Claude Code draws from the cursor position and does not clear the screen.
  So a recording started this way can follow a real prompt and a typed `claude` command
  (`recio.zsh_prefix()`, with the prompt bytes from one of your own captures).
- **Window title:** Claude Code sets `✳ <session name>` when idle and `◐`/`◑ <session name>`
  while it works, and only once a real session starts. Read the titles from the recording.
- **Pacing:** re-pace only the person's typing. The AI's own output bursts are real timing.
- **Thinking time:** speed it up, and say so in the narration (rule 5).
- **Exit:** Claude Code uses the alternate screen; pyte has none, so an `/exit` replays garbled.
  Compose the normal screen instead.
- **Faint text:** its grey hints and suggested replies are faint text, which `rec2frames.py` keeps.
- **The sent-message band** (grey background behind your message) is part of the real screen,
  not a highlight to remove.
- **Editing its output** means rewriting cursor moves: it reserves rows and jumps columns.

## Replaying a terminal recording

A `script -r` file is a list of records: a 24-byte header (length, seconds, microseconds,
direction) and the bytes. Replay the output records through a terminal emulator (pyte) and keep a
frame whenever the screen changes. Keep the key records too, to find "the moment Enter was
pressed".

- **Screen size = the size the capture was drawn at.** zsh pads its end-of-line mark to the width
  minus 1 column: count the spaces.
- **Window titles:** read them from the recording. The shell sends the folder (OSC 7) at a prompt,
  and the program sends its title (OSC 0). `cd X && program` on one line keeps the OLD folder in
  the title. Drop the recorder's own part of the title.
- **Paste highlight:** remove the reverse-video codes only in records that START with them. zsh's
  end-of-line mark also uses reverse video.
- **Keyboard protocol codes** that the emulator does not know show as a stray letter. Strip them.
- **Alternate screen:** pyte has none. A full-screen program's exit replays garbled. Compose the
  normal screen instead.
- **Faint text:** pyte has no faint attribute. Handle it in the replay.
- **Editing a program's output** means rewriting its cursor moves. A program that draws with
  column jumps leaves old text unless the row is cleared.
- **A longer placeholder** than the real name can overflow a full row. Wrap the overflow to the
  next row, as a terminal would, and check that row on a rendered frame.
- **A recording that starts with the program** has no prompt and no command. Put a real prompt
  and the typed command in front of it.
- **Typing pace:** real typing has long pauses, and a paste appears at once. Re-pace typed and
  pasted lines to the typing speed. Keep a map from old to new times, and write the spec in the
  old times. Do not re-pace a program's own output.
- **Damaged files:** two recorders writing one file overwrite each other. Skip any header whose
  length, direction or time does not fit, and report what was skipped.

## Segments

A segment plays a stretch of a capture (`from`-`to`) at a speed, starting on a cue.

- Speed 1.3-1.5 keeps a real typing rhythm. Use 3-12 for waits and long outputs.
- End every segment PAST the output the viewer must see.
- Between segments, the screen holds.
- **A visible cut:** fade to black for 1 s, switch while black, fade in. Use it for any cut that
  skips real time. Let the previous segment run through the fade-out so nothing freezes.
- **A background wait:** a segment that ends exactly when the same window's next segment starts,
  at whatever speed that needs. Without it, every clip waits for every segment placed before it.
  Use one for each watch-only wait, or its dots run at mixed paces.

## Several windows on one desktop

- Each window replays its own capture. Place them so they overlap. The last window listed starts
  in front. Cues bring a window to the front. Draw the back window as inactive.
- Use the same font size in every window that the viewer reads.
- Set the monospace font on the element itself, not only in a stylesheet rule. With the family
  only in the stylesheet, our render used a proportional font and the columns did not line up.
  Check a full-size crop of a table, not a scaled grid.
- **Two recordings on one clock:** `script -r` times are wall-clock time. Recordings made on one
  computer line up exactly: offset = the difference of their start times.
- **Screenshots and PDF pages** can fade in over the windows. When the narration talks about a
  web page setting or a printout, SHOW it. For PDF pages: `pdftoppm -r 120 -png -f 1 -l 2`.
- A busy overview of all windows at a small size is fine for orientation. Say that it is not
  meant to be read.

## Cards

Section cards between two terminal beats can be silent (a fixed hold). A "next part" line plays
over the end card, not over the last terminal. Screen text carries the same message as the voice,
not the same words.

## Assemble and check

1. Join the beats in order with ffmpeg (concat filter). Give silent cards a silent audio track so
   every part has the same streams.
2. Check: the video's length = the sum of the beats. After a change, the difference = the change.
3. **Dead air:** list silences of 2.5 s or more (`silencedetect=n=-45dB:d=2.5`) and frozen
   pictures (`freezedetect`). A stretch in both lists is dead air, unless it is a card by design.
   A long silence over a moving screen is also too long if nothing on it matters.
4. When a recorded voice is longer than the placeholder, slow segments stand out. Speed them up.
