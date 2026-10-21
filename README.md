# Tutorial video production

A starting point for making tutorial and training videos with an AI assistant: terminal sessions,
AI sessions, web pages, title cards and a recorded voice-over, joined into one video.

We made an 8-part YouTube series this way (see "Our series" below). The series is about a
computer simulator, but the method is not. Use it for any software training video.

## Getting started

1. Clone this repo.
2. **Build the example once.** Follow "Build the example" in
   [`example-project/README.md`](example-project/README.md). In 11 steps you go from a real
   terminal recording and a script to a 26-second draft video, and see every tool and check work.
3. **Start your own video** from a copy of the example project: "Start your own video" in the same
   README. Then open Claude Code in your folder and say "start up": it reads `CLAUDE.md` and runs
   the start-up checklist. Say "close out" at the end of a session.

[`WORKFLOW.md`](WORKFLOW.md) explains why each step is there. Read it before your first real video.

## What is here

| Path | What |
|---|---|
| [`example-project/`](example-project/) | A small video project to build once and then copy: a `CLAUDE.md` with start-up and close-out checklists, the handoff files, a script, a real recording and two beats. |
| [`WORKFLOW.md`](WORKFLOW.md) | The whole process, from the first script to the upload, and why each step is there. |
| [`TOOLS.md`](TOOLS.md) | The third-party tools we use, and our tools and kits in this repo. |
| [`skills/`](skills/) | Three Claude Code skills, made general: narration, picture (beats), publish. They tell Claude how to do each step and which mistakes to avoid. |
| [`tools/`](tools/) | Sixteen of our tools: narration, captions, mastering, joining beats, and capturing, editing and replaying terminal sessions and web pages. |
| [`kits/`](kits/) | Four kits that build a beat's HTML page from a `spec.json`: title cards, typed shell sessions, one replayed terminal, several replayed terminals on one desktop. |

For a question or a tool request, [open an issue](https://github.com/trgeuy/tutorial-video-production/issues).

## The idea in one paragraph

A video is a list of short **beats**. A beat is one HTML page with timed parts: a replayed
terminal, a title card, a screenshot. A beat plays its narration clips, and each action on screen
waits for a **cue phrase** in the narration. A speech-to-text tool (whisper) gives the time of
every word. When the narration changes, the beats re-time themselves. A renderer turns each page
into an MP4, and ffmpeg joins the beats into the video.

## Our series

The series on YouTube:
[Altairsim - a simulator of the Altair 8800 and the S-100 bus](https://www.youtube.com/playlist?list=PLSoqnaEz8pQc).
Commands and prompts from each part: [altairsim-video-files](https://github.com/trgeuy/altairsim-video-files).

## Requirements

We made everything on macOS. Some steps use macOS programs (`say`, `script -r`, Terminal.app).
`TOOLS.md` names each one, so you can find the equivalent on Windows or Linux.

## License

MIT. See [LICENSE](LICENSE).
