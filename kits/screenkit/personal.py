"""Personal names that must never reach a frame. screenkit and duokit fail the build if one shows on
screen after the spec's substitutions.

The names come from a text file that stays OUT of any repo you publish:
  - the file named by the PERSONAL_NAMES environment variable, or else
  - the first personal.txt found in the beat's folder or a folder above it.
One name per line: every user name, host name, home folder and e-mail of every computer you capture
on. Lines starting with # are comments. A line "re:<regex>" is a regular expression, for a name that
is also part of a longer word, e.g. re:/Users/jo(?![A-Za-z0-9_]) matches /Users/jo but not /Users/john.
No file = the build stops: a missing list must not look like a passed check.
"""
import os, re, sys

def _find():
    path = os.environ.get("PERSONAL_NAMES")
    if path:
        return path
    d = os.getcwd()
    while True:
        p = os.path.join(d, "personal.txt")
        if os.path.exists(p):
            return p
        up = os.path.dirname(d)
        if up == d:
            sys.exit("personal.txt not found (set PERSONAL_NAMES or put personal.txt in the project folder): "
                     "the personal-name check cannot run")
        d = up

def _load(path):
    plain, rx = [], []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("re:"):
            rx.append(re.compile(line[3:]))
        else:
            plain.append(line)
    return plain, rx

PERSONAL, _RX = _load(_find())

def found(plain):
    """The first personal name in plain screen text, or None."""
    for bad in PERSONAL:
        if bad in plain: return bad
    for r in _RX:
        m = r.search(plain)
        if m: return m.group(0)
    return None
