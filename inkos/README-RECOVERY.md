# /CODE rebuild, 2026-10-15 (ICT)
/CODE is a symlink to /workspace/CODE (persisted). ~/.bashrc and ~/.profile recreate it with `sudo -n ln -sfn` when missing.
- oaichu-novels: fresh clone of oaichu/Xem-Truyen (origin only). Local-only untracked: public/covers/tuc-the.jpg (not committed).
  Lost local untracked scripts: scripts/publish-tien-tro.sh, /CODE/novel-skills/editor/editor-review.sh (used by scripts/publish.sh).
- inkos: CLI is the global npm @actalk/inkos@1.8.0 (survived in ~/.local/lib). All scripts in /CODE/inkos were REWRITTEN except
  tools/fix.py (recovered from /workspace/mimo-fix/fix.py).
- novel-skills/skills: 4 house skills recovered from pi session logs; 10 ported from zenstory-ai/oh-story-claudecode.
- lessons-library: rewritten; seeded from ~/.pi/agent/AGENTS.md.
- inkos-books/xemtruyen: re-created books; inkos-books/dryrun-test is a throwaway copy for novel.sh dry runs.
