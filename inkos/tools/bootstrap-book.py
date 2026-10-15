#!/usr/bin/env python3
"""bootstrap-book.py <book_dir> <genre-key> <source.md...> [--facts-only] [--sample-chapters f...]   (NEW 2026-10-15)
MiMo derives style-bible.md (locked, YAML front matter: genre, era, narration, register, banned, llm_only, address_rules,
layout) and locked_facts.yaml from the story bible / chapters. Never overwrites an existing file (writes *.new instead)."""
import sys, os, json, argparse, yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import mimo
ap = argparse.ArgumentParser(); ap.add_argument("book"); ap.add_argument("genre"); ap.add_argument("src", nargs="+")
ap.add_argument("--facts-only", action="store_true"); ap.add_argument("--sample", nargs="*", default=[]); a = ap.parse_args()
G = yaml.safe_load(open("/CODE/inkos/genre-kit/genres.yaml"))[a.genre]
src = "\n\n".join(open(p, encoding="utf-8").read() for p in a.src)[:60000]
sample = "\n\n".join(open(p, encoding="utf-8").read()[:6000] for p in a.sample)
def put(name, text):
    p = os.path.join(a.book, name); p = p + ".new" if os.path.exists(p) else p
    open(p, "w", encoding="utf-8").write(text); print("wrote", p)
if not a.facts_only:
    sb = mimo.chat("Bạn là tổng biên tập. Từ STORY BIBLE (và chương mẫu nếu có) hãy viết STYLE BIBLE khóa cho bộ truyện, tiếng Việt, gồm: "
      "YAML front matter giữa hai dòng --- với các khóa locked: true, genre, sub_genre, era, narration, register, banned (danh sách từ cấm phá bối cảnh), "
      f"llm_only (từ chỉ LLM xét theo ngữ cảnh, mặc định {G['llm_only']}), address_rules (map 'A → B': xưng hô), layout {{heading: 'Chương N: Tên chương', length_words: [min,max], scene_break: '* * *'}}; "
      "sau đó phần thân: lý do suy luận xưng hô (mỗi quy tắc một dòng lý do), văn phong, định dạng (thoại ngoặc kép thẳng, cấm dấu gạch dài), 2 đoạn mẫu giọng văn. "
      f"Mặc định thể loại: {G['label']}; register gợi ý: {G['register']}; banned gợi ý: {G['banned']}. Chỉ trả về file markdown.\n\nSTORY BIBLE:\n{src}\n\nCHƯƠNG MẪU:\n{sample}", max_tokens=12000)
    put("style-bible.md", sb.strip() + "\n")
r = mimo.chat_json("Từ tài liệu dưới đây, liệt kê các SỰ THẬT KHÓA (không được mâu thuẫn trong các chương sau): thể chất/năng lực cốt lõi, ai đã chết, thương tật vĩnh viễn, "
    "quan hệ huyết thống, quy luật thế giới bất biến, mốc thời gian. Mỗi mục: id kebab-case không dấu, entity, fact (1-2 câu tiếng Việt), since_chapter (số), "
    "forbid (0-3 regex Python an toàn, chỉ khi bắt được vi phạm rõ ràng, có thể rỗng), allow_if (cụm từ cho phép ngoại lệ). Trả về JSON {\"facts\":[...]}. Tối đa 25 mục.\n\n" + src + "\n\n" + sample)
facts = r.get("facts", []) if isinstance(r, dict) else r
put("locked_facts.yaml", yaml.safe_dump({"language": "vi", "facts": facts, "changes": []}, allow_unicode=True, sort_keys=False))
