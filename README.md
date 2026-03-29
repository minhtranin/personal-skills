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
| `/ps:bot-telegram` | Set up Telegram bot to chat with Claude from your phone |
| `/ps:tube-summary <youtube-url>` | Summarize a YouTube video |
| `/ps:medium-summary <medium-url>` | Summarize a Medium article |
| `/ps:jira-summary <PROJ-123>` | Summarize a Jira issue + comments |
| `/ps:jira-plantask <PROJ-123>` | Plan implementation, break into subtasks, create in Jira |
| `/ps:slack-summary <thread-url>` | Summarize a Slack thread |
| `/ps:slack-answer <thread-url>` | Research codebase, draft reply, ask confirmation |
| `/ps:slack_post <channel> <message>` | Post new message to any Slack channel/DM |
| `/ps:excalidraw <description>` | Generate diagram and render to PNG |
| `/ps:web` | Browse all history in a local web UI |

### Telegram Bot Commands

When running the bot, you can use these from Telegram:

| Command | Description |
|---|---|
| `/lookup` | Ask questions about your codebase |
| `/slack_summary <thread-url>` | Summarize a Slack thread |
| `/slack_answer <thread-url>` | Answer a Slack thread with codebase research |
| `/slack_post <channel> <message>` | Post to Slack |
| `/adddir <path>` | Add a directory to search context |
| `/listdirs` | List all directories |
| `/removedir <path>` | Remove a directory |
| `/cwd` | Show current working directory |
| `/provider <name>` | Switch AI provider (anthropic/minimax/zai) |

All summaries are cached locally — re-running the same URL returns instantly. Pass `--refresh` to re-fetch.

## Requirements

- `curl` + `python3`
- Telegram bot: run `/ps:bot-telegram` for setup wizard
- Jira skills: `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_URL` env vars
- Slack skills: tokens stored automatically

## Multi-Provider Support

The Telegram bot supports multiple AI providers:

- **Anthropic** (default) — Claude models
- **MiniMax** — Use `ccm` in fish shell to get API key
- **ZAI** — Use `ccz` in fish shell to get API key

Switch providers with `/provider minimax` or `/provider zai` in Telegram.
