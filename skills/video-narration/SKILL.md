---
name: video-narration
description: Make or change the narration of a tutorial video -- placeholder text-to-speech clips for timing, the narrator's recorded takes (trim, level, transcribe, compare), retakes, word timing with whisper, and cue phrases. Use for a new video's voice-over, a script change, a new or replaced take, a word that sounds wrong, or "the narration does not match the script". The picture side is the video-beats skill; the upload is the video-publish skill.
---

# Video narration

The picture side (beats, captures, renders) is the **video-beats** skill. Publishing is the
**video-publish** skill.

**Judge sound by ear.** When a choice is about how something sounds, play it and ask the
narrator. Never decide from a transcript or a loudness meter alone. Play one thing at a time,
then wait: the narrator can still be listening when the next clip starts.

## Your project (edit this table)

| Setting | Our value | Yours |
|---|---|---|
| Script | `scripts/videoN.md`, narration lines start with `> ` | |
| Clip specs | `voice/vN-clips.json`, one clip per paragraph | |
| Clips used by the beats | `voice/vN/<clip-id>.wav` + `<clip-id>.words.json` | |
| Recorded takes | `voice/rec/vN/NN.wav`, trimmed into `voice/rec/vN-trim/` | |
| Recording script | `scripts/videoN-recording.md`: line number `NN` -> clip id | |
| Clip loudness | -24.5 LUFS | |
| Gap between clips | 1.1 s (0.6-0.8 s sounded rushed) | |
| Placeholder voice | macOS `say -v Reed -r 175` | |
| Take format | 48 kHz, mono, 24 bits, WAV | |

## The order of work

1. **Placeholder first.** Make every clip with a free text-to-speech voice (macOS `say`). Pick the
   voice and rate closest to the narrator's own pace: measure it on a few recorded lines. Build
   and time every beat against these clips, and review the full draft.
2. **The narrator records the final voice**, one file per numbered line.
3. **The recordings re-time the beats** through their cue phrases (video-beats skill, "Timing").

One clip per paragraph. Split a paragraph into more clips when two screen actions land less than
about 1 s apart: the gap between clips gives each action room. Keep the words; change only the
split.

## The recording script

Give the narrator a numbered list: one line per clip, in playing order. For each line:

- the text, with real spellings;
- the **timing words**: the words that switch a window or show a screenshot. If the narrator
  changes them, the cue changes too;
- a table of how to say hard words (abbreviations, file names, product names).

Write around the narrator's trouble spots where it costs nothing. Our narrator had trouble with a
hard "d" at the end of a word, an abbreviation that came out with two letters swapped, and a
short command that would not flow. Say what a command does, and let the screen show the command.

Tell the narrator:

- one file per line, named by its number (`07.wav`);
- a retake gets a suffix (`07-1.wav`, `07-2.wav`); the highest suffix wins;
- a long line can be two halves (`10a.wav`, `10b.wav`);
- leave about 1 s of quiet before and after;
- same microphone, distance and room for every line.

## Prepare the recorded takes

Do these steps for every take, and again for every retake.

1. **Check the format.** Use `ffprobe` for the sample rate, channels and bits. Reject a headerless
   `.aac` export: ffmpeg cannot read it.
2. **Trim by frame energy.** Every take has 2.5-5 s of lead-in (a click, a breath) and a stop click
   in its last 0.1 s. Silence detection finds those small noises, not the speech.
   - Start: the first stretch of sustained loud frames, minus 0.15 s.
   - End: the last loud frame. Then continue through any non-silent frame until a 0.25 s gap,
     plus 0.15 s. A cut at the last loud frame removed a final "t" and the fade of a word.
   - Fades: 20 ms in, 40-50 ms out.
3. **Level with one plain gain:** `volume=<target - measured>dB`. Do not use linear loudnorm: it
   silently changes to dynamic mode when a peak would pass -2 dBTP.
4. **Transcribe** the trimmed take AND the untrimmed take. Compare the first and last words. A
   difference that is only case or punctuation is fine.
5. **Find long pauses inside the take:** `silencedetect=n=-45dB:d=2`. An edit in the recorder can
   leave seconds of silence. Cut a long one to about 0.8 s (silence only).
6. **Read the transcript for meaning**, not only for cues:
   - a reworded line can drop what the screen shows;
   - it can bring in a wrong fact. We found a wrong expansion of an abbreviation, and a statement
     about "every browser" that was true for one browser only;
   - a word whisper hears oddly can be a real mispronunciation. Cut a 3 s excerpt around it and
     play it for the narrator.
7. **Two halves:** trim each, join them with 0.5 s of silence, so the beat keeps one clip.
8. **Retakes:** move the replaced trimmed take to a `superseded/` folder. Keep the raw take.

Then copy each take to the clip name the beats use, and mark it as recorded, so the placeholder
generator does not overwrite it. Back up the placeholder clips first.

## After a recording

- **Update the script** to the recorded words. Expect real rewording: in our series, many
  lines changed. Fix whisper's spellings (product names, file names) to the real ones.
- **Check every cue phrase** against the new words before you build (video-beats skill). A build
  that stops on a missing cue is better than one that guesses.
- **Order changes:** if the narrator reorders a sentence, the actions on screen may need to move,
  not only their cues.

## Whisper and cue phrases

- Whisper gives each word a start and end time. These times are good enough for cues, **not**
  for cutting audio: they were 0.15-0.6 s off a word's real edge.
- Whisper changes names: it hears an AI's name as similar words, glues words to file names
  ("the new.mcp.json"), and spells a short command differently from run to run. Cue on the plain
  words before or after a name.
- Match whole words with the punctuation removed. A hyphenated word can be one token.
- Whisper can drop the first few words of a long file. Check the start of every transcript.

## Splicing (only if you use a synthetic voice)

A cloned voice can say a product name differently every time. One fix is to cut one good take of
the word and paste it over every occurrence.

- Find word edges from the sound (loud and quiet stretches of 10 ms), not from whisper.
- Count the stretches from a word you are sure of on each side.
- Symptoms by ear: a doubled first syllable = the cut starts too late; a doubled tail = the cut
  ends too early; a clipped word = the source cut is short.
- Review one splice at a time, by ear. A single reel of all splices hid several bad ones.
- If a phrase will not splice cleanly, change one word of the text and make that clip again.

In our series, splicing still did not give a consistent voice. The narrator recorded the final
voice instead.
