"""ONovel core: manifest, gates/verdicts, canonical story state, context retrieval, publish transaction.
Paths: ONOVEL_HOME (default: parent of this package = inkos dir), ONOVEL_LESSONS (default /CODE/lessons-library)."""
import os
HOME = os.environ.get("ONOVEL_HOME") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(HOME, "tools")
GENRE_KIT = os.path.join(HOME, "genre-kit")
LESSONS = os.environ.get("ONOVEL_LESSONS") or ("/CODE/lessons-library" if os.path.isdir("/CODE/lessons-library") else os.path.join(os.path.dirname(HOME), "lessons-library"))
def atomic_write(path, text, mode="w"):
    d = os.path.dirname(os.path.abspath(path)); os.makedirs(d, exist_ok=True)
    tmp = os.path.join(d, f".{os.path.basename(path)}.{os.getpid()}.tmp")
    with open(tmp, mode, **({} if "b" in mode else {"encoding": "utf-8"})) as f: f.write(text)
    os.replace(tmp, path)
