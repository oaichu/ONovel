---
name: lessons-library
description: >-
  Shared lessons store for all agents (Grok Bot, Pi, inkos novel pipeline). Use before starting a task to load the
  relevant lessons, and after a user correction or a gate failure to record a new lesson. Three tiers: global, domain, project.
---
# Lessons library

Store: `/CODE/lessons-library` (real path `/workspace/CODE/lessons-library`, rebuilt 2026-10-15). CLI: `python3 /CODE/lessons-library/lessons.py`.

## Tiers
- **global**: rules for every task (language, time zone, no secrets). `global/lessons.jsonl`.
- **domain**: rules for one field. Domains: `novel` (symlink to `/CODE/inkos/genre-kit/lessons`, shared with novel.sh), `grok-bot`, `pi`.
- **project**: rules for one book or repo, stored in `<project>/.lessons/lessons.jsonl` (for a book: the inkos book dir).

## Commands
- `prompt --domain novel --project <book_dir>`: print active lessons as a prompt block. Put it into every writing/review prompt.
- `learn "<rule>" --tier domain --domain novel [--candidate]`: add a lesson (one line, Vietnamese, imperative). Duplicates are skipped. Secrets are refused.
- `curate [--inbox]`: dedupe all tiers; `--inbox` ingests `~/.pi/agent/lessons-inbox.jsonl` as `candidate` lessons in the `pi` domain.
- `promote <id> --to domain|global`: move a lesson up when it proves general (e.g. a book rule that applies to all xianxia).
- `ensure`: recreate layout and symlinks after a restart.
- `list [--all]`: show lessons with ids.

## Rules
1. Record only durable rules, not one-off requests. Merge with an existing lesson instead of adding a near-duplicate.
2. Project first, promote later: a rule learned on one book starts at project tier unless the user said it applies everywhere.
3. Never store keys, tokens, passwords or cookies.
4. Candidates are not used by `prompt` until promoted or re-learned as active.
See `references/format.md` for the record format.
