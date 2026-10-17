#!/bin/bash
# Resumable: ensure tien-tro ch18-40 are ingested (site text + MiMo state), then remove STOP-tien-tro and start loop-book.sh tien-tro (ch41+).
# Safe to re-run any time (flock; ingest is idempotent per chapter). Log: runs/finish-tien-tro.log
I=/CODE/inkos; B=/CODE/inkos-books/xemtruyen/books/tien-tro; SRC=/workspace/tien-tro-import-src; R=$I/runs; L=$R/finish-tien-tro.log
exec 9>/tmp/finish-tien-tro.lock; flock -n 9 || exit 0; exec >>"$L" 2>&1; log(){ echo "[$(date '+%F %T')] $*"; }; cd $I
while pgrep -f "tools/ingest-site.py $B" >/dev/null; do sleep 30; done   # let a running ingest finish
for pass in 1 2 3; do
  todo=$(python3 -c "
import sys,os,re;sys.path.insert(0,'$I');from onovel import state
fs={int(re.match(r'\d+',f).group(0)) for f in state.chapter_files('$B')}
rows={r['n']:r for r in state.chapters('$B')}
print(' '.join(str(n) for n in range(18,41) if n not in fs or n not in rows or rows[n]['status']!='PUBLISHED' or len(rows[n]['summary'] or '')<200 or 'MiMo lỗi' in (rows[n]['summary'] or '')))")
  [ -z "$todo" ] && break; log "pass $pass: ingest $todo"
  for n in $todo; do python3 tools/ingest-site.py $B $SRC $n $n; done
done
[ -n "$todo" ] && log "still incomplete after 3 passes: $todo (ingested with stub summaries; continuing)"
$I/bin/onovel migrate $B --published-upto 40 >/dev/null; python3 -c "import sys;sys.path.insert(0,'$I');from onovel import state;state.render_views('$B')"
log "status: $($I/bin/onovel status $B)"
rm -f $R/STOP-tien-tro; log "removed STOP-tien-tro"
grep -q 'removed STOP-tien-tro' $R/tien-tro-import.log || echo "[$(date '+%F %T')] removed STOP-tien-tro (finish-tien-tro.sh)" >> $R/tien-tro-import.log
pgrep -f "loop-book.sh tien-tro$" >/dev/null || { NOVEL_LLM=mimo setsid nohup ./loop-book.sh tien-tro >/dev/null 2>&1 < /dev/null & log "started loop-book.sh tien-tro"; }
