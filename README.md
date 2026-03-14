# Oh My Skills

A personal collection of Claude Code Skills to automate everyday workflows.

## Project Structure

```
oh-my-skills/
├── skills/                    # All skills
│   ├── fetch-paper/           # arXiv paper search skill
│   │   ├── SKILL.md
│   │   └── fetch_paper.py
│   └── youtube-transcript/    # YouTube transcript & summary skill
│       ├── SKILL.md
│       ├── scripts/
│       │   └── fetch_transcript.py
│       └── evals/
│           └── evals.json
├── video/                     # Output directory for youtube-transcript
├── outputs/                   # Output directory for fetch-paper
└── README.md
```

## Installing Skills

Copy a skill folder to Claude Code's skills directory and restart:

```bash
cp -r skills/<skill-name> ~/.claude/skills/<skill-name>
```

## Skills List

| Skill | Description | Trigger | Output |
|-------|-------------|---------|--------|
| [fetch-paper](./skills/fetch-paper/SKILL.md) | Search arXiv papers and output Traditional Chinese summaries as Markdown | "find papers on XXX", "search papers" | `outputs/YYYYMMDD_<keyword>.md` |
| [youtube-transcript](./skills/youtube-transcript/SKILL.md) | Fetch YouTube subtitles via yt-dlp, translate foreign content to Traditional Chinese, and generate a video summary | YouTube URL / "幫我抓字幕", "transcript" | `video/YYYY-MM-DD_<title>.md` |
