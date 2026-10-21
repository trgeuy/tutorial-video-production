#!/usr/bin/env python3
"""Capture REAL console output of a program the way a viewer sees it, typing keys from a list.

    python3 pty_capture.py [options] <workdir> <out.raw> <steps.json> <program> [args...]
    e.g. python3 pty_capture.py --first-wait "A>" /tmp/scratch run.raw steps.json mysim machine.toml

Run it on a SCRATCH copy of the program's files (a program can change its own data files).
steps.json: [{"send": "DIR\\r", "wait": "A>", "pause": 0.0}, ...] -- `wait` is text to wait for
after sending (8 s timeout, logged), `pause` seconds before sending. Control keys: "\\u0005" = ^E.
Write steps.json with Python or an editor, not `echo`: zsh's echo turns \\r into a real CR.

Before the first step the script waits for --first-wait (if given) and then --settle seconds: a key
typed the instant a prompt appears can be lost (in our capture "DIR" became "IR").
The output is the raw bytes the program wrote (no timing). View it:
    perl -pe 's/\\r//g; s/\\e\\[K//g' out.raw | cat -v
"""
import argparse, json, os, pty, select, struct, sys, termios, fcntl, time

p = argparse.ArgumentParser(description="Capture a program's console output, typing keys from a list.",
                            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
p.add_argument("--first-wait", help="text to wait for before the first step (30 s timeout)")
p.add_argument("--settle", type=float, default=1.5, help="seconds to wait after --first-wait")
p.add_argument("--cols", type=int, default=120)
p.add_argument("--rows", type=int, default=30)
p.add_argument("--key-gap", type=float, default=0.03, help="seconds between keys")
p.add_argument("workdir")
p.add_argument("outfile")
p.add_argument("steps")
p.add_argument("program", nargs=argparse.REMAINDER, help="the program and its arguments")
a = p.parse_args()
if not a.program:
    p.error("no program given")
workdir, outfile, steps, argv = a.workdir, a.outfile, json.load(open(a.steps)), a.program

pid, fd = pty.fork()
if pid == 0:
    os.chdir(workdir)
    os.environ["COLUMNS"], os.environ["LINES"] = str(a.cols), str(a.rows)
    os.execvp(argv[0], argv)
fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", a.rows, a.cols, 0, 0))

buf, mark = b"", 0
def pump(timeout):
    """Read what is there; False at EOF. macOS reports a closed pty as readable and then returns
    b"" forever -- stop on an empty read, or this loop spins at 100 % CPU."""
    global buf
    r, _, _ = select.select([fd], [], [], timeout)
    if not r: return True
    try: d = os.read(fd, 4096)
    except OSError: return False
    if not d: return False
    buf += d; return True

def wait_for(text, timeout=8.0):
    end = time.time() + timeout
    while time.time() < end:
        if text.encode() in buf[mark:]: return True
        if not pump(0.2): return False
    sys.stderr.write(f"TIMEOUT waiting for {text!r}; tail={buf[-160:]!r}\n"); return False

if a.first_wait: wait_for(a.first_wait, 30)
time.sleep(a.settle)
for s in steps:
    time.sleep(s.get("pause", 0.0))
    mark = len(buf)
    for ch in s["send"]:
        os.write(fd, ch.encode()); time.sleep(a.key_gap)
    if s.get("wait"): sys.stderr.write(f"sent {s['send']!r} -> {wait_for(s['wait'])}\n")
end = time.time() + 3
while time.time() < end and pump(0.5): pass
open(outfile, "wb").write(buf)
print(f"{len(buf)} bytes -> {outfile}")
