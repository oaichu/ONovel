#!/usr/bin/env bash
# loop-book.sh <book> [max_chapters]  background writer: novel.sh chapter by chapter; publish each COMMITTED chapter (manifest PASS).
# Counts only PUBLISHED chapters toward max (audit P1.7). rc 5 (gate ERROR / commit failure) = quarantined, retried with backoff.
# Never exits on transient errors (GLM/MiMo/network): backoff 60s..15min. Stop: touch /CODE/inkos/runs/STOP-<book>
B=${1:?book}; MAX=${2:-100000}; L=/CODE/inkos/runs/loop-$B.log; exec 9>/tmp/loop-$B.lock; flock -n 9 || { echo "already running"; exit 1; }
fail=0; done_n=0
while [ $done_n -lt $MAX ] && [ ! -f /CODE/inkos/runs/STOP-$B ]; do
  echo "[$(date '+%F %T')] start chapter (fail=$fail published=$done_n)" >> $L
  /CODE/inkos/novel.sh $B >> $L 2>&1; rc=$?
  echo "[$(date '+%F %T')] novel.sh rc=$rc" >> $L
  if [ $rc = 0 ]; then fail=0; blk=0
    if /CODE/oaichu-novels/scripts/publish-inkos.sh $B >> $L 2>&1; then done_n=$((done_n+1)); else echo "[$(date '+%F %T')] publish rc=$? (committed chapter stays queued; retried next round)" >> $L; fi
    sleep 5
  elif [ $rc = 4 ]; then blk=$((${blk:-0}+1)); echo "[$(date '+%F %T')] LLM blocked ($blk/3): free models exhausted" >> $L
    if [ $blk -ge 3 ]; then echo "[$(date '+%F %T')] loop-$B STOPPED: free LLM quota exhausted; restart loop-book.sh $B later" | tee -a $L >> /CODE/inkos/runs/llm-blocked.txt; break; fi
    sleep 1800
  else [ $rc = 5 ] && echo "[$(date '+%F %T')] chapter quarantined (gate ERROR or commit failure); see runs/quarantine/" >> $L
    fail=$((fail+1)); s=$(( fail*60 )); [ $s -gt 900 ] && s=900; sleep $s; fi
done
echo "[$(date '+%F %T')] loop exit (published=$done_n)" >> $L
