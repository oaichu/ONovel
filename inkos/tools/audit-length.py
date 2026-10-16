#!/usr/bin/env python3
"""audit-length.py [--min 3000] [--json out] book...  word count (onovel.gates.count_words) of every chapter in the inkos book
and on the site (/CODE/oaichu-novels/src/content/chapters/<book>), flags chapters under --min."""
import sys, os, re, json, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from onovel.gates import count_words
from onovel import state
SITE = os.environ.get("ONOVEL_SITE_CHAPTERS", "/CODE/oaichu-novels/src/content/chapters")
P = os.environ.get("INKOS_PROJECT", "/CODE/inkos-books/xemtruyen")
ap = argparse.ArgumentParser(); ap.add_argument("books", nargs="+"); ap.add_argument("--min", type=int, default=3000); ap.add_argument("--json"); a = ap.parse_args()
res = {}
for b in a.books:
    bd = os.path.join(P, "books", b); rows = {}
    for f in state.chapter_files(bd):
        n = int(re.match(r"\d+", f).group(0)); rows.setdefault(n, {})["book"] = count_words(open(os.path.join(bd, "chapters", f), encoding="utf-8").read())
    sd = os.path.join(SITE, b)
    for f in sorted(os.listdir(sd)) if os.path.isdir(sd) else []:
        m = re.match(r"(\d+)\.md$", f)
        if m: rows.setdefault(int(m.group(1)), {})["site"] = count_words(open(os.path.join(sd, f), encoding="utf-8").read())
    res[b] = {n: rows[n] for n in sorted(rows)}
    short_site = [n for n, r in res[b].items() if r.get("site", 10**9) < a.min]; short_book = [n for n, r in res[b].items() if r.get("book", 10**9) < a.min]
    print(f"== {b}: {len(res[b])} chapters, site<{a.min}: {len(short_site)}, book<{a.min}: {len(short_book)}")
    print("   " + " ".join(f"{n}:{r.get('site','-')}/{r.get('book','-')}" for n, r in res[b].items()))
if a.json: json.dump(res, open(a.json, "w"), indent=1)
