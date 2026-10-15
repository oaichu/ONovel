#!/usr/bin/env bash
# novel.sh [--dry-run] [--stub] <book> [chapter hint...]   (REWRITTEN 2026-10-15 after /CODE loss; minimal)
# 3-step pipeline for the next chapter of an inkos book in /CODE/inkos-books/xemtruyen/books/<id>:
#   1 plan / 2 draft: OpenRouter FREE models via tools/glm.py (nemotron-3-ultra:free > gemma-4-31b:free > openrouter/free) (tools/glm.py), NOVEL_LLM=glm (default) | gemini (legacy pi/Antigravity)
#   3 polish: MiMo v2.6 Flash (tools/polish.py)
# then gates: normalize-headings, stylegate (style lock), lockcheck (locked facts); one MiMo minimal-fix round (tools/fix.py)
# if they fail; canon update + lessons. --dry-run: everything runs but the chapter is NOT written into the book and canon
# is not updated (outputs stay in runs/). --stub: no LLM calls (copies the last chapter as the draft) to test plumbing.
set -uo pipefail
source ~/.profile >/dev/null 2>&1; eval "$(grep '^export ' /CODE/inkos/run-inkos.sh)"
I=/CODE/inkos; T=$I/tools; P=${INKOS_PROJECT:-/CODE/inkos-books/xemtruyen}; GM=${NOVEL_GEMINI_MODEL:-gemini-3-8-flash}; LLM=${NOVEL_LLM:-glm}
DRY=0; STUB=0; while [[ ${1:-} == --* ]]; do case $1 in --dry-run) DRY=1;; --stub) STUB=1;; esac; shift; done
Q=${1:?usage: novel.sh [--dry-run] [--stub] <book> [hint]}; shift; HINT="$*"
case $Q in tien|tt) Q=tien-tro;; dkgh) Q=dieu-khoan-gia-han;; pnntl) Q=pham-nhan-nghich-thien-luc;; tuc) Q=tuc-the;; esac
B=$(ls -d "$P/books/$Q"* 2>/dev/null | head -1); [ -d "$B" ] || { echo "ERROR: book '$Q' not found in $P/books" >&2; exit 2; }
ID=$(basename "$B"); BIB="$B/style-bible.md"; [ -f "$BIB" ] || { echo "ERROR: $BIB missing (style lock required)" >&2; exit 2; }
LAST=$(ls "$B"/chapters/[0-9]*.md 2>/dev/null | sort | tail -1); N=$(( ${LAST:+10#$(basename "$LAST" | grep -oE '^[0-9]+')} + 1 ))
R=$I/runs/$ID-$(printf %04d $N)-$(date +%Y%m%dT%H%M%S); mkdir -p "$R"; log(){ echo "[$(date +%H:%M:%S)] $*" | tee -a "$R/run.log" >&2; }
log "book=$ID chapter=$N dry=$DRY stub=$STUB run=$R"
OUTLINE=$(cat "$B"/story/outline/*.md "$B/de-cuong.md" 2>/dev/null | head -c 10000)
{ echo "# QUY TẮC BIÊN TẬP"; cat $T/editor-guardrails.md; echo; python3 $T/lessons.py prompt "$B"; echo; python3 $T/skills.py prompt "$B" --max ${NOVEL_SKILLS_MAX:-15000}; echo; echo "# STYLE BIBLE (KHÓA)"; head -c 15000 "$BIB"
  echo; python3 $T/canon.py context "$B" --n 3; echo; echo "# ĐỀ CƯƠNG"; echo "$OUTLINE"
  echo; echo "# ĐOẠN CUỐI CHƯƠNG TRƯỚC"; [ -n "$LAST" ] && tail -c 4000 "$LAST"; } > "$R/context.md"
gem(){ # gem <prompt-file> <out>   (step 1/2 LLM; name kept for history)
  local f="$1.in.md"; head -c ${NOVEL_PROMPT_MAX:-150000} "$1" > "$f"  # pass as @file: argv limit is 128KB
  if [ "$LLM" = glm ]; then timeout 7200 python3 $T/glm.py "$f" "$2" 2> "$2.err"; local rc=$?; cat "$2.err" >> "$R/run.log"
    [ $rc -eq 4 ] && { log "LLM BLOCKED (free quota): $(tail -1 "$2.err")"; exit 4; }
    [ $rc -eq 0 ] && [ -s "$2" ] || { log "LLM failed rc=$rc: $(tail -3 "$2.err")"; return 1; }; return 0; fi
  timeout 1800 pi -p --no-session --provider antigravity --model "$GM" --thinking medium "@$f" "Thực hiện đúng phần NHIỆM VỤ ở cuối tệp đính kèm. Chỉ trả về kết quả." < /dev/null > "$2" 2> "$2.err"; local rc=$?
  [ $rc -eq 0 ] && [ -s "$2" ] || { log "Gemini failed rc=$rc: $(tail -3 "$2.err")"; return 1; }; }
# 1 plan
{ cat "$R/context.md"; echo; echo "# NHIỆM VỤ"; echo "Lập dàn ý chi tiết cho Chương $N (5-8 cảnh, mỗi cảnh 2-4 câu: mục tiêu, xung đột, chuyển biến, móc cuối chương). Tuân thủ style bible, sự thật khóa, đề cương. Gợi ý của tác giả: ${HINT:-(không)}. Chỉ trả về dàn ý tiếng Việt."; } > "$R/plan.prompt"
if [ $STUB = 1 ]; then echo "(stub plan) $HINT" > "$R/plan.md"; else log "step1 plan ($LLM)"; gem "$R/plan.prompt" "$R/plan.md" || exit 3; fi
# 2 draft
{ cat "$R/context.md"; echo; echo "# DÀN Ý CHƯƠNG $N"; cat "$R/plan.md"; echo; echo "# NHIỆM VỤ"; echo "Viết toàn văn Chương $N theo dàn ý, đúng giọng và định dạng tiêu đề trong style bible (dòng đầu là tiêu đề chương). Độ dài BẮT BUỘC: khoảng ${NOVEL_WORDS:-3000} chữ (tối thiểu ${NOVEL_MIN_WORDS:-2400} chữ); triển khai đầy đủ từng cảnh trong dàn ý bằng hành động, thoại, chi tiết cảm giác, không tóm tắt. Thoại trong ngoặc kép thẳng, không dấu gạch dài, không chữ Hán, không ghi chú. Chỉ trả về chương."; } > "$R/draft.prompt"
if [ $STUB = 1 ]; then { echo "# Chương $N: Bản thử"; tail -n +2 "$LAST"; } > "$R/draft.md"; else log "step2 draft ($LLM)"; for k in 1 2 3; do gem "$R/draft.prompt" "$R/draft.md" || exit 3; w=$(wc -w < "$R/draft.md"); log "draft try $k: $w words"; [ $w -ge ${NOVEL_MIN_WORDS:-2400} ] && break; cp "$R/draft.md" "$R/draft.short$k.md"; done; fi
STY=colon; grep -q 'Chương N ·' "$BIB" && STY=dot
python3 $T/normalize-headings.py --style $STY "$R/draft.md" >/dev/null
# 3 polish
if [ $STUB = 1 ]; then cp "$R/draft.md" "$R/chapter.md"; else log "step3 polish (MiMo)"; python3 $T/polish.py "$R/draft.md" --bible "$BIB" --out "$R/chapter.md" | tee -a "$R/run.log" >&2; fi
python3 $T/normalize-headings.py --style $STY "$R/chapter.md" >/dev/null
NL=; [ $STUB = 1 ] && NL=--no-llm
gate(){ python3 $T/stylegate.py check "$B" "$R/chapter.md" $NL > "$R/style.json"; local a=$?
  python3 - "$R" <<'PY' || a=0   # drop LLM false positives: flagged word absent from the chapter (exit 1 = none left)
import json,re,sys
r=sys.argv[1]; d=json.load(open(r+'/style.json')); t=open(r+'/chapter.md').read().lower()
def real(v):
    w=(v.get('word') or '').strip().lower()
    return not (v.get('source')=='llm' and w and not re.search(r'(?<!\w)'+re.escape(w)+r'(?!\w)',t))
d['issues']=[v for v in d.get('issues',[]) if real(v)]; json.dump(d,open(r+'/style.json','w'),ensure_ascii=False)
sys.exit(0 if [v for v in d['issues'] if v.get('source')!='layout'] else 1)
PY
 python3 $T/lockcheck.py check "$B" "$R/chapter.md" $NL > "$R/lock.json"; local b=$?; return $(( a|b )); }
log "gates (style lock + locked facts)"
if ! gate; then
  python3 - "$R" > "$R/fix.txt" <<'PY'
import json,sys
r=sys.argv[1]; out=[]
for f,k in (('style.json','issues'),('lock.json','violations')):
    try: d=json.load(open(f'{r}/{f}'))
    except Exception: continue
    for v in d.get(k,[]):
        if v.get('source')=='layout': continue
        out.append(f"- [{v.get('fact_id') or v.get('source')}] {v.get('word','')} {v.get('reason','')} | trích: {(v.get('quote') or '')[:200]}")
print("\n".join(out))
PY
  for k in 1 2 3; do [ $STUB = 0 ] && [ -s "$R/fix.txt" ] || break; log "fix round $k (MiMo): $(wc -l < "$R/fix.txt") issues"; python3 $T/fix.py "$R/chapter.md" "$R/fix.txt" | tee -a "$R/run.log" >&2; gate && break; python3 - "$R" > "$R/fix.txt" <<'PY'
import json,sys
r=sys.argv[1]; out=[]
for f,k in (('style.json','issues'),('lock.json','violations')):
    try: d=json.load(open(f'{r}/{f}'))
    except Exception: continue
    for v in d.get(k,[]):
        if v.get('source')=='layout': continue
        out.append(f"- [{v.get('fact_id') or v.get('source')}] {v.get('word','')} {v.get('reason','')} | trích: {(v.get('quote') or '')[:200]}")
print("\n".join(out))
PY
done
fi
RES=$(python3 - "$R" <<'PY'
import json,sys
r=sys.argv[1]; s=json.load(open(r+'/style.json')); l=json.load(open(r+'/lock.json'))
si=[v for v in s.get('issues',[]) if v.get('source')!='layout']; lv=l.get('violations',[])
print(f"style={'PASS' if not si else 'FAIL(%d)'%len(si)} locked_facts={'PASS' if not lv else 'FAIL(%d)'%len(lv)} active_facts={len(l.get('active_facts',[]))} llm_error={s.get('llm_error') or l.get('llm_error') or 'none'}")
PY
)
log "result: $RES"
TITLE=$(head -1 "$R/chapter.md" | sed -E 's/^#+ *//; s/[\/:·]+/ /g; s/ +/_/g'); DST="$B/chapters/$(printf %04d $N)_${TITLE}.md"
if [ $DRY = 1 ]; then log "dry-run: chapter NOT written (would be $DST)"; OUT="$R/chapter.md"
elif [[ $RES == *FAIL* ]]; then log "gates failed: chapter kept in run dir only"; OUT="$R/chapter.md"
  python3 $T/lessons.py learn "$B" "Chương $N bị cổng chặn: $(head -c 300 "$R/fix.txt" | tr '\n' ' ')" >/dev/null 2>&1 || true
else cp "$R/chapter.md" "$DST"; OUT="$DST"; [ $STUB = 0 ] && python3 $T/canon.py update "$B" "$DST" >> "$R/run.log" 2>&1; fi
echo "book: $ID"; echo "chapter: $N"; echo "file: $OUT"; echo "locked-facts: $RES"; echo "words: $(wc -w < "$R/chapter.md")"; echo "run: $R"
echo "summary: $(sed -n 2,40p "$R/plan.md" | tr '\n' ' ' | head -c 400)"
[[ $RES == *FAIL* ]] && exit 1 || exit 0
