#!/usr/bin/env python3
"""lessons.py: shared lessons store (REWRITTEN 2026-10-15 after /CODE loss).
Tiers: global (LIB/global), domain (LIB/domains/<d>), project (<project>/.lessons). Each tier dir holds lessons.jsonl,
one JSON per line: {id, ts, tier, domain, text, tags, status(active|candidate|retired), source}.
  prompt  [--domain D] [--project DIR] [--max N]   print active lessons (global + domain + project) as a prompt block
  learn   "text" [--tier global|domain|project] [--domain D] [--project DIR] [--tag T] [--candidate]
  curate  [--domain D] [--project DIR] [--inbox]   dedupe (normalised text), optional ingest of ~/.pi/agent/lessons-inbox.jsonl as candidates
  promote ID --to domain|global [--domain D]       move a lesson up a tier (and activate it)
  list    [--tier ...] [--all]
  ensure                                           create layout + symlinks (novel domain -> /CODE/inkos/genre-kit/lessons, pi skill link)
Never stores secrets: text matching key/token patterns is refused."""
import sys, os, re, json, argparse, hashlib, datetime, unicodedata
LIB = os.path.dirname(os.path.realpath(__file__))
SECRET = re.compile(r"(sk-[a-z0-9-]{10,}|api[_-]?key\s*[:=]|password\s*[:=]|token\s*[:=]|gh[po]_[A-Za-z0-9]{20,})", re.I)
def tdir(tier, domain=None, project=None):
    if tier == "global": return os.path.join(LIB, "global")
    if tier == "domain": return os.path.join(LIB, "domains", domain or "general")
    return os.path.join(os.path.abspath(project or "."), ".lessons")
def load(d):
    p = os.path.join(d, "lessons.jsonl")
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if os.path.exists(p) else []
def save(d, rows):
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "lessons.jsonl"), "w", encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
def norm(t): return re.sub(r"\W+", " ", unicodedata.normalize("NFC", re.sub(r"^\s*-?\s*(\[[^\]]*\])*", "", t)).lower()).strip()
def learn(text, tier="domain", domain=None, project=None, tags=(), status="active", source="cli"):
    if SECRET.search(text): raise SystemExit("refused: looks like a secret")
    d = tdir(tier, domain, project); rows = load(d)
    if any(norm(r["text"]) == norm(text) for r in rows): return None
    r = dict(id=hashlib.sha1((tier + str(domain) + text).encode()).hexdigest()[:8], ts=datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
             tier=tier, domain=domain, text=text.strip(), tags=list(tags), status=status, source=source)
    rows.append(r); save(d, rows); return r
def prompt(domain=None, project=None, mx=60):
    out = []
    for label, d in (("Toàn cục", tdir("global")), (f"Lĩnh vực {domain}", tdir("domain", domain) if domain else None), ("Dự án", tdir("project", project=project) if project else None)):
        if not d: continue
        rows = [r for r in load(d) if r.get("status") == "active"][-mx:]
        if rows: out.append(f"## Bài học: {label}\n" + "\n".join(f"- {r['text']}" for r in rows))
    return "\n\n".join(out)
def all_dirs(project=None):
    ds = [tdir("global")] + [os.path.join(LIB, "domains", x) for x in sorted(os.listdir(os.path.join(LIB, "domains")))]
    return ds + ([tdir("project", project=project)] if project else [])
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("arg", nargs="?")
    ap.add_argument("--tier", default="domain"); ap.add_argument("--domain"); ap.add_argument("--project"); ap.add_argument("--tag", action="append", default=[])
    ap.add_argument("--max", type=int, default=60); ap.add_argument("--candidate", action="store_true"); ap.add_argument("--inbox", action="store_true")
    ap.add_argument("--to"); ap.add_argument("--all", action="store_true"); a = ap.parse_args()
    if a.cmd == "prompt": print(prompt(a.domain, a.project, a.max))
    elif a.cmd == "learn":
        r = learn(a.arg, a.tier, a.domain, a.project, a.tag, "candidate" if a.candidate else "active"); print(json.dumps(r, ensure_ascii=False) if r else "duplicate, skipped")
    elif a.cmd == "list":
        for d in all_dirs(a.project):
            for r in load(d):
                if a.all or r.get("status") == "active": print(f"{r['id']} [{r['tier']}/{r.get('domain') or '-'}/{r['status']}] {r['text']}")
    elif a.cmd == "curate":
        n = 0
        if a.inbox:
            p = os.path.expanduser("~/.pi/agent/lessons-inbox.jsonl")
            for l in open(p, encoding="utf-8") if os.path.exists(p) else []:
                try: t = json.loads(l).get("text", "")
                except Exception: continue
                if t and len(t) < 400 and "REDACTED" not in t and learn(t, "domain", a.domain or "pi", status="candidate", source="pi-inbox"): n += 1
        for d in all_dirs(a.project):
            rows, seen, keep = load(d), set(), []
            for r in rows:
                k = norm(r["text"])
                if k in seen: continue
                seen.add(k); keep.append(r)
            if len(keep) != len(rows): save(d, keep); print(f"{d}: removed {len(rows)-len(keep)} duplicates")
        print(f"ingested {n} candidates")
    elif a.cmd == "promote":
        for d in all_dirs(a.project):
            rows = load(d); hit = [r for r in rows if r["id"] == a.arg]
            if hit:
                r = hit[0]; save(d, [x for x in rows if x["id"] != a.arg])
                learn(r["text"], a.to or "global", a.domain or r.get("domain"), tags=r.get("tags", []), source="promoted:" + r["id"]); print("promoted", a.arg, "->", a.to); return
        raise SystemExit("id not found")
    elif a.cmd == "ensure":
        for x in ("global", "domains/grok-bot", "domains/pi", "references"): os.makedirs(os.path.join(LIB, x), exist_ok=True)
        nov = os.path.join(LIB, "domains", "novel"); tgt = "/CODE/inkos/genre-kit/lessons"; os.makedirs(tgt, exist_ok=True)
        if not os.path.islink(nov): os.symlink(tgt, nov)
        sk = os.path.expanduser("~/.pi/agent/skills/lessons-library")
        if not os.path.exists(sk): os.makedirs(os.path.dirname(sk), exist_ok=True); os.symlink("/CODE/lessons-library", sk)
        print("ok", LIB)
    else: ap.error("unknown command")
if __name__ == "__main__": main()
