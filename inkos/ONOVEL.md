# ONovel core (inkos/onovel)

Single core for all ONovel books. CLI: `inkos/bin/onovel` (python package `inkos/onovel`).

| Step | Module | What |
|---|---|---|
| Book manifest | `manifest.py` | `<book>/onovel.yaml` (genre_id, subgenre, audience, register, style_profile, xung_ho, layout, soft_max, max_attempts, state_domains), JSON-schema validated whenever a book is opened; `tools/skills.py` reads it (no name guessing). |
| Gates | `gates.py`, `judge.py`, `tools/stylegate.py`, `tools/lockcheck.py`, `state.canon_gate` | Every gate returns `{verdict: PASS/FAIL/ERROR, blocking[], soft[], warnings[], error, sha256}`; exit 0/1/2. Rule-based issues block; layout blocks per manifest; MiMo judge returns structured items (rule_id, verdict, severity, confidence, evidence_span) accepted structurally, soft up to soft_max; any judge/API/JSON error = ERROR (never PASS). |
| State engine | `state.py` | One writer: SQLite `<book>/.onovel/state.db` (chapters ledger, locked facts with provenance, characters + realm history, treasures, factions, secrets + knowers, promises, foreshadowing with visibility window, snapshots, proposals, audit). Markdown/YAML files are generated views. `canon.py` and novel-continuity only read or propose. |
| Transaction | `txn.py` | prepare -> validate (gate PASS + sha + deterministic recheck) -> commit (chapter file + state, rollback on failure) -> manifest `<book>/.onovel/chapters/NNNN.json`; ERROR/commit failure -> `runs/quarantine/`. `publish-inkos.sh` publishes only PASS manifests and marks them PUBLISHED. |
| Context | `context.py` | Token-budgeted retrieval: outline blocks by chapter range + overlap, no future arcs, relevant facts/characters/plot debts, previous ending at paragraph boundaries. |
| Length | `expand.py`, `tools/draftcheck.py` | Short drafts get an 'expand missing scenes' pass on free models, then MiMo polish; degenerate drafts rejected. |
| Lessons | `lessons.py` | Gate failures -> lessons-library per book (project), per genre (`novel.<genre_id>`), global (generic classes only). |

New book: `onovel new <id> --title "..." --genre tien-hiep|ngon-tinh-hien-dai|... [--audience nam|nu|chung]`.
Legacy book: `onovel migrate <book> --published-upto N`. Tests: `python -m pytest inkos/tests && bash inkos/tests/smoke.sh` (mocked LLM).
LLM policy: plan/draft free models only (openrouter/free first, then `:free` list; never paid); chapter text only changed by MiMo/scripts.
