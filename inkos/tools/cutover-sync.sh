#!/usr/bin/env bash
# cutover-sync.sh <working_dir> <inkos_book_dir> [--dry-run]   (REWRITTEN 2026-10-15)
# Copies working-folder chapters (chuong-NNN.md) into the inkos book as chapters/NNNN_<slug-title>.md, replacing any older
# file of the same number. Keeps a pristine copy in <project>/.import-src/<book-id>/ (used by mimo-fix and import).
set -euo pipefail
W=${1:?working dir}; B=${2:?book dir}; DRY=${3:-}
P=$(dirname "$(dirname "$B")"); ID=$(basename "$B"); mkdir -p "$B/chapters" "$P/.import-src/$ID"
for f in "$W"/chuong-[0-9]*.md; do
  n=$(basename "$f" | grep -oE '[0-9]+' | head -1); n=$((10#$n)); nn=$(printf %04d $n)
  t=$(head -1 "$f" | sed -E 's/^#+ *//; s/[\/:·]+/ /g; s/ +/_/g')
  dst="$B/chapters/${nn}_${t}.md"
  if [ -n "$DRY" ]; then echo "would sync $f -> $dst"; continue; fi
  for o in "$B/chapters/${nn}"_*.md; do [ -e "$o" ] && [ "$o" != "$dst" ] && rm -f "$o"; done
  cmp -s "$f" "$dst" 2>/dev/null || { cp -p "$f" "$dst"; echo "synced $nn"; }
  cp -p "$f" "$P/.import-src/$ID/$(basename "$f")"
done
