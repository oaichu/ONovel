#!/usr/bin/env bash
# reaudit-publish.sh <inkos_book_dir> [from] [to]   (REWRITTEN 2026-10-15, audit-only)
# Re-runs stylegate + lockcheck over chapters [from..to] (default all) in parallel (4 at a time) and writes
# <book>/audit/<timestamp>/{sg,lc}-NNNN.json + summary.txt. It NEVER publishes: when clean, it prints the publish
# command for the user to approve and run (cd /CODE/oaichu-novels && npm run publish -- --book <id>).
set -uo pipefail
source ~/.profile >/dev/null 2>&1; eval "$(grep '^export ' /CODE/inkos/run-inkos.sh)"
B=${1:?book dir}; FROM=${2:-1}; TO=${3:-99999}; T=/CODE/inkos/tools; O="$B/audit/$(date +%Y%m%dT%H%M%S)"; mkdir -p "$O"
for f in "$B"/chapters/[0-9]*.md; do n=$((10#$(basename "$f" | grep -oE '^[0-9]+'))); [ $n -ge $FROM ] && [ $n -le $TO ] || continue
  nn=$(printf %04d $n); ( python3 $T/stylegate.py check "$B" "$f" > "$O/sg-$nn.json"; python3 $T/lockcheck.py check "$B" "$f" > "$O/lc-$nn.json" ) &
  while [ $(jobs -r | wc -l) -ge 4 ]; do sleep 2; done; done; wait
python3 - "$O" <<'PY' | tee "$O/summary.txt"
import json,glob,sys,os
bad=0
for p in sorted(glob.glob(sys.argv[1]+'/*.json')):
    try: r=json.load(open(p))
    except Exception: print(os.path.basename(p),'NOJSON'); bad+=1; continue
    n=[v for v in r.get('issues',r.get('violations',[])) if v.get('source')!='layout']
    if n or r.get('llm_error') or r.get('error'): bad+=1; print(os.path.basename(p),len(n),r.get('llm_error') or r.get('error') or '',[(v.get('fact_id') or v.get('word') or '')[:30] for v in n][:8])
print('CLEAN' if not bad else f'{bad} files with issues')
PY
grep -q '^CLEAN' "$O/summary.txt" && echo "Publish (needs user approval): cd /CODE/oaichu-novels && npm run publish -- --book $(basename "$B")"
