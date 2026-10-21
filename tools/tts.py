#!/usr/bin/env python3
"""Generate narration clips with macOS `say` or ElevenLabs, one clip per paragraph.

Usage: python3 tts.py <clips.json>

clips.json: {"engine": "say", "out_dir": "v1", "clips": [{"id": "a", "text": "..."}, ...]}
out_dir is relative to the clips.json file. Each clip becomes <out_dir>/<id>.wav (48 kHz stereo).
Optional "target_lufs" (default TARGET_LUFS): every .wav is loudness-matched to it (two-pass ffmpeg
loudnorm, linear gain only), so every clip has the same level whatever the voice.

A clip is only made again when its text, voice or settings changed since the last run (the hash is
kept in <out_dir>/<id>.sha). A clip with a <out_dir>/<id>.recorded file is a human recording and is
never regenerated (delete the .recorded file to go back to TTS).

"engine": "say" (free placeholder voice, macOS only): optional "say_voice" (a `say -v` name, default
the system voice) and "say_rate" (words per minute). Iterate wording and timing with it.

"engine": "elevenlabs": needs "voice_id"; optional "model_id" (default MODEL), "seed" (same seed +
same text = repeatable take) and "voice_settings", sent as-is (e.g. {"stability": 0.5,
"similarity_boost": 0.75, "style": 0.0, "use_speaker_boost": true, "speed": 0.9}). Send the voice's
full stored set, not only the changed key. The .mp3 stays as the API sent it. Only changed clips are
sent, so an edit to one paragraph costs only that paragraph's characters. The API key comes from
the ELEVENLABS_API_KEY environment variable, else ~/.config/elevenlabs/api_key; it is never printed.
"""
import hashlib, json, os, re, subprocess, sys

MODEL = "eleven_multilingual_v2"
TARGET_LUFS = -24.5  # low on purpose; master.sh raises the finished video once

spec_path = sys.argv[1]
spec = json.load(open(spec_path))
out_dir = os.path.join(os.path.dirname(os.path.abspath(spec_path)), spec["out_dir"])
os.makedirs(out_dir, exist_ok=True)
ENGINE = spec.get("engine", "elevenlabs")
TARGET = spec.get("target_lufs", TARGET_LUFS)

def api_key():
    key = os.environ.get("ELEVENLABS_API_KEY")
    if key:
        return key.strip()
    return open(os.path.expanduser("~/.config/elevenlabs/api_key")).read().strip()

key = api_key() if ENGINE == "elevenlabs" else None

def tts_elevenlabs(clip, base, key):
    model = spec.get("model_id", MODEL)
    # curl, not urllib: a python.org Python on macOS can lack CA certificates until you install them.
    # The key and body go in through a curl config on stdin, so the key is never on a command line.
    req = {"text": clip["text"], "model_id": model}
    for opt in ("voice_settings", "seed"):
        if opt in spec:
            req[opt] = spec[opt]
    body = json.dumps(req)
    config = (f'url = "https://api.elevenlabs.io/v1/text-to-speech/{spec["voice_id"]}?output_format=mp3_44100_128"\n'
              f'header = "xi-api-key: {key}"\nheader = "Content-Type: application/json"\n'
              f'data = {json.dumps(body)}\noutput = "{base}.mp3"\nwrite-out = "%{{http_code}}"\nsilent\nshow-error\n')
    code = subprocess.run(["curl", "-K", "-"], input=config, capture_output=True, text=True).stdout.strip()
    if code != "200":
        sys.exit(f"{clip['id']}: HTTP {code}: {open(base + '.mp3', errors='replace').read()[:300]}")

spent = 0
for clip in spec["clips"]:
    base = os.path.join(out_dir, clip["id"])
    if os.path.exists(base + ".recorded"):
        print(f"{clip['id']}: recorded by hand, skipped")
        continue
    if ENGINE == "say":
        key_parts = ["say", spec.get("say_voice"), spec.get("say_rate"), clip["text"]]
    else:
        model = spec.get("model_id", MODEL)
        key_parts = [spec["voice_id"], model, clip["text"]]
        for opt in ("voice_settings", "seed"):  # only hashed when present, so older clips stay cached
            if opt in spec:
                key_parts.append(spec[opt])
    if TARGET != TARGET_LUFS:  # only hashed when changed, so clips made at the default stay cached
        key_parts.append(TARGET)
    digest = hashlib.sha256(json.dumps(key_parts, sort_keys=True).encode()).hexdigest()
    if os.path.exists(base + ".sha") and open(base + ".sha").read() == digest and os.path.exists(base + ".wav"):
        print(f"{clip['id']}: unchanged, skipped")
        continue
    if ENGINE == "say":
        src = base + ".aiff"
        cmd = ["say", "-o", src]
        if spec.get("say_voice"): cmd += ["-v", spec["say_voice"]]
        if spec.get("say_rate"): cmd += ["-r", str(spec["say_rate"])]
        subprocess.run(cmd + [clip["text"]], check=True)
    else:
        src = base + ".mp3"
        tts_elevenlabs(clip, base, key)
    # Pass 1 measures the clip; pass 2 applies one gain change to reach TARGET.
    ln = f"loudnorm=I={TARGET}:TP=-2:LRA=7"
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", src, "-af", ln + ":print_format=json",
                          "-f", "null", "-"], capture_output=True, text=True, check=True).stderr
    m = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", err).group(0))
    ln += (f":linear=true:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
           f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", ln, "-ar", "48000", "-ac", "2",
                    base + ".wav"], check=True)
    open(base + ".sha", "w").write(digest)
    if ENGINE != "say": spent += len(clip["text"])
    print(f"{clip['id']}: generated ({ENGINE}), {len(clip['text'])} characters")
print(f"characters sent this run: {spent}")
