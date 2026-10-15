#!/usr/bin/env bash
# loop-book.sh <book> [max_chapters]  background writer: novel.sh chapter by chapter, publish each passed chapter.
# Never exits on transient errors (Gemini/MiMo/network): backoff 60s..15min. Stop: touch /CODE/inkos/runs/STOP-<book>
B=${1:?book}; MAX=${2:-100000}; L=/CODE/inkos/runs/loop-$B.log; exec 9>/tmp/loop-$B.lock; flock -n 9 || { echo "already running"; exit 1; }
fail=0; done_n=0
while [ $done_n -lt $MAX ] && [ ! -f /CODE/inkos/runs/STOP-$B ]; do
  echo "[$(date '+%F %T')] start chapter (fail=$fail)" >> $L
  /CODE/inkos/novel.sh $B >> $L 2>&1; rc=$?
  echo "[$(date '+%F %T')] novel.sh rc=$rc" >> $L
  if [ $rc = 0 ]; then fail=0; done_n=$((done_n+1))
    /CODE/oaichu-novels/scripts/publish-inkos.sh $B --check >> $L 2>&1 || echo "[$(date '+%F %T')] publish rc=$? (will retry next round)" >> $L
    sleep 5
  else fail=$((fail+1)); s=$(( fail*60 )); [ $s -gt 900 ] && s=900; sleep $s; fi
done
echo "[$(date '+%F %T')] loop exit (done=$done_n)" >> $L
