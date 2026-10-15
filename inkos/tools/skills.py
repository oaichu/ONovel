#!/usr/bin/env python3
"""skills.py prompt <book_dir|book_id> [--max N]  -> prints genre skills+cards text for the book (genres.yaml books/skill_sets).
   skills.py list <book>  -> names only."""
import sys, os, re, yaml
G="/CODE/inkos/genre-kit"
def resolve(book):
    y=yaml.safe_load(open(f"{G}/genres.yaml")); bid=os.path.basename(book.rstrip("/"))
    key=next((v for k,v in y.get("books",{}).items() if bid.startswith(k)),None)
    if not key and os.path.isfile(os.path.join(book,"style-bible.md")):
        g=open(os.path.join(book,"style-bible.md")).read(2000)
        key="ngon-tinh-hien-dai" if "hiện đại" in g else "ngon-tinh-co-dai" if "ngôn tình" in g else "tien-hiep"
    s=y["skill_sets"][key or "tien-hiep"]; return bid,key,s
def body(p): t=open(p).read(); return re.sub(r"^---\n.*?\n---\n","",t,flags=re.S).strip()
if __name__=="__main__":
    cmd,book=sys.argv[1],sys.argv[2]; mx=int(sys.argv[sys.argv.index("--max")+1]) if "--max" in sys.argv else 60000
    bid,key,s=resolve(book)
    if cmd=="list": print(bid,key,"skills:",*s["skills"],"cards:",*s["cards"]); sys.exit()
    out=[f"# KỸ NĂNG THỂ LOẠI ({key})"]
    for c in s["cards"]:
        p=f"{G}/cards/{c}.md"; os.path.isfile(p) and out.append(f"## Thẻ: {c}\n{body(p)}")
    for k in s["skills"]:
        p=f"{G}/skills/{k}/SKILL.md"; os.path.isfile(p) and out.append(f"## Skill: {k}\n{body(p)}")
    print("\n\n".join(out)[:mx])
