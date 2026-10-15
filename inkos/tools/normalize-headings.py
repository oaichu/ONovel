#!/usr/bin/env python3
"""normalize-headings.py [--style colon|dot] [--dry-run] <files...>  (REWRITTEN 2026-10-15)
Makes the first line '# Chương N: Tên' (colon, default) or '# Chương N · Tên' (dot, DKGH). Removes duplicate heading lines,
replaces em dashes in headings. Prints one line per changed file."""
import sys, re, argparse
ap = argparse.ArgumentParser(); ap.add_argument("files", nargs="+"); ap.add_argument("--style", default="colon"); ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args(); sep = ": " if a.style == "colon" else " · "
for p in a.files:
    t = open(p, encoding="utf-8").read(); lines = t.lstrip("\ufeff\n").split("\n")
    m = re.match(r"^#*\s*(?:Chương|Chapter)\s+(\d+)\s*[:：·.\-–—]?\s*(.*)$", lines[0].strip(), re.I)
    if not m: print("SKIP(no heading)", p); continue
    title = m.group(2).strip().replace("—", ",").strip(" ,")
    new = f"# Chương {int(m.group(1))}" + (sep + title if title else ""); body = lines[1:]
    while body and (not body[0].strip() or re.match(r"^#*\s*Chương\s+\d+", body[0].strip())): body.pop(0)
    out = new + "\n\n" + "\n".join(body).rstrip() + "\n"
    if out != t:
        print("FIX", p, "->", new)
        if not a.dry_run: open(p, "w", encoding="utf-8").write(out)
