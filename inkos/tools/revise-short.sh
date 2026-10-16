#!/bin/bash
# Throttled worker: expand published chapters under min_words, book order tuc-the -> DKGH -> tien-tro -> pnntl.
# One chapter at a time (flock), nice'd, with a pause so new-chapter writing keeps its GLM slots. Republishes after each book.
I=/CODE/inkos; BK=/CODE/inkos-books/xemtruyen/books; LOG=$I/runs/revise-short.log; PAUSE=${REVISE_PAUSE:-120}
exec 9>/tmp/revise-short.lock; flock -n 9 || { echo "already running"; exit 0; }
exec >>"$LOG" 2>&1; log(){ echo "[$(date '+%F %T')] $*"; }
for ID in tuc-the dieu-khoan-gia-han tien-tro pham-nhan-nghich-thien-luc; do B=$BK/$ID
  [ -f "$B/.onovel/state.db" ] || { log "$ID not migrated yet, skipping"; continue; }
  $I/bin/onovel migrate "$B" --published-upto $(ls /CODE/oaichu-novels/src/content/chapters/$ID 2>/dev/null | wc -l) >/dev/null
  MIN=$($I/bin/onovel get "$B" layout.min_words); changed=0
  for f in $(ls "$B"/chapters/[0-9]*.md | sort); do N=$((10#$(basename "$f" | grep -oE '^[0-9]+')))
    w=$(python3 -c "import sys;sys.path.insert(0,'$I');from onovel.gates import count_words;print(count_words(open('$f').read()))")
    [ "$w" -ge "$MIN" ] && continue
    st=$(python3 -c "import sys,json;sys.path.insert(0,'$I');from onovel import txn;m=txn.load('$B',$N) or {};print(len(m.get('revision_failures',[])))")
    [ "$st" -ge 2 ] && { log "$ID ch$N: skipped (2 failed revisions)"; continue; }
    [ -f $I/runs/llm-blocked.txt ] && { log "llm-blocked.txt present, stopping"; exit 4; }
    log "$ID ch$N: $w < $MIN, revise-expand"
    r=$(nice -n 10 $I/bin/onovel revise-expand "$B" $N 2>>"$LOG"); log "$ID ch$N: $r"
    case "$r" in *REVISED*) changed=1;; *LLM_BLOCKED*) log "free models blocked, stop"; exit 4;; esac
    sleep $PAUSE
  done
  [ $changed = 1 ] && { log "$ID: republish"; /CODE/oaichu-novels/scripts/publish-inkos.sh "$ID"; }
done
log "done"; python3 $I/tools/audit-length.py > $I/runs/audit-length-after.json
