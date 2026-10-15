---
name: novel-prepublish-audit
description: >-
  Before publishing or deploying Vietnamese novel chapters to a website, scan ALL
  chapters and book metadata for invalid characters (Chinese/Han, CJK punctuation,
  emoji/icons, odd symbols, other scripts, zero-width/control chars, mojibake),
  understand each hit from context, replace it with correct Vietnamese (Han-Viet for
  names and terms), then re-verify before deploy. Unclear hits block the publish.
---
# Novel pre-publish audit

Run this on every publish/deploy of novel content, over ALL chapters, not just the new one. Content must be pure Vietnamese.

## 1. Scan
Scan every chapter file and the book metadata (title, synopsis, tags) for:
- Han/CJK characters: `\p{Script=Han}`, CJK punctuation (。，、《》「」【】：；！？), fullwidth forms `\uFF00-\uFFEF`
- Other non-Vietnamese scripts: Hiragana, Katakana, Hangul, Cyrillic, etc.
- Emoji and pictographs: `\p{Extended_Pictographic}`, variation selectors, ZWJ
- Odd symbols such as ★☆◆■→←✦❖※§¶, box drawing, and stray markdown/HTML artefacts
- Invisible or control characters: zero-width chars, BOM, `\p{Cc}` other than newline/tab
- Mojibake (Ã¡, â€™, �) and broken Vietnamese diacritics (combining marks left unnormalized; normalize to NFC)

Allowed characters: Vietnamese Latin letters with diacritics, digits, normal punctuation (. , ; : ! ? … " " ' ' ( ) - – —), whitespace, and markdown headings.

Output a report: file, line, the character(s), and about 40 characters of context on each side.

## 2. Understand and fix (do not just delete)
For each hit, read the surrounding passage and decide what was meant:
- Chinese names, 法宝, realms, sects or terms: convert them to Hán-Việt consistent with the story's existing naming. Check the book's character and setting records first, so an entity keeps one spelling across the whole book (e.g. 筑基 becomes Trúc Cơ, 青冥剑 becomes Thanh Minh Kiếm).
- Chinese phrases or sentences: translate them into natural Vietnamese prose in the same tone.
- CJK punctuation: replace with the Vietnamese equivalent (。 becomes ., 《》 become " ").
- Emoji or icons: remove them, or turn them into words if they carried meaning (e.g. a sword icon becomes "thanh kiếm" if it stood for an object).
- Decorative symbols used as scene breaks: replace them with a single standard break (`* * *`).
- Mojibake: restore the intended Vietnamese word from context.
- If the meaning truly cannot be determined, do not guess. Flag it in the report and block the publish of that chapter.

Edit the source chapter files (the canonical source), not just the published copy, so that later syncs don't bring the problem back.

## 3. Re-verify
Re-run the scan over all chapters. The result must be 0 hits. Then run the site's build and its content checks (e.g. a no-CJK check on the built output). Deploy only if everything passes.

## 4. Report
List each fix (file, before, after, reason) and any blocked chapters.

## Tooling in oaichu-novels (xemtruyen.io.vn)
- `npm run audit:content` (`scripts/audit-content.mjs [paths...]`): file:line, kind, chars, code points, context; exit 1 on any hit. Run it on the inkos source too: `node scripts/audit-content.mjs /CODE/inkos-books`.
- `npm run sync:inkos` runs with `--strict-vi`: chapters or metadata with hits are refused (exit 1).
- `npm run build` = audit:content, astro check, astro build, check:no-cjk (Han/emoji/CJK punctuation in src/, public/, dist/). `npm run deploy` runs build first, so a dirty site cannot ship.
