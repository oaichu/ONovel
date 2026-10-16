#!/usr/bin/env python3
"""tools/lessons.py: wrapper over the lessons library (ONOVEL_LESSONS, default /CODE/lessons-library), domain 'novel'.
  lessons.py prompt <book_dir>      global + novel + genre (novel.<genre_id> from onovel.yaml) + book-project lessons
  lessons.py learn <book_dir> "text" [--domain]   record a book lesson (project tier) or, with --domain, a novel-domain lesson"""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from onovel import LESSONS, manifest as mf
L = os.path.join(LESSONS, "lessons.py"); a = sys.argv[1:]
if not a: print(__doc__); sys.exit(2)
if not os.path.exists(L): sys.exit(0)
if a[0] == "prompt":
    rc = subprocess.call(["python3", L, "prompt", "--domain", "novel", "--project", a[1]])
    try:
        g = mf.load(a[1])["genre_id"]
        out = subprocess.run(["python3", L, "list", "--tier", "domain", "--domain", f"novel.{g}"], capture_output=True, text=True).stdout.strip()
        if out: print(f"\n# BÀI HỌC THỂ LOẠI ({g})\n" + "\n".join("- " + l.split("] ", 1)[-1] for l in out.splitlines()[-30:]))
    except Exception: pass
    sys.exit(rc)
if a[0] == "learn":
    tier = ["--tier", "domain"] if "--domain" in a else ["--tier", "project", "--project", a[1]]
    sys.exit(subprocess.call(["python3", L, "learn", a[2], "--domain", "novel", "--tag", "novel.sh"] + tier))
sys.exit(subprocess.call(["python3", L] + a))
