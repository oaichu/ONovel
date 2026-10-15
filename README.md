# ONovel — hệ thống viết tiểu thuyết

Backup công khai của tooling viết tiểu thuyết (không gồm nội dung sách).

## Cấu trúc

```
inkos/                 # CLI wrapper + tools + genre-kit
  novel.sh, loop-book.sh, review-books.sh, run-inkos.sh
  tools/               # Python/shell helpers (mimo, stylegate, lockcheck, …)
  genre-kit/           # skills, cards, genres.yaml, build/, licenses, ATTRIBUTION.md
novel-skills/          # bộ skill viết/biên tập tiểu thuyết
lessons-library/       # thư viện bài học (global/domain)
RECOVERY.md            # ghi chú phục hồi /CODE (2026-10-15)
```

**Không có trong repo:** nội dung sách (`inkos-books`), website, clone vendor (`genre-kit/vendor`), `runs/`, `.env`, và secret.

## API keys

Script chỉ đọc key từ biến môi trường (`BAI_API_KEY`, `INKOS_LLM_API_KEY`, …). Không commit giá trị secret. Ví dụ:

```bash
export BAI_API_KEY=...   # trong ~/.profile hoặc shell hiện tại
/CODE/inkos/run-inkos.sh --help
```

## Đồng bộ lại từ /CODE

```bash
/CODE/inkos/tools/sync-onovel.sh
```

Script copy theo cùng quy tắc loại trừ, rồi commit + push `main` nếu có thay đổi.

## License / attribution

Xem `inkos/genre-kit/ATTRIBUTION.md` và `inkos/genre-kit/licenses/`.
