#!/usr/bin/env python3
"""draftcheck.py <draft.md> <target_words>: exit 1 (+reason on stdout) if the draft is degenerate:
over 2.5x target words, or heavy repetition (zlib ratio < 0.2, or >25% of sentences/paragraphs duplicated)."""
import sys, re, zlib
t = open(sys.argv[1], encoding="utf-8", errors="ignore").read(); tgt = int(sys.argv[2]); w = len(t.split())
if w > 2.5 * tgt: print(f"too long {w} words > 2.5x{tgt}"); sys.exit(1)
b = t.encode(); r = len(zlib.compress(b, 9)) / max(1, len(b))
if len(b) > 4000 and r < 0.2: print(f"repetitive (zlib ratio {r:.2f})"); sys.exit(1)
ss = [s.strip().lower() for s in re.split(r"(?<=[.!?…])\s+|\n+", t) if len(s.strip()) > 25]
if len(ss) > 20:
    d = 1 - len(set(ss)) / len(ss)
    if d > 0.25: print(f"repetitive ({d:.0%} duplicate sentences)"); sys.exit(1)
print(f"ok {w} words zlib={r:.2f}")
