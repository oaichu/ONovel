"""onovel CLI: onovel <cmd> ... (see `onovel help`)."""
import os, sys, json, argparse, re
from . import manifest as mf, state, gates, txn, context, expand as ex, lessons, atomic_write, GENRE_KIT
def _book(b):
    if os.path.isdir(b): return os.path.abspath(b)
    p = os.path.join(os.environ.get("INKOS_PROJECT", "/CODE/inkos-books/xemtruyen"), "books", b)
    if os.path.isdir(p): return p
    sys.exit(f"onovel: book {b!r} not found")
def cmd_new(a):
    root = os.path.join(a.project or os.environ.get("INKOS_PROJECT", "/CODE/inkos-books/xemtruyen"), "books", a.book)
    if os.path.exists(root): sys.exit(f"onovel new: {root} exists")
    g = mf.genres().get(a.genre) or sys.exit(f"onovel new: unknown genre {a.genre}")
    tien = a.genre == "tien-hiep"
    m = dict(schema_version=1, id=a.book, title=a.title, genre_id=a.genre, skill_set=a.genre if a.genre in mf.genres().get("skill_sets", {}) else "tien-hiep",
             subgenre=a.subgenre or g.get("label", a.genre), audience=a.audience, language="vi", register=g.get("register", ""), style_profile="style-bible.md",
             narration="Ngôi thứ 3 giới hạn",
             xung_ho=dict(rules=(["tu sĩ không bao giờ xưng 'tôi'; dùng ta/ngươi/tại hạ/bản tọa/vãn bối", "chỉ phàm nhân mới có thể xưng 'tôi'"] if tien else ["xưng hô hiện đại tự nhiên theo quan hệ"]) + ["thoại trong ngoặc kép thẳng, không dấu gạch dài"],
                          **({"forbidden_for": {"tu sĩ": ["tôi"]}} if tien else {})),
             layout=dict(heading_style="colon", blocking=["heading", "length"], target_words=3000, min_words=1800, max_words=7500),
             soft_max=3, max_attempts=3, state_domains=(["realms", "secrets", "treasures", "promises", "foreshadowing"] if tien else ["relationships", "secrets", "promises", "foreshadowing"]))
    mf.validate(m)
    for d in ("chapters", "story/outline", "story/roles", ".onovel/chapters"): os.makedirs(os.path.join(root, d), exist_ok=True)
    import yaml
    atomic_write(os.path.join(root, "onovel.yaml"), yaml.safe_dump(m, allow_unicode=True, sort_keys=False))
    fm = dict(locked=True, genre=g.get("label", a.genre), register=g.get("register", ""), banned=g.get("banned", []), llm_only=g.get("llm_only", []),
              layout={"heading": "Chương N: Tên chương", "length_words": [2400, 4000]})
    atomic_write(os.path.join(root, "style-bible.md"), "---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False) + "---\n\n# Style bible: " + a.title +
                 "\n\n- Giọng kể: (điền)\n- Xưng hô: " + "; ".join(m["xung_ho"]["rules"]) + "\n- Thoại: ngoặc kép thẳng \"...\", cấm dấu gạch dài.\n")
    atomic_write(os.path.join(root, "story", "outline", "story_frame.md"), f"# {a.title}\n\n(Tiền đề, nhân vật chính, xung đột trung tâm.)\n\nCh 1–20: (mạch truyện quyển 1)\n")
    atomic_write(os.path.join(root, "book.json"), json.dumps({"id": a.book, "title": a.title, "genre": g.get("inkos_genre", "other"), "status": "outlining",
                 "chapterWordCount": 3000, "language": "vi"}, ensure_ascii=False, indent=2))
    atomic_write(os.path.join(root, "locked_facts.yaml"), "language: vi\nfacts: []\nchanges: []\n")
    state.migrate(root); mf.load(root); print(root)
def main(argv=None):
    ap = argparse.ArgumentParser(prog="onovel"); sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("new"); p.add_argument("book"); p.add_argument("--title", required=True); p.add_argument("--genre", default="tien-hiep")
    p.add_argument("--subgenre"); p.add_argument("--audience", default="chung", choices=["nam", "nu", "chung"]); p.add_argument("--project")
    p = sp.add_parser("validate"); p.add_argument("book")
    p = sp.add_parser("migrate"); p.add_argument("book"); p.add_argument("--published-upto", type=int, default=0); p.add_argument("--force", action="store_true")
    p = sp.add_parser("next"); p.add_argument("book")
    p = sp.add_parser("context"); p.add_argument("book"); p.add_argument("n", type=int); p.add_argument("--hint", default=""); p.add_argument("--tokens", type=int)
    p = sp.add_parser("gate"); p.add_argument("book"); p.add_argument("chapter"); p.add_argument("--n", type=int); p.add_argument("--no-llm", action="store_true")
    p.add_argument("--soft-max", type=int); p.add_argument("--out")
    p = sp.add_parser("fixlist"); p.add_argument("gate_json")
    p = sp.add_parser("commit"); p.add_argument("book"); p.add_argument("run_dir"); p.add_argument("n", type=int)
    p = sp.add_parser("quarantine"); p.add_argument("book"); p.add_argument("run_dir"); p.add_argument("n", type=int); p.add_argument("reason")
    p = sp.add_parser("check-publish"); p.add_argument("book"); p.add_argument("n", type=int); p.add_argument("file")
    p = sp.add_parser("mark-published"); p.add_argument("book"); p.add_argument("n", type=int)
    p = sp.add_parser("regate"); p.add_argument("book"); p.add_argument("n", type=int); p.add_argument("--no-llm", action="store_true"); p.add_argument("--out")
    p = sp.add_parser("expand"); p.add_argument("run_dir"); p.add_argument("--min", type=int, default=2400); p.add_argument("--target", type=int, default=3000)
    p = sp.add_parser("learn"); p.add_argument("book"); p.add_argument("gate_json"); p.add_argument("n", type=int)
    p = sp.add_parser("status"); p.add_argument("book")
    p = sp.add_parser("facts-add"); p.add_argument("book"); p.add_argument("id"); p.add_argument("entity"); p.add_argument("fact"); p.add_argument("--since", type=int, default=1)
    p.add_argument("--forbid", action="append", default=[])
    p = sp.add_parser("get"); p.add_argument("book"); p.add_argument("key")
    a = ap.parse_args(argv)
    if a.cmd == "new": return cmd_new(a)
    b = _book(a.book) if hasattr(a, "book") else None
    if a.cmd == "validate":
        try: m = mf.load(b); print(f"ok {m['id']} genre={m['genre_id']} skill_set={m.get('skill_set', m['genre_id'])}"); return 0
        except mf.ManifestError as e: print(f"INVALID: {e}", file=sys.stderr); return 2
    if a.cmd == "get":
        m = mf.load(b); v = m
        for k in a.key.split("."): v = v.get(k) if isinstance(v, dict) else None
        if v is None: v = mf.get(m, a.key, "")
        print(" ".join(map(str, v)) if isinstance(v, list) else v); return 0
    if a.cmd == "migrate":
        r = state.migrate(b, a.published_upto, a.force); state.render_views(b)
        for n in [c["n"] for c in state.chapters(b)]:
            row = state.chapter(b, n)
            if not txn.load(b, n):
                txn.record(b, n, "PUBLISHED" if row["status"] == "PUBLISHED" else "LEGACY", sha=row["sha256"], gate={"verdict": "LEGACY", "note": "pre-ONovel chapter; run onovel regate to approve"}, file=row["file"], detail="migrate")
        print(json.dumps(r, ensure_ascii=False)); return 0
    if a.cmd == "next": print(state.next_chapter(b)); return 0
    if a.cmd == "context": sys.stdout.write(context.build(b, a.n, a.tokens, a.hint)); return 0
    if a.cmd == "gate":
        try: m = mf.load(b); sm = a.soft_max if a.soft_max is not None else mf.get(m, "soft_max")
        except mf.ManifestError as e:
            g = gates.combine([gates.error("manifest", a.chapter, str(e))], 0); sm = None
        else: g = gates.run_all(b, a.chapter, a.n, use_llm=not a.no_llm, soft_max=sm)
        if a.out: atomic_write(a.out, json.dumps(g, ensure_ascii=False, indent=1))
        print(gates.summary(g)); return gates.EXIT[g["verdict"]]
    if a.cmd == "fixlist": print(gates.fix_list(json.load(open(a.gate_json, encoding="utf-8")))); return 0
    if a.cmd == "commit":
        try: m = txn.commit(b, a.run_dir, a.n); print(f"COMMITTED ch{a.n} -> {m['file']}"); return 0
        except txn.TxnError as e: print(f"TXN FAILED ch{a.n}: {e}", file=sys.stderr); return 2
    if a.cmd == "quarantine": txn.quarantine(b, a.run_dir, a.n, a.reason); print(f"QUARANTINED ch{a.n}: {a.reason}"); return 0
    if a.cmd == "check-publish":
        st, why = txn.check_publishable(b, a.n, a.file); print(f"{st} {why}"); return 0 if st != "block" else 1
    if a.cmd == "mark-published": txn.mark_published(b, a.n); return 0
    if a.cmd == "regate":
        fs = [f for f in state.chapter_files(b) if int(re.match(r"\d+", f).group(0)) == a.n] or sys.exit(f"no chapter {a.n}")
        f = os.path.join(b, "chapters", fs[0]); m = mf.load(b)
        g = gates.run_all(b, f, None, use_llm=not a.no_llm, soft_max=mf.get(m, "soft_max"), canon=lambda bk, ch, n: gates.verdict("canon", ch, open(ch, encoding="utf-8").read(), [], [], [], None, llm=False))
        if a.out: atomic_write(a.out, json.dumps(g, ensure_ascii=False, indent=1))
        r = txn.approve_existing(b, a.n, f, g); print(f"ch{a.n} {r['status']} {gates.summary(g)}"); return gates.EXIT[g["verdict"]]
    if a.cmd == "expand":
        w = ex.expand(a.run_dir, a.min, a.target, log=lambda s: print(s, file=sys.stderr)); print(w); return 4 if w == -4 else 0
    if a.cmd == "learn":
        m = mf.load(b); lessons.from_gate(b, m["genre_id"], a.n, json.load(open(a.gate_json, encoding="utf-8"))); return 0
    if a.cmd == "status":
        rows = state.chapters(b); st = {}
        for r in rows: st[r["status"]] = st.get(r["status"], 0) + 1
        q = [n for n in range(1, state.next_chapter(b) + 1) if (txn.load(b, n) or {}).get("status") == "QUARANTINED"]
        print(json.dumps({"book": os.path.basename(b), "next": state.next_chapter(b), "chapters": st, "quarantined": q}, ensure_ascii=False)); return 0
    if a.cmd == "facts-add": state.add_fact(b, a.id, a.entity, a.fact, since=a.since, forbid=a.forbid); return 0
if __name__ == "__main__": sys.exit(main() or 0)
