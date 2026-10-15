#!/usr/bin/env bash
# review-books.sh : one book at a time (tien-tro, dieu-khoan-gia-han, pham-nhan-nghich-thien-luc):
# wait for its inkos import to finish, then stylegate+lockcheck (MiMo) each chapter, one MiMo fix.py round on failures,
# re-gate, then publish passed chapters (publish-inkos.sh --force --continue). Log: runs/review-books.log, status runs/review-<book>.tsv
set -uo pipefail; set +u; . ~/.profile >/dev/null 2>&1; eval "$(grep '^export ' /CODE/inkos/run-inkos.sh)"; set -u
T=/CODE/inkos/tools; P=/CODE/inkos-books/xemtruyen; L=/CODE/inkos/runs/review-books.log; log(){ echo "[$(date '+%F %T')] $*" >> $L; }
for b in ${BOOKS:-tien-tro dieu-khoan-gia-han pham-nhan-nghich-thien-luc}; do
  while pgrep -f "inkos import chapters $b" >/dev/null; do sleep 120; done
  B=$P/books/$b; S=/CODE/inkos/runs/review-$b.tsv; : > $S
  n_src=$(ls $P/.import-src/$b 2>/dev/null | wc -l); n=$(ls $B/chapters/[0-9]*.md 2>/dev/null | wc -l); log "$b import done/not running: $n chapters in book ($n_src in import src)"
  for f in $(ls $B/chapters/[0-9]*.md 2>/dev/null | sort); do
    W=$(mktemp -d); ok=0
    for i in 1 2 3; do  # retry transient API errors
      python3 $T/stylegate.py check "$B" "$f" > $W/style.json 2>$W/err; a=$?; python3 $T/lockcheck.py check "$B" "$f" > $W/lock.json 2>>$W/err; c=$?
      grep -q '"llm_error": *null\|"llm_error": *""' $W/style.json 2>/dev/null || ! grep -q llm_error $W/style.json && break; sleep 30; done
    st=pass
    if [ $((a|c)) != 0 ]; then
      python3 - $W > $W/fix.txt <<'PY'
import json,sys
w=sys.argv[1]; o=[]
for f,k in (('style.json','issues'),('lock.json','violations')):
    try: d=json.load(open(f'{w}/{f}'))
    except Exception: continue
    for v in d.get(k,[]):
        if v.get('source')=='layout': continue
        o.append(f"- [{v.get('fact_id') or v.get('source')}] {v.get('word','')} {v.get('reason','')} | trích: {(v.get('quote') or '')[:200]}")
print("\n".join(o))
PY
      if [ -s $W/fix.txt ]; then cp "$f" $W/orig.md; python3 $T/fix.py "$f" $W/fix.txt >> $L 2>&1
        python3 $T/stylegate.py check "$B" "$f" > $W/style.json; a=$?; python3 $T/lockcheck.py check "$B" "$f" > $W/lock.json; c=$?
        [ $((a|c)) = 0 ] && st=fixed || st="fail($(wc -l < $W/fix.txt) issues before fix)"; touch "$f"
      else st=pass-layout-only; fi
    fi
    echo -e "$(basename $f)\t$st" >> $S; log "$b $(basename $f): $st"; rm -rf $W
  done
  /CODE/oaichu-novels/scripts/publish-inkos.sh $b --force --continue >> $L 2>&1; log "$b published rc=$?"
done
log "review-books done"
