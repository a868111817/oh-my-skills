# Oh My Skills

A personal collection of Claude Code Skills to automate everyday workflows.

## Project Structure

```
oh-my-skills/
├── skills/               # All skills
│   └── fetch-paper/      # arXiv paper search skill
│       ├── SKILL.md      # Skill definition and instructions
│       └── fetch_paper.py
├── outputs/              # Output directory for skill results
└── README.md
```

## Installing Skills

Copy a skill folder to Claude Code's skills directory and restart:

```bash
cp -r skills/<skill-name> ~/.claude/skills/<skill-name>
```

## Skills List

| Skill | Description | Trigger |
|-------|-------------|---------|
| [fetch-paper](./skills/fetch-paper/SKILL.md) | Search arXiv papers and output Traditional Chinese summaries as Markdown | "find papers on XXX", "search papers" |

## Output Format

Results are saved to the `outputs/` directory with the naming convention:

```
outputs/YYYYMMDD_<keyword>.md
```
