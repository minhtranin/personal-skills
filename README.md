# personal-skills

Personal productivity skills for Claude Code, Antigravity, and OpenCode.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/minhtranin/personal-skills/main/install.sh | bash
```

Update anytime:

```bash
curl -fsSL https://raw.githubusercontent.com/minhtranin/personal-skills/main/install.sh | bash -s -- --update
```

## Skills

| Command | Description |
|---|---|
| `/ps-tube-summary <youtube-url>` | Summarize a YouTube video |
| `/ps-medium-summary <medium-url>` | Summarize a Medium article |
| `/ps-jira-summary <PROJ-123>` | Summarize a Jira issue + comments |
| `/ps-jira-plantask <PROJ-123>` | Plan implementation, break into subtasks, create in Jira |
| `/ps-slack-login` | Save Slack session tokens |
| `/ps-slack-summary <thread-url>` | Summarize a Slack thread |
| `/ps-web` | Browse all history in a local web UI |

All summaries are cached locally — re-running the same URL returns instantly. Pass `--refresh` to re-fetch.

## Requirements

- `curl` + `python3`
- Jira skills: `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_URL` env vars
- Slack skills: run `/ps-slack-login` first
