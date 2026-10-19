"""Publish transaction (ONovel audit P0.3/P0.4): prepare -> validate -> commit (chapter file + canonical state, atomic, rollback)
-> publish (publish-inkos.sh publishes ONLY chapters whose manifest shows a PASS verdict and matching sha256).
Per-chapter manifest <book>/.onovel/chapters/NNNN.json records status, sha256, gate evidence and history.
Statuses: QUARANTINED (gate ERROR / commit failure, retried later), COMMIT_FAILED, COMMITTED, PUBLISHED."""
import os, re, json, shutil, time
from . import atomic_write, state, gates
def mpath(book, n): return os.path.join(book, ".onovel", "chapters", f"{n:04d}.json")
def load(book, n):
    p = mpath(book, n); return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None
def save(book, m): atomic_write(mpath(book, m["n"]), json.dumps(m, ensure_ascii=False, indent=1))
def _hist(m, status, detail=""):
    m["status"] = status; m.setdefault("history", []).append({"ts": gates.now(), "status": status, "detail": str(detail)[:500]}); return m
def record(book, n, status, sha=None, gate=None, file=None, run_dir=None, detail=""):
    m = load(book, n) or {"book": os.path.basename(os.path.normpath(book)), "n": n}
    if sha: m["sha256"] = sha
    if gate is not None: m["gate"] = gate
    if file: m["file"] = file
    if run_dir: m["run_dir"] = run_dir
    m["attempts"] = m.get("attempts", 0) + (1 if status in ("QUARANTINED", "COMMIT_FAILED") else 0)
    save(book, _hist(m, status, detail)); return m
class TxnError(Exception): pass
def quarantine(book, run_dir, n, reason, qroot=None):
    qroot = qroot or os.path.join(os.path.dirname(os.path.normpath(run_dir)), "quarantine"); os.makedirs(qroot, exist_ok=True)
    dst = os.path.join(qroot, os.path.basename(os.path.normpath(run_dir)))
    if not os.path.exists(dst): shutil.copytree(run_dir, dst)
    cur = load(book, n)
    if cur and cur.get("status") in ("COMMITTED", "PUBLISHED"): return cur
    g = None
    try: g = json.load(open(os.path.join(run_dir, "gate.json"), encoding="utf-8"))
    except Exception: pass
    return record(book, n, "QUARANTINED", gate=g, run_dir=dst, detail=reason)
def title_of(text): return re.sub(r"^#+\s*", "", text.lstrip().split("\n", 1)[0]).strip()
def dest_name(n, text):
    t = re.sub(r"[\/:·]+", " ", title_of(text)); t = re.sub(r"\s+", "_", t.strip())
    return f"{n:04d}_{t}.md"
def commit(book, run_dir, n, extract=None, recheck=None, now_ts=None):
    """Returns manifest dict on success; raises TxnError (after rollback + quarantine) otherwise."""
    chap = os.path.join(run_dir, "chapter.md")
    # prepare
    if not os.path.exists(chap): raise TxnError("prepare: no chapter.md")
    text = open(chap, encoding="utf-8").read()
    try: g = json.load(open(os.path.join(run_dir, "gate.json"), encoding="utf-8"))
    except Exception as e: quarantine(book, run_dir, n, f"prepare: gate.json unreadable {e}"); raise TxnError("prepare: gate.json unreadable")
    # validate
    if g.get("verdict") != "PASS": quarantine(book, run_dir, n, f"validate: verdict {g.get('verdict')}"); raise TxnError(f"validate: verdict {g.get('verdict')}")
    if g.get("sha256") != gates.sha(text): quarantine(book, run_dir, n, "validate: chapter changed after gating"); raise TxnError("validate: sha mismatch")
    if recheck is None: recheck = lambda: gates.run_all(book, chap, n, use_llm=False, soft_max=10**6, retries=0)
    rc = recheck()
    if rc["verdict"] != "PASS": quarantine(book, run_dir, n, f"validate: deterministic recheck {gates.summary(rc)}"); raise TxnError("validate: deterministic recheck failed")
    # commit
    dst = os.path.join(book, "chapters", dest_name(n, text))
    if os.path.exists(dst) or (state.chapter(book, n) or {}).get("status") in ("COMMITTED", "PUBLISHED"): raise TxnError(f"commit: chapter {n} already exists")
    bak = state.path(book) + f".pre-{n:04d}.bak"; had_db = state.exists(book)
    if had_db: state.backup(book, bak)
    ex_err = None
    for k in range(2):
        try: ex = (extract or state.extract)(book, text); ex_err = None; break
        except Exception as e: ex_err = f"{type(e).__name__}: {e}"
    if ex_err: quarantine(book, run_dir, n, f"commit: state extraction ERROR {ex_err}"); raise TxnError("commit: extraction error")
    try:
        atomic_write(dst, text)
        state.commit_chapter(book, n, title_of(text), text, ex, os.path.basename(dst))
    except Exception as e:
        if os.path.exists(dst): os.remove(dst)
        if had_db and os.path.exists(bak): state.restore(book, bak)
        record(book, n, "COMMIT_FAILED", sha=gates.sha(text), gate=g, run_dir=run_dir, detail=f"{type(e).__name__}: {e}")
        quarantine(book, run_dir, n, f"commit rolled back: {type(e).__name__}: {e}")
        raise TxnError(f"commit rolled back: {e}")
    finally:
        if os.path.exists(bak): os.remove(bak)
    return record(book, n, "COMMITTED", sha=gates.sha(text), gate=g, file=os.path.basename(dst), run_dir=run_dir, detail=gates.summary(g))
def check_publishable(book, n, file):
    """-> ('publish'|'published'|'block', reason). Publisher must refuse anything but 'publish'/'published'."""
    m = load(book, n)
    if not m: return "block", "no manifest"
    text = open(file, encoding="utf-8").read(); same = m.get("sha256") == gates.sha(text)
    if m.get("status") == "PUBLISHED": return ("published", "ok") if same else ("block", "published revision differs from file (needs regate)")
    if m.get("status") != "COMMITTED": return "block", f"status {m.get('status')}"
    if (m.get("gate") or {}).get("verdict") != "PASS": return "block", f"gate verdict {(m.get('gate') or {}).get('verdict')}"
    if not same: return "block", "sha mismatch (chapter changed after approval)"
    return "publish", "ok"
def mark_published(book, n, file=None):
    """Audit A06: only a chapter that check_publishable() approves can be marked; SQLite errors raise TxnError (manifest untouched)."""
    m = load(book, n)
    if not m: raise TxnError("no manifest")
    file = file or (os.path.join(book, "chapters", m["file"]) if m.get("file") else None)
    if not file or not os.path.exists(file): raise TxnError(f"mark_published: chapter file missing ({m.get('file')})")
    st, why = check_publishable(book, n, file)
    if st not in ("publish", "published"): raise TxnError(f"mark_published: not publishable ({why})")
    try: state.mark_published(book, n)
    except Exception as e: raise TxnError(f"mark_published: state.db update failed: {type(e).__name__}: {e}")
    if m["status"] != "PUBLISHED": save(book, _hist(m, "PUBLISHED", "site"))
    return m
def notify(book, n, msg, runs=None):
    """Append a human-attention line to runs/needs-review.txt (attempt exhaustion, etc.)."""
    runs = runs or os.environ.get("ONOVEL_RUNS", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runs"))
    try:
        os.makedirs(runs, exist_ok=True)
        with open(os.path.join(runs, "needs-review.txt"), "a", encoding="utf-8") as f: f.write(f"[{gates.now()}] {os.path.basename(os.path.normpath(book))} ch{n}: {msg}\n")
    except OSError: pass
def approve_existing(book, n, file, g):
    """For a chapter already in chapters/ (legacy/review flow): record its gate evidence; PASS -> COMMITTED, else QUARANTINED."""
    text = open(file, encoding="utf-8").read()
    if g["verdict"] == "PASS" and g.get("sha256") == gates.sha(text):
        cur = load(book, n); st = "PUBLISHED" if cur and cur.get("status") == "PUBLISHED" and cur.get("sha256") == gates.sha(text) else "COMMITTED"
        return record(book, n, st, sha=gates.sha(text), gate=g, file=os.path.basename(file), detail="regate " + gates.summary(g))
    return record(book, n, "QUARANTINED", sha=gates.sha(text), gate=g, file=os.path.basename(file), detail="regate " + gates.summary(g))
def revise_commit(book, run_dir, n, file):
    """Replace an existing (usually published) chapter with a gated revision. Old text kept in .onovel/revisions/.
    Publishing happens again through publish-inkos.sh (manifest COMMITTED + PASS + sha)."""
    chap = os.path.join(run_dir, "chapter.md"); text = open(chap, encoding="utf-8").read()
    g = json.load(open(os.path.join(run_dir, "gate.json"), encoding="utf-8"))
    if g.get("verdict") != "PASS" or g.get("sha256") != gates.sha(text): raise TxnError("revise: gate not PASS or sha mismatch")
    rc = gates.run_all(book, chap, n, use_llm=False, soft_max=10**6, retries=0, canon=lambda b, c, k: state.canon_gate(b, c, k, check_number=False))
    if rc["verdict"] != "PASS": raise TxnError("revise: deterministic recheck failed")
    old = open(file, encoding="utf-8").read(); rv = os.path.join(book, ".onovel", "revisions"); os.makedirs(rv, exist_ok=True)
    bak = os.path.join(rv, f"{n:04d}-{time.strftime('%Y%m%dT%H%M%S')}.md"); atomic_write(bak, old)
    try:
        atomic_write(file, text); state.revise_chapter(book, n, text, os.path.basename(file))
    except Exception as e:
        atomic_write(file, old); raise TxnError(f"revise rolled back: {e}")
    m = load(book, n) or {"book": os.path.basename(os.path.normpath(book)), "n": n}
    m.setdefault("revisions", []).append({"ts": gates.now(), "run_dir": run_dir, "old_sha256": gates.sha(old), "backup": bak, "words": [gates.count_words(old), gates.count_words(text)]})
    m["sha256"] = gates.sha(text); m["gate"] = g; m["file"] = os.path.basename(file); save(book, _hist(m, "COMMITTED", f"REVISED {gates.summary(g)}"))
    return m
def revise_quarantine(book, run_dir, n, reason):
    """A failed revision never touches the live chapter/manifest status; it is only recorded + copied to quarantine."""
    qroot = os.path.join(os.path.dirname(os.path.normpath(run_dir)), "quarantine"); os.makedirs(qroot, exist_ok=True)
    dst = os.path.join(qroot, os.path.basename(os.path.normpath(run_dir)))
    if not os.path.exists(dst): shutil.copytree(run_dir, dst)
    m = load(book, n)
    if m: m.setdefault("revision_failures", []).append({"ts": gates.now(), "run_dir": dst, "reason": str(reason)[:300]}); save(book, m)
    return dst
