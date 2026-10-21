#!/usr/bin/env python3
"""Record a command's terminal output as a macOS `script -r` file.

    python3 pty_rec.py <out.rec> <cols> <rows> <seconds> <command> [args...]

Runs the command in a pseudo-terminal of the given size and writes each output chunk as an "o"
record (recio's format), so rec2frames.py replays it like a real `script -r` capture. Stops after
<seconds> or when the command exits. For a watch-only program (a log, a monitor) where no keys are
typed; a capture with typing comes from `script -r` itself. Needs recio.py next to this file.
"""
import fcntl, os, pty, select, signal, struct, sys, termios, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recio

if len(sys.argv) < 6:
    sys.exit(__doc__)
out, cols, rows, secs, cmd = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4]), sys.argv[5:]
pid, fd = pty.fork()
if pid == 0:
    os.environ["COLUMNS"], os.environ["LINES"] = str(cols), str(rows)
    os.execvp(cmd[0], cmd)
fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
recs, end = [(time.time(), "s", b"")], time.time() + secs
while time.time() < end:
    r, _, _ = select.select([fd], [], [], 0.2)
    if not r: continue
    try: data = os.read(fd, 4096)
    except OSError: break
    if not data: break
    recs.append((time.time(), "o", data))
try: os.kill(pid, signal.SIGINT); time.sleep(0.3); os.kill(pid, signal.SIGTERM)
except ProcessLookupError: pass
recs.append((time.time(), "e", b""))
recio.write(out, recs)
print(f"{len(recs)} records, {sum(len(r[2]) for r in recs)} bytes -> {out}")
