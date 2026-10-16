#!/usr/bin/env bash
# novel.sh [--dry-run] [--stub] <book> [chapter hint...]   ONovel pipeline for the next chapter of a book in $INKOS_PROJECT/books/<id>.
# (rewritten 2026-10-16 per ONovel audit; previous version in /workspace/inkos-bak-20261016/)
#   0 open book: validate onovel.yaml (schema), migrate legacy state into .onovel/state.db if needed, chapter id from the state engine
#   1 plan / 2 draft: FREE models only (Gemini sub when its auth works, else OpenRouter via tools/glm.py: openrouter/free first,
#     then the :free list; never paid). Context = semantic retrieval within a token budget (onovel context).
#     Degenerate drafts (>2.5x target, repetition) are rejected; short drafts get an 'expand missing scenes' pass (onovel expand).
#   3 polish: MiMo (tools/polish.py)
#   gates (onovel gate): style, locked facts, layout (blocking per manifest), canon; verdict PASS/FAIL/ERROR in gate.json.
#     FAIL -> up to 3 MiMo minimal-fix rounds (tools/fix.py); ERROR -> quarantine (never published), exit 5.
#   commit (onovel commit): transaction chapter file + canonical state, rollback on failure; per-chapter manifest .onovel/chapters/NNNN.json.
#   Publishing is done by the caller (loop-book.sh -> publish-inkos.sh), which publishes only manifests with verdict PASS.
# Exit: 0 committed, 1 gates FAIL, 2 setup error, 3 LLM failure, 4 free LLMs blocked, 5 ERROR/quarantine or commit failure.
set -uo pipefail
source ~/.profile >/dev/null 2>&1; I=${ONOVEL_HOME:-/CODE/inkos}; eval "$(grep '^export ' $I/run-inkos.sh 2>/dev/null)"
T=$I/tools; ON="$I/bin/onovel"; P=${INKOS_PROJECT:-/CODE/inkos-books/xemtruyen}; GM=${NOVEL_GEMINI_MODEL:-gemini-3-8-flash}; LLM=${NOVEL_LLM:-mimo}; export NOVEL_LLM=$LLM
DRY=0; STUB=0; while [[ ${1:-} == --* ]]; do case $1 in --dry-run) DRY=1;; --stub) STUB=1;; esac; shift; done
Q=${1:?usage: novel.sh [--dry-run] [--stub] <book> [hint]}; shift; HINT="$*"
case $Q in tien|tt) Q=tien-tro;; dkgh) Q=dieu-khoan-gia-han;; pnntl) Q=pham-nhan-nghich-thien-luc;; tuc) Q=tuc-the;; esac
B="$P/books/$Q"; [ -d "$B" ] || { echo "ERROR: book '$Q' not found in $P/books" >&2; exit 2; }
ID=$(basename "$B"); RUNS=${ONOVEL_RUNS:-$I/runs}
$ON validate "$B" >&2 || { echo "ERROR: $B/onovel.yaml invalid (see above)" >&2; exit 2; }
BIB="$B/$($ON get "$B" style_profile)"; [ -f "$BIB" ] || { echo "ERROR: $BIB missing (style lock required)" >&2; exit 2; }
SITE=${ONOVEL_SITE_CHAPTERS:-/CODE/oaichu-novels/src/content/chapters}/$ID
$ON migrate "$B" --published-upto $(ls "$SITE" 2>/dev/null | wc -l) >/dev/null || exit 2   # first run: migrate; later: sync new chapter files into the ledger
if false; then SITE=${ONOVEL_SITE_CHAPTERS:-/CODE/oaichu-novels/src/content/chapters}/$($ON get "$B" publish.site_book_id 2>/dev/null || echo $ID)
  $ON migrate "$B" --published-upto $(ls "$SITE" 2>/dev/null | wc -l) >&2 || exit 2; fi
N=$($ON next "$B") || exit 2; LAST=$(ls "$B"/chapters/$(printf %04d $((N-1)))*.md 2>/dev/null | head -1)
TW=$($ON get "$B" layout.target_words); TW=${NOVEL_WORDS:-${TW:-3000}}; MINW=$($ON get "$B" layout.min_words); MINW=${NOVEL_MIN_WORDS:-${MINW:-3000}}; ROUNDS=${ONOVEL_EXPAND_ROUNDS:-4}
STY=$($ON get "$B" layout.heading_style); MAXATT=$($ON get "$B" max_attempts); SOFTMAX=$($ON get "$B" soft_max)
R=$RUNS/$ID-$(printf %04d $N)-$(date +%Y%m%dT%H%M%S); mkdir -p "$R"; log(){ echo "[$(date +%H:%M:%S)] $*" | tee -a "$R/run.log" >&2; }
wc_(){ python3 -c "import sys;sys.path.insert(0,'$I');from onovel.gates import count_words;print(count_words(open('$1').read()))"; }
log "book=$ID chapter=$N dry=$DRY stub=$STUB run=$R"
$ON context "$B" $N --hint "$HINT" > "$R/context.md" || { log "context build failed"; exit 2; }
log "context: $(wc -c < "$R/context.md") bytes (semantic retrieval, budget ${ONOVEL_CTX_TOKENS:-18000} tokens)"
gem(){ # gem <prompt-file> <out>   step 1/2 LLM: Gemini (pi-gemini/Antigravity, free sub) -> fallback OpenRouter FREE (glm.py). Never paid.
  local f="$1.in.md"; head -c ${NOVEL_PROMPT_MAX:-150000} "$1" > "$f"  # pass as @file: argv limit is 128KB
  local GD=$RUNS/gemini-down; if [ "$LLM" = gemini ] && [ -f $GD ] && [ $(( $(date +%s) - $(stat -c %Y $GD) )) -lt ${NOVEL_GEMINI_DOWN_TTL:-3600} ]; then log "gemini skipped (auth down flag $GD, $(( ($(date +%s)-$(stat -c %Y $GD))/60 ))min old) -> OpenRouter FREE"; fi
  if [ "$LLM" = gemini ] && ! { [ -f $GD ] && [ $(( $(date +%s) - $(stat -c %Y $GD) )) -lt ${NOVEL_GEMINI_DOWN_TTL:-3600} ]; }; then
    timeout 1800 pi -p --no-session --provider antigravity --model "$GM" --thinking medium "@$f" "Thực hiện đúng phần NHIỆM VỤ ở cuối tệp đính kèm. Chỉ trả về kết quả." < /dev/null > "$2" 2> "$2.err"; local rc=$?
    if [ $rc -eq 0 ] && [ -s "$2" ]; then log "gemini ok ($GM, $(wc -c < "$2") bytes)"; return 0; fi
    grep -qiE "authenticat|login|unauthori|401" "$2.err" && { touch $GD; log "gemini auth failure -> flag $GD set for 1h"; }
    log "Gemini failed rc=$rc: $(tail -2 "$2.err" | tr '\n' ' ' | cut -c1-300) -> fallback OpenRouter FREE (glm.py)"
  fi
  timeout 3600 python3 $T/gen.py "$f" "$2" 2> >(tee "$2.err" >> "$R/run.log"); local rc=$?; sleep 1  # live progress in run.log (supervisor sees it)
  [ $rc -eq 4 ] && { log "LLM BLOCKED (gemini + free quota): $(tail -1 "$2.err")"; echo "[$(date '+%F %T')] $ID ch$N: gemini and all OpenRouter free models blocked" >> $RUNS/llm-blocked.txt; exit 4; }
  [ $rc -eq 0 ] && [ -s "$2" ] || { log "LLM failed rc=$rc: $(tail -3 "$2.err")"; return 1; }; return 0; }
# 1 plan
{ cat "$R/context.md"; echo; echo "# NHIỆM VỤ"; echo "Lập dàn ý chi tiết cho Chương $N gồm 4-5 cảnh; MỖI cảnh bắt đầu bằng một dòng riêng dạng '## Cảnh k: <tên cảnh>' rồi 3-5 câu: mục tiêu, xung đột, chuyển biến, chi tiết cụ thể; cảnh cuối có móc cuối chương. Tuân thủ style bible, sự thật khóa, nợ cốt truyện, đề cương. Gợi ý của tác giả: ${HINT:-(không)}. Chỉ trả về dàn ý tiếng Việt."; } > "$R/plan.prompt"
if [ $STUB = 1 ]; then echo "(stub plan) $HINT" > "$R/plan.md"; else log "step1 plan ($LLM)"; gem "$R/plan.prompt" "$R/plan.md" || exit 3; fi
# 2 draft
{ cat "$R/context.md"; echo; echo "# DÀN Ý CHƯƠNG $N"; cat "$R/plan.md"; echo; echo "# NHIỆM VỤ"; echo "Viết toàn văn Chương $N theo dàn ý, đúng giọng và định dạng tiêu đề trong style bible (dòng đầu là tiêu đề chương). Độ dài BẮT BUỘC: khoảng $TW chữ (tối thiểu $MINW chữ); triển khai đầy đủ từng cảnh trong dàn ý bằng hành động, thoại, chi tiết cảm giác, không tóm tắt. Thoại trong ngoặc kép thẳng, không dấu gạch dài, không chữ Hán, không ghi chú; tu sĩ không xưng 'tôi'. Chỉ trả về chương."; } > "$R/draft.prompt"
if [ $STUB = 1 ]; then { echo "# Chương $N: Bản thử"; if [ -n "$LAST" ]; then tail -n +2 "$LAST"; else tail -n +2 "${ONOVEL_STUB_TEXT:-/dev/null}"; fi; } > "$R/draft.md"
else log "step2 draft scene by scene ($LLM -> free models)"
  $ON draft-scenes "$R" $N --target $TW 2>>"$R/run.log"; drc=$?
  [ $drc = 4 ] && { log "LLM BLOCKED during scene drafting"; exit 4; }
  if [ $drc != 0 ] || [ ! -s "$R/draft.md" ]; then log "scene drafting failed (rc=$drc): whole-chapter fallback"
    for k in 1 2 3; do gem "$R/draft.prompt" "$R/draft.md" || exit 3
      dc=$(python3 $T/draftcheck.py "$R/draft.md" $TW) && { log "draft try $k: $dc"; break; }
      log "draft try $k REJECTED: $dc"; mv "$R/draft.md" "$R/draft.bad$k.md"; done
    [ -s "$R/draft.md" ] || { log "no usable draft (all 3 rejected as degenerate)"; exit 3; }; fi
  w=$(wc_ "$R/draft.md"); log "draft: $w words"; GOAL=$(( MINW * 105 / 100 ))
  for k in $(seq 1 $ROUNDS); do [ $w -ge $GOAL ] && break
    log "expand round $k/$ROUNDS ($w < $GOAL)"; ew=$($ON expand "$R" --min $GOAL --target $TW --passes 1 2>>"$R/run.log"); [ $? = 4 ] && { log "LLM BLOCKED during expand"; exit 4; }
    w=$(wc_ "$R/draft.md"); done
  [ $w -ge $MINW ] || { log "still short after $ROUNDS expand rounds ($w < $MINW) -> quarantine, retry later"; $ON quarantine "$B" "$R" $N "short draft $w < $MINW" >&2; exit 5; }
fi
python3 $T/normalize-headings.py --style $STY "$R/draft.md" >/dev/null
# 3 polish
if [ $STUB = 1 ]; then cp "$R/draft.md" "$R/chapter.md"; else log "step3 polish (MiMo)"; python3 $T/polish.py "$R/draft.md" --bible "$BIB" --out "$R/chapter.md" | tee -a "$R/run.log" >&2; fi
python3 $T/normalize-headings.py --style $STY "$R/chapter.md" >/dev/null
if [ $STUB = 0 ] && [ $(wc_ "$R/chapter.md") -lt $MINW ]; then log "polished chapter short ($(wc_ "$R/chapter.md") < $MINW): one more expand + polish"
  cp "$R/chapter.md" "$R/draft.md"; $ON expand "$R" --min $(( MINW * 105 / 100 )) --target $TW --passes 2 2>>"$R/run.log" >/dev/null
  python3 $T/polish.py "$R/draft.md" --bible "$BIB" --out "$R/chapter.md" | tee -a "$R/run.log" >&2; python3 $T/normalize-headings.py --style $STY "$R/chapter.md" >/dev/null
  [ $(wc_ "$R/chapter.md") -ge $MINW ] || { log "chapter still short -> quarantine (never published short)"; $ON quarantine "$B" "$R" $N "short chapter" >&2; exit 5; }; fi
# gates
NL=; [ $STUB = 1 ] && NL=--no-llm
ATT=$(ls -d $RUNS/$ID-$(printf %04d $N)-* 2>/dev/null | wc -l); [ $ATT -ge ${MAXATT:-3} ] && SOFTMAX=999
log "gates (style, locked facts, layout, canon): attempt $ATT, rule-based issues block, LLM-judged soft issues allowed <= $SOFTMAX, judge/API error = ERROR"
gate(){ local g; g=$($ON gate "$B" "$R/chapter.md" --n $N $NL --soft-max $SOFTMAX --out "$R/gate.json"); local rc=$?; log "gate: $g"; return $rc; }
gate; rc=$?
for k in 1 2 3; do [ $rc = 1 ] && [ $STUB = 0 ] || break
  $ON fixlist "$R/gate.json" > "$R/fix.txt"; [ -s "$R/fix.txt" ] || break
  log "fix round $k (MiMo): $(wc -l < "$R/fix.txt") issues"; python3 $T/fix.py "$R/chapter.md" "$R/fix.txt" | tee -a "$R/run.log" >&2
  gate; rc=$?; done
case $rc in 0) RES=PASS;; 1) RES=FAIL;; *) RES=ERROR;; esac
log "result: $RES"
echo "book: $ID"; echo "chapter: $N"; echo "run: $R"; echo "verdict: $RES"; echo "summary: $(sed -n 2,20p "$R/plan.md" | tr '\n' ' ' | head -c 300)"
if [ $RES != PASS ]; then $ON learn "$B" "$R/gate.json" $N 2>/dev/null || true; fi
if [ $RES = ERROR ]; then $ON quarantine "$B" "$R" $N "gate ERROR: $(python3 -c "import json;print('; '.join(json.load(open('$R/gate.json'))['errors'])[:200])" 2>/dev/null)" | tee -a "$R/run.log" >&2; exit 5; fi
[ $RES = FAIL ] && { log "gates failed: chapter kept in run dir only"; exit 1; }
if [ $DRY = 1 ]; then log "dry-run: not committed"; exit 0; fi
log "commit transaction (chapter + canonical state)"; $ON commit "$B" "$R" $N 2>&1 | tee -a "$R/run.log" >&2; [ ${PIPESTATUS[0]} = 0 ] || { log "commit failed -> quarantined"; exit 5; }
exit 0
