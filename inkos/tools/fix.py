#!/usr/bin/env python3
# fix.py <chapter.md> <instructions-file>: MiMo minimal fix (thinking disabled); apply only if len within 5% and no names lost.
# Recovered verbatim from /workspace/mimo-fix/fix.py on 2026-10-15.
import sys, os, re, json, shutil, urllib.request
sys.path.insert(0, '/CODE/inkos/tools'); import stylegate as sg, polish as pl
chap, instf = sys.argv[1:3]; inst = open(instf, encoding='utf-8').read()
t = open(chap, encoding='utf-8').read(); head, rest = t.split('\n', 1)
while rest.lstrip().startswith('#'):  # keep repeated title headings (imported chapters) out of the LLM text
    h2, rest = rest.lstrip().split('\n', 1); head += '\n\n' + h2
prompt = ("Bạn là biên tập viên tiên hiệp. Sửa TỐI THIỂU chương dưới đây theo đúng các chỉ dẫn/lỗi liệt kê; chỉ đổi từ hoặc câu bị nêu, "
  "giữ nguyên mọi đoạn khác từng chữ, không đổi sự kiện, tên riêng, số đoạn. Thoại dùng dấu nháy kép thẳng \", cấm dấu gạch dài. "
  "Tu sĩ không xưng 'tôi'. Chỉ trả về toàn văn chương đã sửa (không tiêu đề, không giải thích).\n\nCHỈ DẪN/LỖI:\n" + inst + "\n\nCHƯƠNG:\n" + rest.strip())
import mimo
out = mimo.chat(prompt, temperature=0.2, max_tokens=16000)  # streaming, 20s/90s/5min timeouts, 1 retry
out = re.sub(r"^```\w*\n|\n```\s*$", "", out.strip())
if out.lstrip().startswith("#"): out = out.split("\n", 1)[1]
wd, wo = len(rest.split()), len(out.split()); lost = sorted(n for n in pl.names(rest) - pl.names(out) if n not in inst)  # names the fix list asked to change may go
why = None
if not out.strip() or abs(wo - wd) > 0.05 * wd: why = f"length {wd}->{wo}"
elif pl.HAN.search(out): why = "Han"
elif lost: why = f"names lost {lost[:6]}"
elif '—' in out: why = "em dash"
if not why:
    bak = chap + '.bak-clean'
    if os.path.exists(bak): bak = chap + '.bak-mimo'
    shutil.copy2(chap, bak); open(chap, 'w', encoding='utf-8').write(head + "\n\n" + out.strip() + "\n")
print(json.dumps({"chapter": os.path.basename(chap), "words": [wd, wo], "applied": not why, "rejected": why}, ensure_ascii=False))
