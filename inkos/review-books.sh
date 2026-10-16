#!/usr/bin/env bash
# review-books.sh : one book at a time (BOOKS, default tien-tro dieu-khoan-gia-han pham-nhan-nghich-thien-luc):
# wait for its inkos import to finish, then `onovel regate` every chapter (full gates incl. MiMo judge; records the per-chapter
# manifest: PASS -> COMMITTED, FAIL/ERROR -> QUARANTINED), one MiMo fix.py round on FAIL, re-gate, then publish-inkos.sh
# WITHOUT --force/--continue: the publisher itself only ships chapters whose manifest shows PASS (ONovel audit P0.4).
# Log: runs/review-books.log, status runs/review-<book>.tsv
set -uo pipefail; set +u; . ~/.profile >/dev/null 2>&1; eval "$(grep '^export ' /CODE/inkos/run-inkos.sh)"; set -u
T=/CODE/inkos/tools; ON=/CODE/inkos/bin/onovel; P=/CODE/inkos-books/xemtruyen; L=/CODE/inkos/runs/review-books.log; log(){ echo "[$(date '+%F %T')] $*" >> $L; }
for b in ${BOOKS:-tien-tro dieu-khoan-gia-han pham-nhan-nghich-thien-luc}; do
  while pgrep -f "inkos import chapters $b" >/dev/null; do sleep 120; done
  B=$P/books/$b; S=/CODE/inkos/runs/review-$b.tsv; : > $S
  $ON validate $B >> $L 2>&1 || { log "$b: manifest invalid, skipped"; continue; }
  [ -f $B/.onovel/state.db ] || $ON migrate $B >> $L 2>&1
  for f in $(ls $B/chapters/[0-9]*.md 2>/dev/null | sort); do
    n=$((10#$(basename $f | grep -oE '^[0-9]+'))); W=$(mktemp -d)
    $ON regate $B $n --out $W/gate.json >> $L 2>&1; rc=$?
    if [ $rc = 1 ]; then $ON fixlist $W/gate.json > $W/fix.txt
      [ -s $W/fix.txt ] && python3 $T/fix.py "$f" $W/fix.txt >> $L 2>&1
      $ON regate $B $n --out $W/gate.json >> $L 2>&1; rc=$?; fi
    st=$(case $rc in 0) echo PASS;; 1) echo FAIL;; *) echo ERROR;; esac)
    echo -e "$(basename $f)\t$st" >> $S; log "$b $(basename $f): $st"; rm -rf $W
  done
  /CODE/oaichu-novels/scripts/publish-inkos.sh $b >> $L 2>&1; log "$b publish rc=$?"
done
log "review-books done"
