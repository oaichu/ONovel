#!/usr/bin/env bash
# supervisor.sh: inkos watchdog (no cron on the box). Every 2 min: if a book's newest log (loop log / run.log / import log) is
# older than 10 min while its process is alive -> kill that process tree (loop/import continue with the next attempt);
# restart loops/import that exited (unless STOP-<book>, or a free-LLM-blocked stop < 1h old). After a box pause/restore
# (wall clock jumped), waits 3 min grace so the new MiMo/glm timeouts can recover on their own first.
# Start: setsid nohup /CODE/inkos/supervisor.sh >/dev/null 2>&1 &   Log: /CODE/inkos/runs/supervisor.log  Stop: touch runs/STOP-supervisor
exec 8>/tmp/inkos-supervisor.lock; flock -n 8 || exit 0
I=/CODE/inkos; R=$I/runs; L=$R/supervisor.log; BOOKS="tuc-the dieu-khoan-gia-han tien-tro"; STALE=${SUP_STALE:-600}
log(){ echo "[$(date '+%F %T')] $*" >> $L; }
tree(){ local p; for p in $(pgrep -P $1); do tree $p; done; echo $1; }
killtree(){ local ps=$(tree $1); kill -TERM $ps 2>/dev/null; sleep 5; kill -KILL $ps 2>/dev/null; }
age(){ local m=0 f t; for f in "$@"; do [ -e "$f" ] && { t=$(stat -c %Y "$f"); [ $t -gt $m ] && m=$t; }; done; echo $(( $(date +%s) - m )); }
log "supervisor start pid $$"; prev=$(date +%s)
while [ ! -f $R/STOP-supervisor ]; do
  sleep 120; now=$(date +%s)
  if [ $((now-prev)) -gt 300 ]; then log "clock jumped $(( (now-prev)/60 ))min (box paused/restored); grace 180s"; sleep 180; now=$(date +%s); fi; prev=$now
  imp=$(pgrep -f 'tools/import-tien-tro.sh' | head -1)
  if [ -n "$imp" ]; then a=$(age $R/tien-tro-import.log)
    if [ $a -gt $STALE ]; then c=$(pgrep -f 'inkos import chapters' | head -1); log "import log stale ${a}s -> kill inkos import ${c:-none} (import script retries/skips)"; [ -n "$c" ] && killtree $c; fi
  elif ! grep -q 'removed STOP-tien-tro' $R/tien-tro-import.log 2>/dev/null; then
    n=$(( $(ls $I/../inkos-books/xemtruyen/books/tien-tro/chapters/[0-9]*.md 2>/dev/null | wc -l) + 1 ))
    [ $n -le 40 ] && { log "import not running, restarting from ch$n"; (cd $I && setsid nohup tools/import-tien-tro.sh $n >/dev/null 2>&1 < /dev/null &); }
  fi
  for b in $BOOKS; do
    lp=$(pgrep -f "loop-book.sh $b\$" | head -1)
    if [ -z "$lp" ]; then
      [ -f $R/STOP-$b ] && continue
      tail -n 1 $R/loop-$b.log 2>/dev/null | grep -q 'quota exhausted' && [ $(age $R/loop-$b.log) -lt 3600 ] && continue
      log "loop $b not running -> start"; (cd $I && setsid nohup ./loop-book.sh $b >/dev/null 2>&1 < /dev/null &); continue
    fi
    np=$(pgrep -f "novel.sh $b\$" | head -1); [ -z "$np" ] && continue
    rd=$(ls -td $R/$b-[0-9]*/ 2>/dev/null | head -1); a=$(age $R/loop-$b.log ${rd}run.log ${rd})
    if [ $a -gt $STALE ]; then log "$b stale ${a}s (run $(basename "$rd")) -> kill novel.sh tree $np"; killtree $np; fi
  done
done; log "supervisor stop"
