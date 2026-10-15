"""Shared book helpers: load style bible (YAML front matter + body), locked facts, chapter split."""
import os, re, yaml
def bible_path(book):
    for n in ("style-bible.md", "story/style_guide.md"):
        p = os.path.join(book, n)
        if os.path.exists(p): return p
def load_bible(book):
    p = bible_path(book); 
    if not p: return {}, ""
    t = open(p, encoding="utf-8").read(); meta = {}
    m = re.match(r"---\n(.*?)\n---\n?", t, re.S)
    if m:
        try: meta = yaml.safe_load(m.group(1)) or {}
        except Exception: meta = {}
    return meta, t
def load_facts(book):
    p = os.path.join(book, "locked_facts.yaml")
    if not os.path.exists(p): return []
    return (yaml.safe_load(open(p, encoding="utf-8")) or {}).get("facts", []) or []
def chapter_no(path, text=""):
    m = re.search(r"(\d+)", os.path.basename(path)) or re.search(r"Chương\s+(\d+)", text)
    return int(m.group(1)) if m else 0
def paras(text): return [p for p in re.split(r"\n\s*\n", text) if p.strip()]
