# The workflow

This is the process we used for an 8-part series, one video at a time. Each step tells why it is
there: most steps exist because something went wrong without them. The skills in `skills/` hold
the details for each step.

## The rules we set first

1. **Every character on screen comes from a real capture.** We control the pacing, not the
   content. We never type a terminal screen by hand. If a capture lost something, re-capture it.
2. **Use a placeholder identity.** Real user names, host names and e-mail addresses never reach a
   frame. Replace them with placeholders (for example `user@Macbook`), and make the build fail
   if a real name is still on screen.
3. **Capture on a clean computer.** A fresh account or a second computer shows what a new user
   sees: no aliases, no installed tools, no history.
4. **The viewer must never wait for nothing.** No section plays more than about 2 seconds past its
   narration. Speed up waits (installs, builds, an AI that is thinking) and say so aloud.
5. **Judge sound by ear and pictures by eye.** A meter or a transcript does not tell you if a
   take sounds right. A build log does not tell you if a frame looks right. Look at the frames.

## The steps

### 1. Write the script

Write the narration one paragraph per clip. Write what the viewer does in plain words. Screen
text (cards, captions) carries the same message as the voice, but not the same words: identical
text sounds like someone reading slides.

Plan around words the narrator finds hard to say. Say what a command does, and let the screen
show the command.

### 2. Capture the real screens

- **Terminal:** record with `script -r` (macOS) or any recorder that keeps the timing of each
  byte. Record at a fixed window size, for example 120x30.
- **A program's output only:** run it in a pseudo-terminal from a script, and send the keys from
  a list. Wait a moment after the first prompt: a key sent at once can be lost.
- **An AI session:** record the terminal like any other program, and keep the AI's session log
  too. The log has the exact text of every message and tool call. The video-beats skill
  ("Recording an AI session") has what is special about replaying one.
- **Web pages:** use a headless browser for a public page. Use real window screenshots for a page
  that needs a sign-in, and paint over the personal data only.

### 3. Make placeholder narration

Before anyone records, make the narration with a free text-to-speech voice (we used macOS `say`).
Pick the voice and rate that come closest to the narrator's own pace. Build and time every beat
against these clips. This lets you review the whole video before the real recording.

### 4. Build the beats

Each beat is one HTML page that a renderer turns into an MP4. A beat can be:

- a title or section card, with or without narration;
- a replayed terminal capture, in its real colours, with parts sped up;
- two or more replayed captures as windows on one desktop, with the front window switched on cues;
- a typed shell session for short commands;
- screenshots or PDF pages that fade in over the windows.

Every action waits for a **cue phrase**: a few plain words in the narration. Whisper gives the
time of each word, and the build places the action there. Keep cue phrases to plain English
words; whisper mis-hears product names.

### 5. Review the draft

Join the beats into a draft and watch it. Expect notes: long pauses, a screenshot that is
missing when the voice talks about it, a stray key. Fix and build the next draft.

### 6. Record the real narration

The narrator records one file per paragraph, at a fixed setting (we used 48 kHz, mono, 24 bits,
WAV). Expect rewording: the narrator changes words as they read. The recording is the new script.

For each take:

1. Trim the lead-in and the stop click. Find the speech by its energy, not by silence detection.
2. Set one plain gain so every clip has the same loudness (we used -24.5 LUFS).
3. Transcribe the take. Compare its first and last words with the untrimmed take.
4. Look for long pauses inside the take.
5. Read the transcript for meaning: a reworded line can drop a fact the screen shows, or add a
   wrong one.

Then update the script to the recorded words and check every cue phrase again. In our series,
many cues changed after a recording.

### 7. Render, assemble, check

Render each beat. Join them with ffmpeg. The length of the video must equal the sum of the beats.
Look for dead air: a stretch with no voice and no real change on screen.

### 8. Publish

1. **Master the loudness.** The clips are quiet on purpose (-24.5 LUFS). Raise the whole video to
   the level of your channel (we used -15.9 LUFS) with a limiter. Do not skip this: one of our
   videos went up 8 dB too quiet.
2. **Make your own captions** from the whisper words of the final video. Fix the words whisper
   gets wrong (product names). Compare the captions with the recorded script.
3. Make the thumbnail, the title and the description. Chapters come from the card start times.
4. After the upload, open the page as an anonymous viewer and check everything.

## What did not work for us

- **A cloned voice.** We tried a commercial voice clone. It said one product name differently in
  every clip, even inside one clip. Splicing one good take of the word over every occurrence
  helped, but never fully. The narrator recorded the final voice in the end.
- **Whisper word times as cut points.** They were 0.15 to 0.6 seconds off. Find word edges from
  the sound itself.
- **Fixed waits in place of cues.** Every new take moved the actions. Cue phrases re-time the
  video by themselves.
