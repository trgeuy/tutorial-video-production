# Working with Claude

These are our tips for making a video together with Claude Code. They come from our own videos.
[`WORKFLOW.md`](WORKFLOW.md) has the steps. This list is about how you and Claude work through them.

This is our list, not a set of rules. Question each item. Change it to suit how you work. If you
find an item that is wrong or missing, [open an issue](https://github.com/trgeuy/tutorial-video-production/issues).

## Drafts and notes

1. **Expect many drafts.** Claude builds a draft, you watch it, and you give notes. Our companion
   video went through more than ten drafts.
2. **Tell Claude when something does not look or sound right.** You do not need to know the
   cause. "This pause feels too long" is a good note. Claude finds the cause.
3. **Read what Claude tells you back.** Claude reports what its checks find, for example dead air
   or a cue phrase that is not in the take, and often proposes a fix. Read the report before you
   ask for the next draft.
4. **Give the time in the draft for each note.** Write one note per line, for example "2:10: the
   voice starts before the screen". With a time, Claude can find the exact beat and cue.
5. **Keep the earlier draft.** Give each draft its own number in `drafts/` (`video1-draft2.mp4`).
   Before a large change, ask Claude to keep a copy of the files it changes. If the new draft is
   worse, compare the two and tell Claude which parts to keep.

## The narration

6. **Change the words so that they sound like you.** A script reads differently aloud. Reword a
   line as you record it. Do not record a line that sounds wrong to you.
7. **Keep a list of the words you changed, and give it to Claude.** The recording is the new
   script. Claude updates the script, the cue phrases and the captions to match. See step 6 in
   [`WORKFLOW.md`](WORKFLOW.md).
8. **Record again only the part that is wrong.** If one sentence of a take is wrong, record that
   sentence only. Claude can join the new sentence to the old take.

## Checks and sessions

9. **You are the final check.** The checks find dead air and personal names. They do not find a
   wrong fact on the screen, or a line that is not clear. Watch the final draft from start to end.
10. **Question what Claude tells you.** Claude can be wrong. When Claude says that something is
    fixed or correct, ask how it checked. Ask why when Claude proposes a change.
11. **Plan for many sessions.** Say "close out" when you stop, and "start up" when you come back.
    Claude writes down what is done and what comes next, so you can stop at any step.
