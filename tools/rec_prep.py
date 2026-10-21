#!/usr/bin/env python3
"""Trim and level recorded narration takes (the video-narration skill, "Prepare the recorded takes").

    python3 rec_prep.py rec/v2 rec/v2-trim [NN ...]

For each <src>/NN.m4a or NN.wav: decode, find the speech by frame energy, trim, fade, then one plain
gain to the target loudness. Writes <dst>/NN.wav (48 kHz stereo s16) and prints the cut times so
edges can be moved by hand (--start/--end) after a listen.

    python3 rec_prep.py rec/v2 rec/v2-trim 05 --end 05=4.82
"""
import argparse, array, json, math, os, re, subprocess

RATE = 48000
FRAME = 0.02            # 20 ms energy frames
TAIL_IGNORE = 0.15      # stop click lives in the last ~0.1 s
SUSTAIN = 5             # frames (100 ms) of loud = speech started
GAP = 0.25              # silence that ends the run-on after the last loud frame
PAD = 0.15


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(RATE),
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return array.array("h", raw)


def frame_db(s):
    n = int(RATE * FRAME)
    out = []
    for i in range(0, len(s) - n + 1, n):
        acc = sum(x * x for x in s[i:i + n]) / n
        out.append(10 * math.log10(acc / 32768 ** 2) if acc else -120.0)
    return out


def find_cuts(db, dur):
    usable = db[:max(1, int((dur - TAIL_IGNORE) / FRAME))]
    peak = max(usable)
    floor = sorted(usable)[len(usable) // 10]
    loud = peak - 25
    nonsilent = floor + 8
    start_f = next(i for i in range(len(usable) - SUSTAIN)
                   if all(v > loud for v in usable[i:i + SUSTAIN]))
    last = max(i for i, v in enumerate(usable) if v > loud)
    gap_frames, quiet, end_f = int(GAP / FRAME), 0, last
    for i in range(last + 1, len(usable)):
        if usable[i] > nonsilent:
            end_f, quiet = i, 0
        else:
            quiet += 1
            if quiet >= gap_frames:
                break
    start = max(0.0, start_f * FRAME - PAD)
    end = min(dur - TAIL_IGNORE, (end_f + 1) * FRAME + PAD)
    return round(start, 3), round(end, 3), round(floor, 1), round(peak, 1)


def loudness(path, af):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af",
                          af + ",loudnorm=print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return float(json.JSONDecoder().raw_decode(err[err.rindex("{\n"):])[0]["input_i"])


def overrides(items):
    """["05=4.82", ...] -> {"05": 4.82}"""
    out = {}
    for item in items:
        nn, t = item.split("=")
        out[nn] = float(t)
    return out


def main():
    p = argparse.ArgumentParser(description="Trim and level recorded narration takes.",
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("src", help="folder with the raw takes (NN.m4a or NN.wav)")
    p.add_argument("dst", help="folder for the trimmed takes")
    p.add_argument("only", nargs="*", metavar="NN", help="only these takes (default: all)")
    p.add_argument("--target", type=float, default=-24.5, help="clip loudness, LUFS")
    p.add_argument("--start", action="append", default=[], metavar="NN=SEC",
                   help="move a take's start cut by hand (repeatable)")
    p.add_argument("--end", action="append", default=[], metavar="NN=SEC",
                   help="move a take's end cut by hand (repeatable)")
    a = p.parse_args()
    starts, ends, only = overrides(a.start), overrides(a.end), set(a.only)
    os.makedirs(a.dst, exist_ok=True)
    for f in sorted(os.listdir(a.src)):
        m = re.fullmatch(r"(.+)\.(m4a|wav)", f)
        if not m or (only and m[1] not in only):
            continue
        nn, path = m[1], os.path.join(a.src, f)
        s = decode(path)
        dur = len(s) / RATE
        start, end, floor, peak = find_cuts(frame_db(s), dur)
        start = starts.get(nn, start)
        end = ends.get(nn, end)
        length = end - start
        cut = (f"atrim={start}:{end},asetpts=PTS-STARTPTS,"
               f"afade=t=in:d=0.02,afade=t=out:st={length - 0.045:.3f}:d=0.045")
        gain = a.target - loudness(path, cut)
        out = os.path.join(a.dst, nn + ".wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-af",
                        f"{cut},volume={gain:.2f}dB", "-ar", str(RATE), "-ac", "2",
                        "-c:a", "pcm_s16le", out], check=True)
        print(f"{nn}: take {dur:5.2f}s  cut {start:6.3f}-{end:6.3f}  ({length:5.2f}s)  "
              f"gain {gain:+5.1f} dB  floor {floor} peak {peak} dBFS")


if __name__ == "__main__":
    main()
