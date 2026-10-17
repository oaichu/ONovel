#!/usr/bin/env python3
"""ingest-site.py <book-dir> <src-dir> <from> <to>   fast scripted import of already-published site chapters into the book.
Copies src/NNNN.md verbatim (published text, no rewrite) to chapters/NNNN_<title>.md (existing partial imports backed up),
then MiMo (state.extract, sequential so continuity accumulates) extracts summary/state/entities into .onovel/state.db and
the chapter is ledgered PUBLISHED. On MiMo failure (content_filter etc.) the chapter is ledgered with a stub summary."""
import os, re, sys, shutil, time, json, signal
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from onovel import state, atomic_write
book, src, a, b = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
ch = os.path.join(book, "chapters"); bak = os.path.join(book, ".onovel", "ingest-backup-" + time.strftime("%Y%m%dT%H%M%S")); os.makedirs(bak, exist_ok=True)
log = lambda s: print(f"[{time.strftime('%H:%M:%S')}] {s}", flush=True)
for n in range(a, b + 1):
    text = open(os.path.join(src, f"{n:04d}.md"), encoding="utf-8").read().strip() + "\n"
    title = re.sub(r"^#+\s*", "", text.split("\n", 1)[0]).strip()
    for f in os.listdir(ch):
        if re.match(rf"^{n:04d}_.*\.md$", f): shutil.move(os.path.join(ch, f), os.path.join(bak, f))
    fn = f"{n:04d}_" + re.sub(r"[^\w,]+", "_", re.sub(r"^Chương\s+\d+\s*[:.]\s*", "", title)).strip("_") + ".md"
    atomic_write(os.path.join(ch, fn), text)
    t0 = time.time()
    def _alarm(*a): raise TimeoutError("ingest watchdog 420s")
    signal.signal(signal.SIGALRM, _alarm); ex = None
    for k in range(2):
        signal.alarm(420)
        try: ex = state.extract(book, text); signal.alarm(0); break
        except Exception as e: signal.alarm(0); err = e; log(f"ch{n}: extract try {k+1} failed {type(e).__name__}: {str(e)[:120]}")
    try:
        if ex is None: raise err
    except Exception as e: ex = {"summary": f"(Chương {n} nhập từ site; trích xuất MiMo lỗi: {type(e).__name__})"}; log(f"ch{n}: extract failed {type(e).__name__}: {str(e)[:120]}")
    state.commit_chapter(book, n, title, text, ex, fn, actor="ingest-site", replace=True); state.mark_published(book, n, actor="ingest-site")
    log(f"ch{n}: ingested {len(text.split())} words, summary {len(str(ex.get('summary','')))} chars, {time.time()-t0:.0f}s")
state.render_views(book); log("done; views rendered")
