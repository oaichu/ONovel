#!/usr/bin/env python3
"""canon.py: READ-ONLY adapter over the canonical story-state engine (onovel/state.py). Since 2026-10-16 the only state writer
is the publish transaction (onovel/txn.py -> state.commit_chapter) after a chapter's gates PASS.
  canon.py context <book_dir> [--n 5]        planning context: current state + last N summaries + locked facts (from state.db)
  canon.py update  <book_dir> <chapter.md>   DEPRECATED: refuses; use `onovel commit <book> <run_dir> <n>`."""
import sys, os, json, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from onovel import state
def context(book, n=5):
    nx = state.next_chapter(book)
    summ = "\n".join(f"## Chương {r['n']}\n{r['summary']}" for r in state.summaries(book, last=n))
    return ("# Trạng thái hiện tại\n" + state.current_state(book) + "\n\n# Tóm tắt các chương gần nhất\n" + summ
            + "\n\n# Sự thật đã khóa\n" + "\n".join(f"- [{f['id']}] {f['fact']}" for f in state.active_facts(book, nx)))
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["context", "update"]); ap.add_argument("book"); ap.add_argument("chapter", nargs="?")
    ap.add_argument("--n", type=int, default=5); a = ap.parse_args()
    if a.cmd == "update": print("canon.py update is deprecated: state changes only via `onovel commit` (single writer)", file=sys.stderr); sys.exit(2)
    print(context(a.book, a.n))
