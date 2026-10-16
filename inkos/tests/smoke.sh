#!/usr/bin/env bash
# smoke.sh: end-to-end shell smoke test with a mocked LLM (no network, no keys):
# onovel new -> novel.sh --stub (ch1, ch2) -> gates -> commit transaction -> publish check -> mark published -> state/next.
set -euo pipefail
H="${ONOVEL_HOME:-$(cd "$(dirname "$0")/.." && pwd)}"; export ONOVEL_HOME="$H"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
export INKOS_PROJECT=$TMP/proj ONOVEL_RUNS=$TMP/runs ONOVEL_MOCK_LLM=1 ONOVEL_LESSONS=$TMP/lessons ONOVEL_SITE_CHAPTERS=$TMP/site NOVEL_LLM=glm
mkdir -p $ONOVEL_RUNS $TMP/site; ON="$H/bin/onovel"; NS=${NOVEL_SH:-$H/novel.sh}
$ON new smoke --title "Sách Khói" --genre tien-hiep --project $INKOS_PROJECT >/dev/null
B=$INKOS_PROJECT/books/smoke
python3 - > $TMP/seed.md <<'PY'
import random
r = random.Random(1); P = "gió núi sương mù bậc đá kiếm khí đan lô linh thạch sư huynh trưởng lão ngọn đèn suối lạnh ánh trăng tiếng chuông lá trúc phù lục trận pháp cổ thụ".split()
print("# Chương 0: seed\n"); [print(f'Lâm Phong {" ".join(r.choice(P) for _ in range(12))} lần {i}. "Ta đi {i}," hắn nói.\n') for i in range(230)]
PY
export ONOVEL_STUB_TEXT=$TMP/seed.md
fail(){ echo "SMOKE FAIL: $*" >&2; exit 1; }
for n in 1 2; do
  bash $NS --stub smoke > $TMP/out$n.txt 2> $TMP/err$n.txt || { cat $TMP/err$n.txt >&2; fail "novel.sh ch$n rc=$?"; }
  grep -q "verdict: PASS" $TMP/out$n.txt || fail "ch$n verdict"
  f=$(ls $B/chapters/$(printf %04d $n)_*.md) || fail "ch$n not committed"
  $ON check-publish $B $n "$f" | grep -q '^publish ok' || fail "ch$n not publishable"
  $ON mark-published $B $n; $ON check-publish $B $n "$f" | grep -q '^published' || fail "ch$n not marked"
done
[ "$($ON next $B)" = 3 ] || fail "next != 3"
$ON status $B | grep -q '"PUBLISHED": 2' || fail "status"
grep -q "Trạng thái giả lập" $B/story/current_state.md || fail "state view not rendered"
# failure injection: judge/API error must quarantine, never commit
ONOVEL_MOCK_LLM=error $ON gate $B $f --n 3 --out $TMP/g.json >/dev/null && fail "ERROR gate returned 0" || true
python3 -c "import json,sys;sys.exit(0 if json.load(open('$TMP/g.json'))['verdict']=='ERROR' else 1)" || fail "gate verdict not ERROR"
# manifest validation blocks a broken book
sed -i 's/^genre_id: .*/genre_id: khong-ton-tai/' $B/onovel.yaml; bash $NS --stub smoke >/dev/null 2>&1 && fail "invalid manifest accepted" || true
echo "SMOKE OK"
