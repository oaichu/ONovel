"""Lessons from failures -> /CODE/lessons-library at three tiers: book (project tier, <book>/.lessons), genre (domain
'novel.<genre_id>'), global (domain-free, only generic failure classes so it stays small; the library dedupes)."""
import os, subprocess, sys
from . import LESSONS
def _lib(*a):
    p = os.path.join(LESSONS, "lessons.py")
    if not os.path.exists(p): return 1
    return subprocess.run([sys.executable, p, *a], capture_output=True, text=True, timeout=60).returncode
def learn(book, genre_id, text, global_text=None, tag="onovel"):
    _lib("learn", text, "--tier", "project", "--project", book, "--domain", "novel", "--tag", tag)
    if genre_id: _lib("learn", text, "--tier", "domain", "--domain", f"novel.{genre_id}", "--tag", tag)
    if global_text: _lib("learn", global_text, "--tier", "global", "--tag", tag)
def from_gate(book, genre_id, n, g):
    """Summarise a failed/errored combined gate into lessons."""
    rules = {}
    for r in g.get("gates", []):
        for v in r.get("blocking", []) + r.get("soft", []): rules[v["rule_id"]] = rules.get(v["rule_id"], 0) + 1
    top = ", ".join(f"{k}×{c}" for k, c in sorted(rules.items(), key=lambda x: -x[1])[:6])
    if g["verdict"] == "ERROR":
        learn(book, genre_id, f"Chương {n}: cổng ERROR ({'; '.join(g.get('errors', []))[:200]}) -> quarantine, thử lại sau.",
              global_text="Cổng kiểm tra lỗi API/JSON (ERROR) không bao giờ được coi là PASS; chương vào quarantine và thử lại.")
    elif rules:
        learn(book, genre_id, f"Chương {n} bị chặn bởi: {top}. Tránh các lỗi này ngay từ bản nháp.",
              global_text=None if not any(k in rules for k in ("em-dash", "quotes", "han-script")) else
              "Lỗi định dạng lặp lại (gạch dài, ngoặc cong, chữ Hán): nhắc rõ trong prompt nháp, không để tới cổng mới sửa.")
