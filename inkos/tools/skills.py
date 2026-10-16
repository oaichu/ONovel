#!/usr/bin/env python3
"""skills.py prompt <book_dir|book_id> [--max N]  -> genre skills+cards text for the book.
   skills.py list <book>  -> names only.
The skill set comes ONLY from the validated book manifest (<book>/onovel.yaml: skill_set or genre_id); no name guessing."""
import sys, os, re, yaml
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from onovel import manifest as mf, GENRE_KIT as G
def resolve(book):
    if not os.path.isdir(book): book = os.path.join(os.environ.get("INKOS_PROJECT", "/CODE/inkos-books/xemtruyen"), "books", book)
    m = mf.load(book); key = m.get("skill_set", m["genre_id"])
    return m["id"], key, mf.genres()["skill_sets"][key]
def body(p): t=open(p, encoding="utf-8").read(); return re.sub(r"^---\n.*?\n---\n","",t,flags=re.S).strip()
if __name__=="__main__":
    cmd,book=sys.argv[1],sys.argv[2]; mx=int(sys.argv[sys.argv.index("--max")+1]) if "--max" in sys.argv else 60000
    try: bid,key,s=resolve(book)
    except mf.ManifestError as e: print(f"skills.py: {e}", file=sys.stderr); sys.exit(2)
    if cmd=="list": print(bid,key,"skills:",*s["skills"],"cards:",*s["cards"]); sys.exit()
    out=[f"# KỸ NĂNG THỂ LOẠI ({key})"]
    for c in s["cards"]:
        p=f"{G}/cards/{c}.md"; os.path.isfile(p) and out.append(f"## Thẻ: {c}\n{body(p)}")
    for k in s["skills"]:
        p=f"{G}/skills/{k}/SKILL.md"; os.path.isfile(p) and out.append(f"## Skill: {k}\n{body(p)}")
    print("\n\n".join(out)[:mx])
