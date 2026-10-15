---
name: novel-style-lock
description: When starting a new novel, before writing or reviewing any chapter, or when a plot event like rebirth or transmigration changes the setting - first reason out the setting's xưng hô system and forbidden forms of address (mandatory step 0), then define and lock the book's genre, voice, register and chapter layout in style-bible.md (locked true) and keep every chapter consistent with it.
---

# Novel style lock

Goal: the whole book reads as one consistent voice. A modern romance never slips into xianxia diction, and the reverse holds too. The lock changes only through an explicit, recorded plot shift such as rebirth, transmigration or a system awakening.


## 0. Mandatory pre-writing reasoning (before ANY line of story text)
Before writing, outlining prose, or building anything for a book, the AI must first think through the setting and write the conclusions into the style bible. This step is not optional and cannot be skipped, even for a "quick" chapter.
1. Infer the era, the world and the social register from the premise: ancient, xianxia or huyen huyen, modern, future, and so on.
2. Derive the **xung hô (forms of address) system** that fits that world. Do it per relationship type (family, master and disciple, lovers, superior and inferior, strangers, enemies) and per pair of key characters.
3. Derive the **forbidden xung hô and vocabulary** that would break immersion in this world. Reason it out; don't rely only on a fixed list. Examples:
   - Modern settings must never use huynh, muội, sư huynh, tại hạ, bản tọa, ngươi (as the plain word for "you"), nàng, chàng, công tử or tiểu thư (unless parody or roleplay is explicitly part of the plot). Use anh, chị, em, cậu, bạn, chú, thím and the like instead.
   - Xianxia and huyen huyen settings must never use chú, thím, dì, cậu, bạn, anh, em in the modern sense, or modern objects and slang. Use sư phụ, sư huynh, sư muội, đạo hữu, tiền bối, vãn bối, ta, ngươi, hắn, nàng, thúc thúc, thẩm thẩm and the like.
4. Put the reasoning in writing: for each rule, a one-line justification ("the setting is ancient cultivation, so modern kinship terms break immersion").
5. Only then lock the bible and start writing. The step 3 gate checks every chapter's xung hô against these rules, and any violation is rewritten.

## 1. Create the Style Bible (once, at the start of the book)
From the premise and the first outline, write `style-bible.md` (YAML front matter plus notes) in the book folder. Ask the author only for things you can't infer. It must cover:
- **Genre and sub-genre:** e.g. tiên hiệp, huyền huyễn, ngôn tình hiện đại, đô thị, cổ đại cung đấu, khoa huyễn. Also record the core trope or mô týp (phế vật nghịch thiên, hệ thống, điền văn, ngược, sủng...).
- **Era and setting register:** ancient, modern or future, and which world rules apply.
- **Narration:** point of view (first person or third, limited or omniscient), tense feel, and narrator distance.
- **Language register:**
  - The vocabulary family allowed. Ancient or xianxia uses Hán-Việt terms and forms of address (ta, ngươi, sư phụ, đạo hữu, tại hạ). Modern uses everyday Vietnamese (anh, em, tôi, cậu).
  - A banned list for this book: words, forms of address, slang and anachronisms that must never appear (e.g. no "điện thoại" or "OK" in xianxia; no "linh lực", "bản tọa" or "đạo hữu" in modern romance).
  - The rules for forms of address between each pair of key characters.
- **Prose style:** sentence length and rhythm, how much description versus dialogue, tone (hào hùng, ngọt, ngược, hài), how much humour, and how heat and violence are handled.
- **Dialogue formatting:** em dash or quotes, and how thoughts are marked.
- **Chapter layout:** heading format (`Chương N: Tên`), target length range, scene-break marker (`* * *`), opening/closing pattern (e.g. end on a hook), and whether notes or summaries are allowed (default: none in the story text).
- **Two or three short reference paragraphs** written in the locked voice, to use as a calibration sample.

Mark the bible `locked: true`. From then on it is the source of truth.

## 2. Before writing each chapter
Load the style bible and the most recent chapter. Put the genre, register, banned list, address rules and layout into the writing instructions. Write in that voice only.

## 3. After writing each chapter (gate)
Check the new chapter against the bible:
- Genre drift: does any passage read like another genre (modern slang in xianxia, cultivation terms in a modern romance)?
- Banned words or anachronisms, and wrong forms of address between characters.
- Point of view and narration consistency.
- Layout: the heading format, length range and scene breaks.
- Compare it with the calibration sample and the previous chapter: is it the same voice?

Rewrite only the offending passages, keeping the plot. Re-check until it passes, and record the result in the chapter log.

## 4. Allowed style changes (plot shifts only)
A style change is allowed only when the story itself changes world or identity: trùng sinh, xuyên không, xuyên sách, hệ thống thức tỉnh, or moving to a new realm or world. When that happens:
1. Append an **amendment** to the style bible: the chapter where it takes effect, the in-story cause, what changes (e.g. a modern soul in an ancient body: narration keeps modern inner thoughts while dialogue switches to ancient forms of address), and what stays the same.
2. Add any new genre tags; never silently replace the original genre.
3. Update the banned and allowed lists from that chapter onward. Earlier chapters keep their original rules.

No amendment means no change. Even if the author or the AI drifts, the gate enforces the lock.

## 5. Whole-book audit (before publishing or on request)
Run the step 3 checks across all chapters and report any chapters that drift from the bible (and its amendments). Fix them before publishing, together with the pre-publish character audit if one exists.

## Tooling on this box (inkos)
- `/CODE/inkos/novel.sh <book>` runs step 0 + creates `style-bible.md` if missing (`python3 /CODE/inkos/tools/stylegate.py init <book_dir>`), refuses to write if the bible or its `xung_ho` section is missing/invalid (`stylegate.py validate`), injects the bible into the write prompt and inkos's `story/style_guide.md`, and after each chapter runs the gate (banned-word + xưng hô grep, LLM drift check), rewriting only offending passages.
- Manual gate: `python3 /CODE/inkos/tools/stylegate.py check <book_dir> <chapter.md>` (exit 2 = drift); `fix` = check + rewrite + re-check (log: `style-gate-log.jsonl`).
- Amendments: append to `amendments:` in the bible front matter (`from_chapter`, `cause`, `changes`, `add_banned`, `remove_banned`, `add_tags`). No amendment, no change.
