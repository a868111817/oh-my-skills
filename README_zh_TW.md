# Oh My Skills

個人 Claude Code Skills 收藏庫，存放自製的 Claude Code skill，讓日常工作流程更自動化。

## 專案結構

```
oh-my-skills/
├── skills/                    # 所有 skills 存放處
│   ├── fetch-paper/           # arXiv 論文搜尋 skill
│   │   ├── SKILL.md           # Skill 定義與使用說明
│   │   └── fetch_paper.py
│   └── youtube-transcript/    # YouTube 字幕擷取與摘要 skill
│       ├── SKILL.md
│       ├── scripts/
│       │   └── fetch_transcript.py
│       └── evals/
│           └── evals.json
├── video/                     # youtube-transcript 輸出目錄
├── outputs/                   # fetch-paper 輸出目錄
└── README.md
```

## 安裝 Skills

將 skill 資料夾複製到 Claude Code 的 skills 目錄，重啟後即可使用：

```bash
cp -r skills/<skill-name> ~/.claude/skills/<skill-name>
```

## Skills 清單

| Skill | 說明 | 觸發方式 | 輸出目錄 |
|-------|------|----------|----------|
| [fetch-paper](./skills/fetch-paper/SKILL.md) | 搜尋 arXiv 論文並輸出繁體中文摘要 Markdown | 「幫我找 XXX 論文」、「搜尋論文」 | `outputs/YYYYMMDD_<關鍵字>.md` |
| [youtube-transcript](./skills/youtube-transcript/SKILL.md) | 用 yt-dlp 擷取 YouTube 字幕、翻譯外文為繁體中文，並自動摘要整部影片 | YouTube 連結 / 「幫我抓字幕」、「transcript」 | `video/YYYY-MM-DD_<標題>.md` |
