#!/usr/bin/env python3
"""tools/lessons.py: thin wrapper over /CODE/lessons-library/lessons.py with domain 'novel' as default (REWRITTEN 2026-10-15).
  lessons.py prompt <book_dir>      novel-domain + global + book-project lessons
  lessons.py learn <book_dir> "text" [--domain]   record a book lesson (project tier) or, with --domain, a novel-domain lesson"""
import sys, subprocess
L = "/CODE/lessons-library/lessons.py"; a = sys.argv[1:]
if not a: print(__doc__); sys.exit(2)
if a[0] == "prompt": sys.exit(subprocess.call(["python3", L, "prompt", "--domain", "novel", "--project", a[1]]))
if a[0] == "learn":
    tier = ["--tier", "domain"] if "--domain" in a else ["--tier", "project", "--project", a[1]]
    sys.exit(subprocess.call(["python3", L, "learn", a[2], "--domain", "novel", "--tag", "novel.sh"] + tier))
sys.exit(subprocess.call(["python3", L] + a))
