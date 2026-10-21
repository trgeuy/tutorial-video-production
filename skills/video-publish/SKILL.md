---
name: video-publish
description: Prepare and check a finished tutorial video for upload -- loudness mastering, captions from whisper words, a caption check against the script, thumbnail, title, description with chapters, and the after-upload checks. Use when a cut is approved, before any upload, or when an uploaded video sounds too quiet or its captions are wrong. Narration is the video-narration skill; beats are the video-beats skill.
---

# Video publish

Do these steps only after the approved cut. Master from the UNMASTERED cut. Never master a final
again.

## Your project (edit this table)

| Setting | Our value | Yours |
|---|---|---|
| Target loudness | -15.9 LUFS (the level of the channel we match) | |
| Limiter ceiling | -2 dBFS | |
| Upload folder | `youtube/`: upload files only; drafts stay in `drafts/` | |
| Platform | YouTube | |

## 1. Master the loudness. Never skip this step.

The clips are levelled low (-24.5 LUFS) on purpose. A video uploaded at that level is about 8 dB
quieter than a normal video. One of ours went up that way and had to be replaced.

1. Measure the cut: `ffmpeg -i cut.mp4 -af loudnorm=print_format=json -f null -`.
2. Add gain to the target, with a limiter at the ceiling. Copy the video stream.
3. The limiter takes some loudness away. Measure again, and add the difference in a second pass.
4. Check: the final measures the target, plus or minus 0.1 LU.

Some platforms turn loud audio down but do not turn quiet audio up. Check the platform's own
statistics after the upload.

## 2. Captions

Make your own captions. Automatic captions mis-spell product names.

1. Make one word list for the whole video: each beat's clip words, offset by the beat's start.
   The total length must equal the final video's length.
2. Make an `.srt` from the words. Fix the words whisper gets wrong (a list of fixes per video).
3. Word-diff the captions against the RECORDED script, not the script you wrote first.
4. Judge each difference by ear: a whisper error, or a real reworded line.
5. Spot-check a few caption start times against the silence detector.

## 3. Thumbnail, title, description

- **Thumbnail:** an HTML page rendered by headless Chrome at 1280x720. Copy the previous part's
  page and change it. Look at the PNG.
- **Description:** chapters come from the card start times. YouTube's rules: the first chapter
  starts at 0:00, there are at least 3 chapters in time order, and each chapter is 10 s or
  longer.
  Link the other parts with placeholders until their URLs exist.
- Name the upload file well. The platform fills in the title from the file name: tell the person
  who uploads to select all and paste the real title.

## 4. After the upload

Open the page as an anonymous viewer and check:

- the title and the description;
- every link;
- the chapters;
- the caption tracks;
- the thumbnail;
- the order in the playlist.

Then update the companion files (commands, prompts) for the viewers, and link them.
