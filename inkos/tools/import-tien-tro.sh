#!/usr/bin/env bash
# one-off 2026-10-16: import site ch17-40 into inkos tien-tro (MiMo via run-inkos.sh) with a watchdog:
# kill when a chapter streams 0 chars for >=120s (or no log progress for 600s); a chapter that fails twice (any reason) is skipped.
# Afterwards: remove STOP-tien-tro and start loop-book.sh tien-tro (continues with ch41).
L=/CODE/inkos/runs/tien-tro-import.log; S=/workspace/tien-tro-import-src; start=${1:-17}; declare -A nf; streak=0
log(){ echo "[$(date '+%F %T')] $*" >> $L; }
cd /CODE/inkos-books/xemtruyen
while [ $start -le 40 ]; do
  log "import --resume-from $start"; T=$(mktemp)
  setsid /CODE/inkos/run-inkos.sh import chapters tien-tro --from $S --resume-from $start > $T 2>&1 & pid=$!; off=0; why=; lastsz=0; lastt=$(date +%s)
  while kill -0 $pid 2>/dev/null; do sleep 10
    sz=$(stat -c %s $T); [ $sz -gt $off ] && { tail -c +$((off+1)) $T >> $L; off=$sz; }
    [ $sz != $lastsz ] && { lastsz=$sz; lastt=$(date +%s); }
    z=$(tail -n 1 $T | grep -oE 'streaming [0-9]+s, 0 chars' | grep -oE '[0-9]+'); [ -n "$z" ] && [ $z -ge 120 ] && why="0 chars after ${z}s"
    [ $(( $(date +%s)-lastt )) -ge 600 ] && why="no output 600s"
    [ -n "$why" ] && { kill -TERM -- -$pid 2>/dev/null; sleep 3; kill -KILL -- -$pid 2>/dev/null; log "watchdog: killed import ($why)"; break; }
  done; wait $pid; rc=$?; sz=$(stat -c %s $T); [ $sz -gt $off ] && tail -c +$((off+1)) $T >> $L
  [ -z "$why" ] && [ $rc = 0 ] && ! grep -q 'Chapter import failed' $T && { log "import rc=0"; break; }
  n=$(grep -oE 'Analyzing chapter [0-9]+' $T | tail -1 | grep -oE '[0-9]+$'); n=${n:-$start}
  grep -qi content_filter $T && why="content_filter $why"; why=${why:-"error rc=$rc"}
  nf[$n]=$(( ${nf[$n]:-0}+1 )); log "ch$n failed (${nf[$n]}/2): $why"; rm -f $T
  if [ ${nf[$n]} -ge 2 ]; then log "SKIP ch$n (failed twice)"; start=$((n+1)); else start=$n; fi
  [ "$n" = "$prev" ] && streak=$((streak+1)) || streak=0; prev=$n; sleep 20
done
log "done: $(ls /CODE/inkos-books/xemtruyen/books/tien-tro/chapters/[0-9]*.md | wc -l) chapter files"
rm -f /CODE/inkos/runs/STOP-tien-tro; log "removed STOP-tien-tro, starting loop-book.sh tien-tro"
cd /CODE/inkos && setsid nohup ./loop-book.sh tien-tro >/dev/null 2>&1 < /dev/null &
