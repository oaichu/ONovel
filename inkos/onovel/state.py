"""Canonical story-state engine (single writer). SQLite at <book>/.onovel/state.db.
Everything else (canon.py, lockcheck.py, context, novel-continuity, genre-kit tools) only READS this module's API or files
PROPOSALS (table proposals). Markdown/YAML files story/current_state.md, story/chapter_summaries.md, locked_facts.yaml are
generated VIEWS rendered after each approved commit; edit facts with `onovel facts add`, not by hand.
Tracks: chapters ledger (status GENERATED/COMMITTED/PUBLISHED), locked facts with provenance, entities (characters with realm,
treasures, factions, places), secrets + who knows them, promises, foreshadowing (plot debts), state snapshots, audit log.
State changes only via commit_chapter(), called by the publish transaction after the chapter's gates PASSed."""
import os, re, json, sqlite3, shutil, fcntl, contextlib, yaml
from . import atomic_write
from .gates import now, sha, verdict, count_words
SCHEMA = """
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS chapters(n INTEGER PRIMARY KEY, title TEXT, sha256 TEXT, words INTEGER, status TEXT, summary TEXT, file TEXT, committed_at TEXT, published_at TEXT);
CREATE TABLE IF NOT EXISTS facts(id TEXT PRIMARY KEY, entity TEXT, fact TEXT, since_chapter INTEGER DEFAULT 0, retired_from INTEGER,
  forbid TEXT DEFAULT '[]', allow_if TEXT DEFAULT '[]', source TEXT DEFAULT 'author', provenance_chapter INTEGER, created_at TEXT);
CREATE TABLE IF NOT EXISTS entities(kind TEXT, name TEXT, attrs TEXT DEFAULT '{}', since_chapter INTEGER, updated_chapter INTEGER, PRIMARY KEY(kind, name));
CREATE TABLE IF NOT EXISTS secrets(id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT UNIQUE, since_chapter INTEGER, revealed_chapter INTEGER);
CREATE TABLE IF NOT EXISTS secret_knowers(secret_id INTEGER, who TEXT, since_chapter INTEGER, PRIMARY KEY(secret_id, who));
CREATE TABLE IF NOT EXISTS promises(id INTEGER PRIMARY KEY AUTOINCREMENT, who TEXT, to_whom TEXT, content TEXT, made_chapter INTEGER, due_chapter INTEGER, resolved_chapter INTEGER, UNIQUE(who, content));
CREATE TABLE IF NOT EXISTS foreshadowing(id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT UNIQUE, planted_chapter INTEGER, payoff_chapter INTEGER, status TEXT DEFAULT 'open');
CREATE TABLE IF NOT EXISTS snapshots(chapter INTEGER PRIMARY KEY, current_state TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS proposals(id INTEGER PRIMARY KEY AUTOINCREMENT, chapter INTEGER, kind TEXT, payload TEXT, status TEXT DEFAULT 'pending', source TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS audit(ts TEXT, actor TEXT, action TEXT, detail TEXT);
"""
def path(book): return os.path.join(book, ".onovel", "state.db")
def exists(book): return os.path.exists(path(book))
def connect(book):
    os.makedirs(os.path.dirname(path(book)), exist_ok=True)
    c = sqlite3.connect(path(book), timeout=30); c.row_factory = sqlite3.Row; c.executescript(SCHEMA); return c
@contextlib.contextmanager
def writer(book, actor="onovel"):
    """The only write path: exclusive file lock + one SQLite transaction."""
    os.makedirs(os.path.dirname(path(book)), exist_ok=True)
    with open(path(book) + ".lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX); c = connect(book)
        try:
            c.execute("BEGIN IMMEDIATE"); yield c; c.commit()
        except BaseException: c.rollback(); raise
        finally: c.close()
def audit(c, actor, action, detail): c.execute("INSERT INTO audit VALUES(?,?,?,?)", (now(), actor, action, json.dumps(detail, ensure_ascii=False)[:4000]))
def backup(book, dst):
    src = connect(book); d = sqlite3.connect(dst); src.backup(d); d.close(); src.close()
def restore(book, src):
    with open(path(book) + ".lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX); shutil.copy2(src, path(book) + ".restore"); os.replace(path(book) + ".restore", path(book))
# ---------- readers ----------
def _rows(book, q, a=()):
    if not exists(book): return []
    c = connect(book)
    try: return [dict(r) for r in c.execute(q, a)]
    finally: c.close()
def active_facts(book, n):
    if not exists(book) or not _rows(book, "SELECT 1 FROM meta WHERE key='migrated'"):
        return _yaml_active(book, n)
    out = []
    for r in _rows(book, "SELECT * FROM facts WHERE source='author' AND since_chapter<=? AND (retired_from IS NULL OR retired_from>?) ORDER BY id", (n, n)):
        r["forbid"] = json.loads(r["forbid"] or "[]"); ai = json.loads(r["allow_if"] or "[]"); r["allow_if"] = ai; out.append(r)
    return out
def _yaml_active(book, n):
    p = os.path.join(book, "locked_facts.yaml"); d = (yaml.safe_load(open(p, encoding="utf-8")) if os.path.exists(p) else None) or {}
    retired = {c.get("fact_id") for c in (d.get("changes") or []) if int(c.get("from_chapter", 10**9)) <= n}
    return [f for f in (d.get("facts") or []) if int(f.get("since_chapter", 0)) <= n and f.get("id") not in retired]
def chapters(book): return _rows(book, "SELECT * FROM chapters ORDER BY n")
def chapter(book, n):
    r = _rows(book, "SELECT * FROM chapters WHERE n=?", (n,)); return r[0] if r else None
def last_committed(book):
    r = _rows(book, "SELECT MAX(n) m FROM chapters WHERE status IN ('COMMITTED','PUBLISHED')"); return (r[0]["m"] if r else None) or 0
def chapter_files(book):
    d = os.path.join(book, "chapters")
    return sorted(f for f in os.listdir(d) if re.match(r"^\d+.*\.md$", f)) if os.path.isdir(d) else []
def next_chapter(book):
    """Chapter id allocation: max(ledger, files on disk) + 1 (never reuses an existing number)."""
    nf = max([int(re.match(r"\d+", f).group(0)) for f in chapter_files(book)] or [0])
    return max(last_committed(book), nf) + 1
def current_state(book):
    r = _rows(book, "SELECT current_state FROM snapshots ORDER BY chapter DESC LIMIT 1")
    if r: return r[0]["current_state"]
    p = os.path.join(book, "story", "current_state.md"); return open(p, encoding="utf-8").read() if os.path.exists(p) else ""
def summaries(book, last=3, before=None):
    q = "SELECT n, summary FROM chapters WHERE summary IS NOT NULL AND summary<>''" + (" AND n<?" if before else "") + " ORDER BY n DESC LIMIT ?"
    return list(reversed(_rows(book, q, ((before, last) if before else (last,)))))
def entities(book, kind=None):
    rs = _rows(book, "SELECT * FROM entities" + (" WHERE kind=?" if kind else "") + " ORDER BY updated_chapter DESC", ((kind,) if kind else ()))
    for r in rs: r["attrs"] = json.loads(r["attrs"] or "{}")
    return rs
def open_promises(book): return _rows(book, "SELECT * FROM promises WHERE resolved_chapter IS NULL ORDER BY made_chapter")
def open_foreshadowing(book, upto=None):
    """Open plot debts visible at chapter `upto` (visibility window: never hooks planned for later chapters)."""
    if upto is None: return _rows(book, "SELECT * FROM foreshadowing WHERE status='open' ORDER BY planted_chapter")
    return _rows(book, "SELECT * FROM foreshadowing WHERE status='open' AND COALESCE(planted_chapter,0)<=? ORDER BY planted_chapter", (upto,))
def secrets(book):
    out = []
    for s in _rows(book, "SELECT * FROM secrets WHERE revealed_chapter IS NULL ORDER BY since_chapter"):
        s["knowers"] = [r["who"] for r in _rows(book, "SELECT who FROM secret_knowers WHERE secret_id=?", (s["id"],))]; out.append(s)
    return out
# ---------- gate ----------
def canon_gate(book, chap, n=None, check_number=True):
    """Deterministic canon preflight: chapter id must be the next free id; state must be readable and migrated.
    check_number=False (regate / revision of an EXISTING chapter, audit A05): skip only the duplicate/sequence check."""
    text = open(chap, encoding="utf-8").read(); blocking = []
    if n is None and check_number:
        m = re.search(r"Chương\s+(\d+)", text.split("\n", 1)[0]); n = int(m.group(1)) if m else None
    if exists(book):
        connect(book).execute("SELECT COUNT(*) FROM chapters").fetchone()
        if not _rows(book, "SELECT 1 FROM meta WHERE key='migrated'"): blocking.append(_issue("canon-not-migrated", "state.db chưa migrate"))
    else: blocking.append(_issue("canon-no-state", "chưa có state.db (onovel migrate)"))
    if n is not None and check_number:
        nx = next_chapter(book); row = chapter(book, n)
        if row and row["status"] in ("COMMITTED", "PUBLISHED"): blocking.append(_issue("canon-duplicate", f"chương {n} đã commit"))
        elif n != nx: blocking.append(_issue("canon-sequence", f"chương {n} khác chương kế tiếp {nx}"))
    return verdict("canon", chap, text, blocking, [], [], None, llm=False)
def _issue(rule, reason): return dict(rule_id=rule, source="rule", severity="high", confidence=1.0, evidence_span="", reason=reason, word="", para=None)
# ---------- extraction (MiMo) ----------
EXTRACT_SPEC = ('{"summary":"5-8 câu","current_state":"markdown: vị trí, thời gian, thương tích, vật phẩm, quan hệ, phục bút mở",'
  '"characters":[{"name":"...","realm":"cảnh giới/cấp bậc nếu có","status":"sống/chết/bị thương...","location":"..."}],'
  '"treasures":[{"name":"...","owner":"...","note":"..."}],"factions":[{"name":"...","note":"..."}],'
  '"secrets":[{"content":"...","knowers":["..."],"revealed":false}],'
  '"promises":[{"who":"...","to_whom":"...","content":"...","due_chapter":null,"resolved":false}],'
  '"foreshadowing":{"planted":["..."],"paid_off":["<nội dung phục bút cũ được giải>"]},'
  '"new_facts":[{"id":"kebab-id","entity":"...","fact":"sự thật không đổi được (chết, mất tay, cảnh giới...)"}]}')
def extract(book, text, chat=None):
    if chat is None:
        import sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools")); import mimo; chat = mimo.chat
    st = current_state(book)[:8000]
    open_f = "\n".join(f"- {f['content']}" for f in open_foreshadowing(book)[-40:])
    raw = chat("Đọc chương truyện và trạng thái cũ, trích xuất cập nhật trạng thái truyện. Trả về JSON đúng dạng:\n" + EXTRACT_SPEC +
               "\n\nTRẠNG THÁI CŨ:\n" + st + "\n\nPHỤC BÚT ĐANG MỞ:\n" + open_f + "\n\nCHƯƠNG:\n" + text + "\n\nChỉ trả về JSON hợp lệ.", temperature=0.1, max_tokens=8000)
    m = re.search(r"\{.*\}", raw or "", re.S); d = json.loads(m.group(0) if m else raw)
    if not isinstance(d, dict) or not str(d.get("summary", "")).strip(): raise ValueError("extraction missing summary")
    return d
# ---------- the single writer ----------
def commit_chapter(book, n, title, text, ex, file, actor="publish-txn", replace=False):
    """replace=True: (re)ingest an existing chapter row, e.g. site chapters imported by tools/ingest-site.py."""
    with writer(book, actor) as c:
        row = c.execute("SELECT status FROM chapters WHERE n=?", (n,)).fetchone()
        if row and row["status"] in ("COMMITTED", "PUBLISHED") and not replace: raise RuntimeError(f"chapter {n} already committed")
        c.execute("INSERT OR REPLACE INTO chapters(n,title,sha256,words,status,summary,file,committed_at) VALUES(?,?,?,?,?,?,?,?)",
                  (n, title, sha(text), count_words(text), "COMMITTED", str(ex.get("summary", "")).strip(), file, now()))
        if ex.get("current_state"): c.execute("INSERT OR REPLACE INTO snapshots VALUES(?,?,?)", (n, str(ex["current_state"]).strip(), now()))
        for kind, key in (("character", "characters"), ("treasure", "treasures"), ("faction", "factions")):
            for e in ex.get(key) or []:
                if not isinstance(e, dict) or not e.get("name"): continue
                old = c.execute("SELECT attrs, since_chapter FROM entities WHERE kind=? AND name=?", (kind, e["name"])).fetchone()
                attrs = json.loads(old["attrs"]) if old else {}
                for k, v in e.items():
                    if k != "name" and v not in (None, ""): attrs[k] = v
                if kind == "character" and e.get("realm"):
                    hist = attrs.setdefault("realm_history", [])
                    if not hist or hist[-1][1] != e["realm"]: hist.append([n, e["realm"]])
                c.execute("INSERT OR REPLACE INTO entities VALUES(?,?,?,?,?)", (kind, e["name"], json.dumps(attrs, ensure_ascii=False), old["since_chapter"] if old else n, n))
        for s in ex.get("secrets") or []:
            if not isinstance(s, dict) or not s.get("content"): continue
            c.execute("INSERT OR IGNORE INTO secrets(content, since_chapter) VALUES(?,?)", (s["content"], n))
            sid = c.execute("SELECT id FROM secrets WHERE content=?", (s["content"],)).fetchone()["id"]
            for w in s.get("knowers") or []: c.execute("INSERT OR IGNORE INTO secret_knowers VALUES(?,?,?)", (sid, w, n))
            if s.get("revealed"): c.execute("UPDATE secrets SET revealed_chapter=? WHERE id=?", (n, sid))
        for p in ex.get("promises") or []:
            if not isinstance(p, dict) or not p.get("content"): continue
            c.execute("INSERT OR IGNORE INTO promises(who,to_whom,content,made_chapter,due_chapter) VALUES(?,?,?,?,?)",
                      (p.get("who", ""), p.get("to_whom", ""), p["content"], n, p.get("due_chapter")))
            if p.get("resolved"): c.execute("UPDATE promises SET resolved_chapter=? WHERE who=? AND content=?", (n, p.get("who", ""), p["content"]))
        fs = ex.get("foreshadowing") or {}
        for t in fs.get("planted") or []: c.execute("INSERT OR IGNORE INTO foreshadowing(content, planted_chapter) VALUES(?,?)", (str(t), n))
        for t in fs.get("paid_off") or []: c.execute("UPDATE foreshadowing SET status='paid', payoff_chapter=? WHERE status='open' AND content=?", (n, str(t)))
        for f in ex.get("new_facts") or []:  # never auto-lock: proposals for the author
            c.execute("INSERT INTO proposals(chapter,kind,payload,source,created_at) VALUES(?,?,?,?,?)", (n, "fact", json.dumps(dict(f, since_chapter=n), ensure_ascii=False), "mimo-extract", now()))
        audit(c, actor, "commit_chapter", {"n": n, "sha256": sha(text)})
    render_views(book)
def mark_published(book, n, actor="publish"):
    with writer(book, actor) as c:
        c.execute("UPDATE chapters SET status='PUBLISHED', published_at=? WHERE n=?", (now(), n)); audit(c, actor, "published", {"n": n})
def add_fact(book, fid, entity, fact, since=1, forbid=(), allow_if=(), source="author"):
    with writer(book, "author") as c:
        c.execute("INSERT OR REPLACE INTO facts(id,entity,fact,since_chapter,forbid,allow_if,source,created_at) VALUES(?,?,?,?,?,?,?,?)",
                  (fid, entity, fact, since, json.dumps(list(forbid), ensure_ascii=False), json.dumps(allow_if if isinstance(allow_if, str) else list(allow_if), ensure_ascii=False), source, now()))
        audit(c, "author", "add_fact", {"id": fid})
    render_views(book)
def render_views(book):
    s = os.path.join(book, "story"); os.makedirs(s, exist_ok=True)
    st = current_state(book)
    if st: atomic_write(os.path.join(s, "current_state.md"), st.rstrip() + "\n")
    rows = summaries(book, last=100000)
    if rows: atomic_write(os.path.join(s, "chapter_summaries.md"), "<!-- GENERATED by onovel state (do not edit) -->\n" + "".join(f"\n## Chương {r['n']}\n{r['summary']}\n" for r in rows))
    facts = _rows(book, "SELECT * FROM facts WHERE source='author' ORDER BY since_chapter, id")
    if facts:
        out = {"language": "vi", "facts": [], "changes": []}
        for f in facts:
            ai = json.loads(f["allow_if"] or "[]")
            out["facts"].append(dict(id=f["id"], entity=f["entity"], fact=f["fact"], since_chapter=f["since_chapter"], forbid=json.loads(f["forbid"] or "[]"), allow_if=ai))
            if f["retired_from"]: out["changes"].append({"fact_id": f["id"], "from_chapter": f["retired_from"]})
        atomic_write(os.path.join(book, "locked_facts.yaml"), "# GENERATED view of .onovel/state.db (edit via: onovel facts add / lockcheck.py add)\n" + yaml.safe_dump(out, allow_unicode=True, sort_keys=False))
# ---------- migration ----------
def migrate(book, published_upto=0, force=False):
    """Import legacy files into state.db (idempotent). Chapters on disk become COMMITTED (PUBLISHED if n <= published_upto)."""
    if exists(book) and _rows(book, "SELECT 1 FROM meta WHERE key='migrated'") and not force: return {"skipped": True}
    rd = lambda p: open(p, encoding="utf-8").read() if os.path.exists(p) else ""
    st = os.path.join(book, "story"); n_f = n_c = n_p = n_h = 0
    with writer(book, "migrate") as c:
        d = yaml.safe_load(rd(os.path.join(book, "locked_facts.yaml"))) or {}
        ret = {x.get("fact_id"): int(x.get("from_chapter")) for x in (d.get("changes") or []) if x.get("fact_id")}
        for f in d.get("facts") or []:
            c.execute("INSERT OR REPLACE INTO facts(id,entity,fact,since_chapter,retired_from,forbid,allow_if,source,provenance_chapter,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                      (f["id"], f.get("entity", ""), f.get("fact", ""), int(f.get("since_chapter", 0)), ret.get(f["id"]), json.dumps(f.get("forbid") or [], ensure_ascii=False),
                       json.dumps(f.get("allow_if") if isinstance(f.get("allow_if"), str) else (f.get("allow_if") or []), ensure_ascii=False), "author", f.get("since_chapter"), now())); n_f += 1
        c.execute("DELETE FROM proposals WHERE source='legacy-proposed'")
        for f in (yaml.safe_load(rd(os.path.join(book, "locked_facts.proposed.yaml"))) or {}).get("proposed") or []:
            c.execute("INSERT INTO proposals(chapter,kind,payload,source,created_at) VALUES(?,?,?,?,?)", (f.get("since_chapter"), "fact", json.dumps(f, ensure_ascii=False), "legacy-proposed", now())); n_p += 1
        summ = {}; th = None
        for line in rd(os.path.join(st, "chapter_summaries.md")).splitlines():  # inkos table format
            if not line.startswith("|"): th = None if not line.strip() else th; continue
            cells = [x.strip() for x in line.strip().strip("|").split("|")]
            if th is None: th = [x.lower() for x in cells]; continue
            if set("".join(cells)) <= set("-: ") or not cells[0].isdigit(): continue
            r = dict(zip(th, cells))
            summ[int(cells[0])] = " ".join(f"{k.title()}: {v}." for k, v in r.items() if k in ("key events", "state changes", "hook activity") and v)
        for blk in re.split(r"\n(?=## )", rd(os.path.join(st, "chapter_summaries.md"))):
            m = re.match(r"##\s*Chương\s+(\d+)\s*\n(.*)", blk.strip(), re.S)
            if m and m.group(2).strip(): summ[int(m.group(1))] = m.group(2).strip()
        for fn in chapter_files(book):
            n = int(re.match(r"\d+", fn).group(0)); t = rd(os.path.join(book, "chapters", fn))
            c.execute("INSERT OR REPLACE INTO chapters(n,title,sha256,words,status,summary,file,committed_at,published_at) VALUES(?,?,?,?,?,?,?,?,?)",
                      (n, re.sub(r"^#+\s*", "", t.split("\n", 1)[0]).strip(), sha(t), count_words(t), "PUBLISHED" if n <= published_upto else "COMMITTED",
                       summ.get(n, ""), fn, now(), now() if n <= published_upto else None)); n_c += 1
        cs = rd(os.path.join(st, "current_state.md"))
        if cs: c.execute("INSERT OR REPLACE INTO snapshots VALUES(?,?,?)", (max([int(re.match(r'\d+', f).group(0)) for f in chapter_files(book)] or [0]), cs, now()))
        hdr = None
        for line in rd(os.path.join(st, "pending_hooks.md")).splitlines():
            if line.startswith("|"):
                cells = [x.strip() for x in line.strip().strip("|").split("|")]
                if hdr is None: hdr = cells; continue
                if set("".join(cells)) <= set("-: "): continue
                r = dict(zip(hdr, cells)); txt = r.get("expected_payoff") or ""
                if len(txt) < 8: continue
                try: pc = int(r.get("start_chapter") or 0)
                except ValueError: pc = 0
                stt = "paid" if (r.get("status") or "").lower() in ("resolved", "paid", "closed") else "open"
                c.execute("INSERT OR IGNORE INTO foreshadowing(content, planted_chapter, status) VALUES(?,?,?)", (f"[{r.get('hook_id','')}] {txt}"[:500], pc, stt)); n_h += 1
            else:
                m = re.match(r"\s*[-*]\s+(.{8,})", line)
                if m: c.execute("INSERT OR IGNORE INTO foreshadowing(content, planted_chapter) VALUES(?,?)", (m.group(1).strip()[:500], 0)); n_h += 1
        c.execute("INSERT OR REPLACE INTO meta VALUES('migrated', ?)", (now(),)); audit(c, "migrate", "migrate", {"facts": n_f, "chapters": n_c})
    return {"facts": n_f, "chapters": n_c, "proposals": n_p, "foreshadowing": n_h}
def sync_files(book, published_upto=0):
    """Add chapter files missing from the ledger (e.g. written by `inkos import` after migration) as legacy rows."""
    have = {r["n"] for r in chapters(book)}; added = []
    with writer(book, "sync") as c:
        for fn in chapter_files(book):
            n = int(re.match(r"\d+", fn).group(0))
            if n in have: continue
            t = open(os.path.join(book, "chapters", fn), encoding="utf-8").read(); pub = n <= published_upto
            c.execute("INSERT INTO chapters(n,title,sha256,words,status,summary,file,committed_at,published_at) VALUES(?,?,?,?,?,?,?,?,?)",
                      (n, re.sub(r"^#+\s*", "", t.split("\n", 1)[0]).strip(), sha(t), count_words(t), "PUBLISHED" if pub else "COMMITTED", "", fn, now(), now() if pub else None))
            added.append(n)
        if added: audit(c, "sync", "sync_files", {"added": added})
    return {"synced": added}
def revise_chapter(book, n, text, file, actor="revise"):
    """Revision of an existing chapter (e.g. expansion): new sha/words; canon facts are unchanged by contract."""
    with writer(book, actor) as c:
        c.execute("UPDATE chapters SET sha256=?, words=?, status='COMMITTED', file=?, committed_at=? WHERE n=?", (sha(text), count_words(text), file, now(), n))
        audit(c, actor, "revise_chapter", {"n": n, "sha256": sha(text), "words": count_words(text)})
