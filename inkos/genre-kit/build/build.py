#!/usr/bin/env python3
"""Rebuild genre-kit skills/cards from vendor repos via MiMo (rules only, no verbatim story text)."""
import sys, glob, os, re, json, concurrent.futures as cf
sys.path.insert(0, "/CODE/inkos/tools"); import mimo
V="/CODE/inkos/genre-kit/vendor"; G="/CODE/inkos/genre-kit"
LW="oh-story-claudecode/skills/story-long-write/references"; CW="chinese-webnovel-skills"; WS="Chinese-WebNovel-Skill/references/modules"
XX="xianxia-cultivation-agent-skills/skills"; CN="chinese-novelist-skill/references/guides"
HOUSE="""LUẬT NHÀ (bắt buộc, ghi nguyên vào phần 'Luật nhà' nếu liên quan):
- Thoại luôn trong ngoặc kép thẳng "..."; tuyệt đối không dùng dấu gạch dài (—) ở bất cứ đâu.
- Tu sĩ không bao giờ xưng "tôi"; chỉ phàm nhân xưng "tôi". Tu sĩ nói với phàm nhân: bản tọa / lão phu (hoặc bản công tử, bổn cô nương theo thân phận). Đồng cấp: tại hạ ↔ đạo hữu. Tông môn: vãn bối/đệ tử/sư huynh/sư đệ/tiền bối.
- Độ dài chương bám mục tiêu của bộ ±15%; mọi chương kết bằng móc câu (hook)."""
SK={ # name: (title, house?, [globs], focus)
 "worldbuilding":("Xây dựng thế giới",0,[f"{WS}/concept_planning/runtime.md",f"{CW}/references/worldbuilding.md",f"{CW}/skills/world/SKILL.md",f"{XX}/xianxia-asset-bible/**/*.md","Novel-OS/templates/story_bible/template.md","book-os/standards/genre-guides/fantasy-sci-fi.md"],"thiết lập thế giới huyền huyễn/tiên hiệp/cổ đại/hiện đại, kinh tế-chính trị-tông môn, quy tắc nhất quán, story bible"),
 "cultivation-rules":("Quy tắc tu luyện & kiểm toán tiến cấp sức mạnh",1,[f"{XX}/xianxia-script-doctor/references/power-consistency.md",f"{XX}/xianxia-asset-bible/references/asset-schema.md",f"{CW}/references/goldfinger-types.md",f"{CW}/skills/goldfinger/SKILL.md",f"{CW}/skills/shuangdian/SKILL.md",f"{LW}/style-combat-face.md",f"{LW}/reader-contract-and-progression.md"],"hệ cảnh giới, chi phí tu luyện, kim thủ chỉ, kiểm toán power creep, sảng điểm có cái giá"),
 "foreshadowing":("Quản lý phục bút",0,[f"{WS}/plot_logic/runtime.md",f"{CN}/hook-techniques.md",f"{LW}/long-suspense.md",f"{LW}/long-reversal.md","long-novel-agent-kit/SKILL.md"],"sổ phục bút: gieo, nhắc, thu hồi; hạn thu hồi; bảng theo dõi"),
 "character-psychology":("Tâm lý nhân vật",0,[f"{WS}/character_consistency/runtime.md",f"{WS}/character_consistency/tutorial.md",f"{CN}/character-building.md",f"{CW}/skills/character/SKILL.md",f"{LW}/character-design-methods.md",f"{LW}/character-relations.md","Novel-OS/templates/character/template.md"],"động cơ, vết thương, mong muốn vs nhu cầu, nhất quán hành vi, quan hệ"),
 "romance-arcs":("Tuyến tình cảm",1,["novel-master/SKILL.md","novel-master/references/genres.md","novel-master/references/dramaturgy.md","novel-master/references/banned-words.md",f"{LW}/emotional-arc-design.md",f"{LW}/female-audience-writing.md",f"{LW}/emotion-on-page.md",f"{CW}/skills/emotion/SKILL.md",f"{CW}/references/show-emotion.md",f"{CW}/references/trope-library.md"],"nhịp tình cảm ngôn tình cổ đại/hiện đại/huyền huyễn ngôn tình, ngược-sủng, các mốc, show don't tell cảm xúc"),
 "etiquette-address":("Lễ nghi & xưng hô",1,[f"{WS}/dialogue/runtime.md",f"{XX}/xianxia-dialogue-polish/**/*.md",f"{CN}/dialogue-writing.md",f"{LW}/dialogue-mastery.md"],"xưng hô theo thân phận người nói trong tiên hiệp, cung đình, cổ đại, hiện đại; kính ngữ; giọng nói theo vai"),
 "pacing":("Nhịp truyện & móc chương",1,[f"{WS}/chapter_ending/runtime.md",f"{WS}/transition/runtime.md",f"{CW}/references/sentence-rhythm.md",f"{CW}/references/length-standards.md",f"{CW}/references/hook-library.md",f"{CN}/chapter-guide.md",f"{LW}/long-chapter-hooks.md",f"{LW}/outline-rhythm.md"],"nhịp cảnh, nhịp chương, độ dài chương, móc cuối chương, nhịp câu"),
 "continuity-guardian":("Biên tập văn & người gác liên tục",1,[f"{WS}/consistency_review/runtime.md","Novel-OS/agents/continuity_guardian/prompt.md","Novel-OS/agents/editor/prompt.md","book-os/claude-code/agents/continuity-checker.md","book-os/claude-code/agents/prose-reviewer.md",f"{CW}/references/continuity-check.md","long-novel-agent-kit/docs/adversarial-verification.md"],"biên tập câu chữ và kiểm tra liên tục (sự kiện, vết thương, vật phẩm, thời gian, cảnh giới, xưng hô)"),
 "anti-ai-prose":("Chống văn AI",1,[f"{WS}/anti_ai_voice/runtime.md",f"{WS}/anti_ai_voice/tutorial.md","oh-story-qin/skills/story-deslop/references/anti-ai-writing.md",f"{CW}/references/anti-ai-checklist.md",f"{CW}/references/human-texture.md",f"{LW}/banned-words.md"],"dấu hiệu văn AI trong bản dịch/convert tiếng Việt và cách sửa; bổ trợ cho /skill:novel-deslop (không lặp lại nó)"),
 "palace-intrigue":("Cung đấu & trạch đấu",1,["novel-master/SKILL.md","novel-master/references/genres.md","novel-master/references/dramaturgy.md","novel-master/references/banned-words.md",f"{LW}/genre-prose-cards/宫斗宅斗.md",f"{LW}/genre-prose-cards/古风世情.md",f"{CW}/references/trope-library.md",f"{LW}/long-genre-mechanics.md",f"{LW}/plot-special-topics.md"],"chỉ phần cung đấu/trạch đấu/gia đấu: phe phái, đấu trí, lễ nghi cung đình, phẩm cấp phi tần, cơ chế mưu kế"),
 "modern-cn-romance":("Ngôn tình hiện đại",1,["novel-master/SKILL.md","novel-master/references/genres.md","novel-master/references/dramaturgy.md","novel-master/references/banned-words.md",f"{LW}/genre-prose-cards/豪门总裁.md",f"{LW}/genre-prose-cards/职场婚恋.md",f"{LW}/genre-prose-cards/现言脑洞.md",f"{CW}/references/warm-realism.md",f"{LW}/female-audience-writing.md",f"{LW}/long-genre-catalog.md"],"chỉ phần hiện đại: tổng tài, công sở, hào môn, gia đấu, huyền nghi tài chính; xưng hô hiện đại anh/em/tôi"),
}
CARDS={
 "card-dong-phuong-tien-hiep":("Đông phương tiên hiệp",[f"{LW}/genre-prose-cards/东方仙侠.md", f"{LW}/genre-prose-cards/都市修真.md", f"{XX}/xianxia-script-drafting/SKILL.md",f"{CW}/references/genre-library.md"],"tiên hiệp phương Đông: tông môn, đạo tâm, phi thăng"),
 "card-truyen-thong-huyen-huyen":("Truyền thống huyền huyễn",[f"{LW}/genre-prose-cards/传统玄幻.md",f"{LW}/genre-prose-cards/玄幻脑洞.md",f"{CW}/references/goldfinger-types.md"],"huyền huyễn truyền thống: đấu khí, huyết mạch, đại lục, kim thủ chỉ"),
 "card-huyen-huyen-ngon-tinh":("Huyền huyễn ngôn tình",["novel-master/SKILL.md","novel-master/references/genres.md","novel-master/references/dramaturgy.md","novel-master/references/banned-words.md",f"{LW}/genre-prose-cards/玄幻言情.md",f"{LW}/genre-prose-cards/古言脑洞.md",f"{LW}/female-audience-writing.md",f"{CW}/references/genre-library.md"],"huyền huyễn/tiên hiệp có tuyến tình cảm nữ tần, ngôn tình cổ đại"),
 "card-sang-diem":("Sảng điểm",[f"{CW}/skills/shuangdian/SKILL.md",f"{LW}/commercial-core-methods.md",f"{LW}/style-combat-face.md"],"sảng điểm: vả mặt, lật kèo, thu hoạch; mật độ và cái giá"),
}
def clean(t):
    out=[]; fence=False
    for l in t.splitlines():
        if l.strip().startswith("```"): fence=not fence; continue
        if fence and re.search(r"[\u4e00-\u9fff]{25,}",l): continue  # prose-y line inside code block
        if l.lstrip().startswith(">") or re.match(r"^\s*[「“\"].{40,}",l): continue  # quoted passages
        if len(l)>260 and not re.match(r"^\s*([-*|#\d]|\w+:)",l): continue
        out.append(l)
    return "\n".join(out)
def gather(globs,cap=45000):
    fs=[]
    for g in globs:
        q=g.replace("oh-story-claudecode/","oh-story-qin/",1); m=sorted(glob.glob(f"{V}/{q}",recursive=True)) if q!=g else []
        fs.extend(m or sorted(glob.glob(f"{V}/{g}",recursive=True)))
    fs=[f for f in dict.fromkeys(fs) if os.path.isfile(f) and not re.search(r"example|demo|case-stud|sample",f,re.I)]
    s=""; used=[]
    for f in fs:
        c=clean(open(f,errors="ignore").read())[:14000]; s+=f"\n\n=== {os.path.relpath(f,V)} ===\n{c}"; used.append(os.path.relpath(f,V))
    return s[:cap],used
SYS="Bạn là biên tập viên mạng văn Việt chuyên truyện convert/Việt hóa từ webnovel Trung Quốc (huyền huyễn, tiên hiệp, ngôn tình cổ đại, ngôn tình hiện đại)."
def skill(name):
    title,house,globs,focus=SK[name]; src,used=gather(globs,55000)
    p=f"""Dựa trên tài liệu kỹ thuật viết bên dưới (nhiều repo, tiếng Trung/Anh), soạn một SKILL tiếng Việt tên "{name}" ({title}). Trọng tâm: {focus}.
Yêu cầu:
- Chỉ chắt lọc nguyên tắc, quy trình, checklist, bảng kiểm, lỗi thường gặp → cách sửa. KHÔNG chép bất kỳ đoạn văn truyện mẫu nào, không trích nguyên văn ví dụ, không tên nhân vật trong ví dụ.
- Gộp các ý trùng nhau thành một mục; Việt hóa thuật ngữ theo lối Hán-Việt quen dùng (cảnh giới, kim thủ chỉ, phục bút, sảng điểm, vả mặt...).
- Định dạng Markdown: bắt đầu bằng front matter YAML (name: {name}, description: một câu tiếng Việt nói khi nào dùng), rồi các mục: Mục đích; Khi nào dùng; Quy trình; Checklist kiểm tra; Lỗi thường gặp & cách sửa{'; Luật nhà' if house else ''}.
- Dài 900-1600 chữ. Với tuyến tình cảm: áp dụng công thức chướng ngại → tích tụ → bùng nổ và danh sách cấm kỵ nếu tài liệu có. Không dùng dấu gạch dài (—).
{HOUSE if house else 'Thoại ví dụ (nếu có, tự viết ngắn) dùng ngoặc kép thẳng; không dùng dấu gạch dài.'}

TÀI LIỆU:
{src}"""
    out=mimo.chat(p,system=SYS,max_tokens=8000).replace("—",", ")
    d=f"{G}/skills/{name}"; os.makedirs(d,exist_ok=True); open(f"{d}/SKILL.md.tmp","w").write(out.strip()+"\n"); os.replace(f"{d}/SKILL.md.tmp",f"{d}/SKILL.md")
    json.dump({"sources":used},open(f"{d}/SOURCES.json","w"),ensure_ascii=False,indent=1); return name,used
def card(name):
    title,globs,focus=CARDS[name]; src,used=gather(globs,30000)
    p=f"""Soạn THẺ THỂ LOẠI tiếng Việt "{title}" ({focus}) cho người viết/AI, dựa trên tài liệu dưới. Ngắn gọn 300-600 chữ, Markdown, các mục: Lời hứa với độc giả; Mô-típ & cơ chế cốt lõi; Giọng văn & từ vựng; Xưng hô; Cấm kỵ (phá bối cảnh); Móc chương điển hình (mô tả, không chép mẫu).
Không chép nguyên văn truyện mẫu. Không dấu gạch dài.
{HOUSE}

TÀI LIỆU:
{src}"""
    out=mimo.chat(p,system=SYS,max_tokens=4000).replace("—",", ")
    open(f"{G}/cards/{name}.md.tmp","w").write(out.strip()+f"\n\n<!-- sources: {', '.join(used)} -->\n"); os.replace(f"{G}/cards/{name}.md.tmp",f"{G}/cards/{name}.md"); return name,used
if __name__=="__main__":
    only=set(sys.argv[1:])
    jobs=[(skill,n) for n in SK if not only or n in only]+[(card,n) for n in CARDS if not only or n in only]
    with cf.ThreadPoolExecutor(6) as ex:
        for f in cf.as_completed([ex.submit(fn,n) for fn,n in jobs]):
            try: n,u=f.result(); print("OK",n,len(u),"files",flush=True)
            except Exception as e: print("FAIL",repr(e)[:200],flush=True)
