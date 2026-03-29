#!/usr/bin/env python3
"""
personal-skills Telegram bot — chat with Claude Code from your phone.

Supports multiple AI providers via /provider command:
  - anthropic  : Anthropic API (default, requires ANTHROPIC_API_KEY)
  - minimax    : MiniMax via Anthropic-compatible API
  - zai        : ZAI/GLM via Anthropic-compatible API

Usage:
  python3 telegram_bot.py --token <TELEGRAM_BOT_TOKEN> --user-id <YOUR_TELEGRAM_USER_ID>

Or set env vars:
  TELEGRAM_BOT_TOKEN=...
  TELEGRAM_ALLOWED_USER_ID=...
"""

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
import traceback
from pathlib import Path

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
    from telegram.constants import ChatAction
except ImportError:
    print("ERROR: python-telegram-bot not installed.")
    print("Run: pip3 install 'python-telegram-bot>=20.0'")
    sys.exit(2)

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic SDK not installed.")
    print("Run: pip3 install anthropic")
    sys.exit(2)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SCRIPTS_DIR = Path.home() / ".local/share/personal-skills/scripts"
CONFIG_FILE  = Path.home() / ".local/share/personal-skills/bot-config.json"

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# In-memory conversation history per chat
conversation_history: dict[int, list[dict]] = {}

# Active provider per chat (defaults to config default)
active_provider: dict[int, str] = {}

# ---------------------------------------------------------------------------
# Provider definitions
# ---------------------------------------------------------------------------

PROVIDERS = {
    "anthropic": {
        "label":    "Anthropic (Claude)",
        "base_url": None,  # uses default
        "env_key":  "ANTHROPIC_API_KEY",
        "models": {
            "haiku":  "claude-haiku-4-5-20251001",
            "sonnet": "claude-sonnet-4-6",
            "opus":   "claude-opus-4-6",
        },
        "default_model": "sonnet",
    },
    "minimax": {
        "label":    "MiniMax (M2.7)",
        "base_url": "https://api.minimax.io/anthropic",
        "env_key":  "MINIMAX_API_KEY",
        "models": {
            "haiku":  "MiniMax-M2.7",
            "sonnet": "MiniMax-M2.7",
            "opus":   "MiniMax-M2.7",
        },
        "default_model": "sonnet",
    },
    "zai": {
        "label":    "ZAI / GLM",
        "base_url": "https://api.z.ai/api/anthropic",
        "env_key":  "ZAI_API_KEY",
        "models": {
            "haiku":  "glm-4.5-air",
            "sonnet": "glm-4.7",
            "opus":   "glm-5",
        },
        "default_model": "sonnet",
    },
}

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

def build_system_prompt(dirs: list[dict]) -> str:
    if dirs:
        dirs_text = "\n".join(
            f"  - {d['path']}" + (f" ({d['label']})" if d.get('label') else "")
            for d in dirs
        )
        dirs_section = f"\nThe user has added these codebase/knowledge directories:\n{dirs_text}\n\nWhen searching code or looking up knowledge, search ALL of these directories."
    else:
        dirs_section = ""

    return f"""You are a personal assistant with access to the user's personal-skills toolkit.
You can help with:
- Summarizing Slack threads
- Answering Slack threads by researching the codebase
- Summarizing YouTube videos
- Summarizing Medium articles
- Summarizing Jira issues
- Running shell commands when needed
{dirs_section}

When the user gives you a Slack/YouTube/Medium/Jira URL, use the run_script tool
to execute the relevant Python script under ~/.local/share/personal-skills/scripts/.

When the user asks to "lookup the codebase", "search code", or asks about implementation,
use run_script to run grep, find, or cat commands against the directories listed above.

Be concise and conversational — this is a mobile chat interface.
For long outputs, summarize key points first, then offer details.
"""

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "run_script",
        "description": "Run a personal-skills Python script or shell command and return its output.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The full shell command to run."
                }
            },
            "required": ["command"]
        }
    }
]


def run_tool(command: str) -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ, "HOME": str(Path.home())},
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]: {result.stderr[:500]}"
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "ERROR: Command timed out after 120s"
    except Exception as e:
        return f"ERROR: {e}"


# ---------------------------------------------------------------------------
# AI client builder
# ---------------------------------------------------------------------------

def build_client(provider_name: str, config: dict) -> tuple[anthropic.Anthropic, str]:
    """Returns (client, model_name) for the given provider."""
    provider = PROVIDERS[provider_name]

    # Resolve API key: config file → env var
    api_key = (
        config.get("providers", {}).get(provider_name, {}).get("api_key")
        or os.environ.get(provider["env_key"])
        or os.environ.get("ANTHROPIC_API_KEY")  # fallback
    )

    if not api_key:
        raise ValueError(
            f"No API key for provider '{provider_name}'. "
            f"Set {provider['env_key']} in bot-config.json or environment."
        )

    kwargs = {"api_key": api_key}
    if provider["base_url"]:
        kwargs["base_url"] = provider["base_url"]

    client = anthropic.Anthropic(**kwargs)
    model  = provider["models"][provider["default_model"]]
    return client, model


CODEBASE_KEYWORDS = (
    "codebase", "lookup", "source code", "search code", "find in code",
    "grep", "repo", "repository", "source", "implementation", "where is",
    "which file", "find the", "look at the code",
)

def looks_like_codebase_query(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in CODEBASE_KEYWORDS)


async def ask_ai(chat_id: int, user_message: str, config: dict) -> str:
    provider_name = active_provider.get(chat_id, config.get("default_provider", "anthropic"))

    try:
        client, model = build_client(provider_name, config)
    except ValueError as e:
        return f"❌ Provider error: {e}"

    dirs = config.get("dirs", [])
    # migrate legacy single cwd
    if not dirs and config.get("cwd"):
        dirs = [{"path": config["cwd"]}]

    # Warn early if codebase query but no directory set
    if looks_like_codebase_query(user_message) and not dirs:
        return (
            "⚠️ No codebase/knowledge directory added.\n\n"
            "Use `/adddir /path/to/repo` to add one, then try again.\n\n"
            "Example:\n`/adddir /home/minhcongtran/workspace/grapple/grapple-plus-api`\n\n"
            "Add multiple with optional labels:\n"
            "`/adddir /path/to/repo My API`"
        )

    system_prompt = build_system_prompt(dirs)

    history = conversation_history.setdefault(chat_id, [])
    history.append({"role": "user", "content": user_message})
    if len(history) > 20:
        history[:] = history[-20:]

    messages = list(history)

    for _ in range(10):
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )

        text_parts = [b.text for b in response.content if hasattr(b, "text")]

        if response.stop_reason == "end_turn":
            final_text = "\n".join(text_parts).strip()
            history.append({"role": "assistant", "content": response.content})
            return final_text or "(done)"

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    logger.info(f"Tool: {block.name}({block.input})")
                    out = run_tool(block.input["command"])
                    logger.info(f"Output: {out[:200]}")
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     out,
                    })
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user",      "content": tool_results})
            continue

        break

    return f"Sorry, unexpected stop_reason: {response.stop_reason}"


# ---------------------------------------------------------------------------
# Telegram handlers
# ---------------------------------------------------------------------------

def make_allowed_filter(user_id: int):
    return filters.User(user_id=user_id)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = context.bot_data.get("config", {})
    current = active_provider.get(
        update.effective_chat.id,
        config.get("default_provider", "anthropic")
    )
    provider_label = PROVIDERS.get(current, {}).get("label", current)
    dirs  = config.get("dirs", [])
    if not dirs and config.get("cwd"):
        dirs = [{"path": config["cwd"]}]
    dirs_text = f"{len(dirs)} director{'y' if len(dirs)==1 else 'ies'}" if dirs else "none"
    await update.message.reply_text(
        "👋 *personal-skills bot*\n\n"
        f"Provider: *{provider_label}* · Dirs: {dirs_text}\n\n"
        "*ps: skills*\n"
        "`/slack_summary <url>` — summarize Slack thread\n"
        "`/slack_answer <url>` — research + draft reply\n"
        "`/tube_summary <url>` — summarize YouTube video\n"
        "`/medium_summary <url>` — summarize Medium article\n"
        "`/jira_summary <KEY>` — summarize Jira issue\n"
        "`/jira_plantask <KEY>` — plan + break into subtasks\n"
        "`/excalidraw <desc>` — generate diagram\n"
        "`/web` — launch history web UI\n\n"
        "*Directories*\n"
        "`/adddir /path [label]` — add codebase/knowledge dir\n"
        "`/listdirs` — list all directories\n"
        "`/removedir <n>` — remove directory by number\n\n"
        "*Settings*\n"
        "`/provider` — switch AI provider\n"
        "`/clear` — reset conversation\n\n"
        "Or just send any message to chat freely.",
        parse_mode="Markdown"
    )


async def clear_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conversation_history.pop(update.effective_chat.id, None)
    await update.message.reply_text("🗑️ Conversation cleared.")


async def provider_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config  = context.bot_data.get("config", {})
    current = active_provider.get(
        update.effective_chat.id,
        config.get("default_provider", "anthropic")
    )

    keyboard = []
    for key, p in PROVIDERS.items():
        label = p["label"]
        if key == current:
            label = f"✓ {label}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"provider:{key}")])

    await update.message.reply_text(
        "Select AI provider:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def provider_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    provider_name = query.data.split(":", 1)[1]
    if provider_name not in PROVIDERS:
        await query.edit_message_text("Unknown provider.")
        return

    chat_id = query.message.chat_id
    active_provider[chat_id] = provider_name
    label = PROVIDERS[provider_name]["label"]

    # Clear history when switching provider (different context/format)
    conversation_history.pop(chat_id, None)

    await query.edit_message_text(
        f"✓ Switched to *{label}*\nConversation cleared.",
        parse_mode="Markdown"
    )


async def adddir_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config    = context.bot_data.get("config", {})
    args_text = " ".join(context.args).strip() if context.args else ""

    if not args_text:
        await update.message.reply_text(
            "Usage: `/adddir /path/to/repo [optional label]`\n\n"
            "Examples:\n"
            "`/adddir /home/minhcongtran/workspace/grapple/grapple-plus-api`\n"
            "`/adddir /home/minhcongtran/workspace/grapple/grapple-frontend Frontend`\n"
            "`/adddir /home/minhcongtran/docs/knowledge Knowledge Base`",
            parse_mode="Markdown"
        )
        return

    # Split: first token is path, rest is label
    parts = args_text.split(None, 1)
    raw_path = parts[0]
    label    = parts[1] if len(parts) > 1 else ""

    path = Path(raw_path).expanduser()
    if not path.exists():
        await update.message.reply_text(f"❌ Path does not exist: `{raw_path}`", parse_mode="Markdown")
        return

    dirs = config.get("dirs", [])
    # migrate legacy cwd
    if not dirs and config.get("cwd"):
        dirs = [{"path": config["cwd"]}]
        del config["cwd"]

    # Avoid duplicates
    path_str = str(path)
    if any(d["path"] == path_str for d in dirs):
        await update.message.reply_text(f"Already added: `{path_str}`", parse_mode="Markdown")
        return

    entry = {"path": path_str}
    if label:
        entry["label"] = label
    dirs.append(entry)
    config["dirs"] = dirs
    save_config(config)

    label_part = f" *({label})*" if label else ""
    await update.message.reply_text(
        f"✓ Added{label_part}:\n`{path_str}`\n\nTotal directories: {len(dirs)}",
        parse_mode="Markdown"
    )


async def listdirs_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = context.bot_data.get("config", {})
    dirs   = config.get("dirs", [])
    if not dirs and config.get("cwd"):
        dirs = [{"path": config["cwd"]}]

    if not dirs:
        await update.message.reply_text(
            "No directories added yet.\nUse `/adddir /path/to/repo` to add one.",
            parse_mode="Markdown"
        )
        return

    lines = ["*Codebase/knowledge directories:*\n"]
    for i, d in enumerate(dirs, 1):
        label = f" — {d['label']}" if d.get("label") else ""
        lines.append(f"{i}. `{d['path']}`{label}")
    lines.append(f"\nUse `/removedir <number>` to remove one.")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def removedir_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config    = context.bot_data.get("config", {})
    args_text = " ".join(context.args).strip() if context.args else ""
    dirs      = config.get("dirs", [])
    if not dirs and config.get("cwd"):
        dirs = [{"path": config["cwd"]}]
        del config["cwd"]

    if not args_text:
        await update.message.reply_text(
            "Usage: `/removedir <number>`\nRun `/listdirs` to see numbers.",
            parse_mode="Markdown"
        )
        return

    try:
        idx = int(args_text) - 1
        if idx < 0 or idx >= len(dirs):
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            f"❌ Invalid number. Run `/listdirs` to see valid numbers.",
            parse_mode="Markdown"
        )
        return

    removed = dirs.pop(idx)
    config["dirs"] = dirs
    save_config(config)
    await update.message.reply_text(
        f"✓ Removed: `{removed['path']}`\nRemaining: {len(dirs)} director{'y' if len(dirs)==1 else 'ies'}",
        parse_mode="Markdown"
    )


# ---------------------------------------------------------------------------
# ps: skill handlers — each maps to a direct prompt to Claude
# ---------------------------------------------------------------------------

PS_COMMANDS = {
    "slack_summary": {
        "cmd":   "slack_summary",
        "usage": "/slack_summary <slack-thread-url>",
        "desc":  "Summarize a Slack thread",
        "prompt": "Summarize this Slack thread: {args}",
    },
    "slack_answer": {
        "cmd":   "slack_answer",
        "usage": "/slack_answer <slack-thread-url>",
        "desc":  "Research codebase and draft a reply to a Slack thread",
        "prompt": "Answer this Slack thread by researching the codebase: {args}",
    },
    "tube_summary": {
        "cmd":   "tube_summary",
        "usage": "/tube_summary <youtube-url>",
        "desc":  "Summarize a YouTube video",
        "prompt": "Summarize this YouTube video: {args}",
    },
    "medium_summary": {
        "cmd":   "medium_summary",
        "usage": "/medium_summary <medium-url>",
        "desc":  "Summarize a Medium article",
        "prompt": "Summarize this Medium article: {args}",
    },
    "jira_summary": {
        "cmd":   "jira_summary",
        "usage": "/jira_summary <PROJ-123 or jira-url>",
        "desc":  "Summarize a Jira issue",
        "prompt": "Summarize this Jira issue: {args}",
    },
    "jira_plantask": {
        "cmd":   "jira_plantask",
        "usage": "/jira_plantask <PROJ-123>",
        "desc":  "Plan and break a Jira issue into subtasks",
        "prompt": "Plan and break this Jira issue into implementation subtasks: {args}",
    },
    "excalidraw": {
        "cmd":   "excalidraw",
        "usage": "/excalidraw <description>",
        "desc":  "Generate an Excalidraw diagram from a description",
        "prompt": "Generate an Excalidraw diagram for: {args}",
    },
    "web": {
        "cmd":   "web",
        "usage": "/web",
        "desc":  "Launch the personal-skills history web UI",
        "prompt": "Launch the personal-skills web UI history server",
    },
}


def make_ps_handler(skill: dict):
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        args_text = " ".join(context.args).strip() if context.args else ""
        config    = context.bot_data.get("config", {})
        chat_id   = update.effective_chat.id

        if not args_text and skill["cmd"] != "web":
            await update.message.reply_text(
                f"Usage: `{skill['usage']}`",
                parse_mode="Markdown"
            )
            return

        prompt = skill["prompt"].format(args=args_text)
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        try:
            reply = await ask_ai(chat_id, prompt, config)
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"AI error: {tb}")
            reply = f"❌ Error: {e}\n\n```\n{tb[-800:]}\n```"

        if len(reply) <= 4096:
            await update.message.reply_text(reply)
        else:
            for chunk in [reply[i:i+4000] for i in range(0, len(reply), 4000)]:
                await update.message.reply_text(chunk)
                await asyncio.sleep(0.3)

    return handler


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id   = update.effective_chat.id
    user_text = update.message.text.strip()
    config    = context.bot_data.get("config", {})

    if not user_text:
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        reply = await ask_ai(chat_id, user_text, config)
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"AI error: {tb}")
        reply = f"❌ Error: {e}\n\n```\n{tb[-800:]}\n```"

    if len(reply) <= 4096:
        await update.message.reply_text(reply)
    else:
        for chunk in [reply[i:i+4000] for i in range(0, len(reply), 4000)]:
            await update.message.reply_text(chunk)
            await asyncio.sleep(0.3)


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(data: dict):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, indent=2))
    CONFIG_FILE.chmod(0o600)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token",            help="Telegram bot token")
    parser.add_argument("--user-id",          type=int, help="Your Telegram user ID")
    parser.add_argument("--setup",            action="store_true", help="Save config and exit")
    parser.add_argument("--default-provider", default=None,
                        choices=list(PROVIDERS.keys()),
                        help="Default AI provider (anthropic/minimax/zai)")
    parser.add_argument("--minimax-key",      help="MiniMax API key")
    parser.add_argument("--zai-key",          help="ZAI API key")
    parser.add_argument("--anthropic-key",    help="Anthropic API key")
    parser.add_argument("--add-dir",          action="append", metavar="PATH[:LABEL]",
                        help="Add a codebase/knowledge directory (repeatable)")
    args = parser.parse_args()

    config = load_config()

    token   = args.token   or config.get("token")   or os.environ.get("TELEGRAM_BOT_TOKEN")
    user_id = args.user_id or config.get("user_id") or os.environ.get("TELEGRAM_ALLOWED_USER_ID")

    if not token:
        print("ERROR: No Telegram bot token. Run with --token <TOKEN> --user-id <ID> --setup")
        sys.exit(1)
    if not user_id:
        print("ERROR: No user ID. Run with --token <TOKEN> --user-id <ID> --setup")
        sys.exit(1)

    user_id = int(user_id)

    if args.setup:
        config["token"]   = token
        config["user_id"] = user_id

        if args.default_provider:
            config["default_provider"] = args.default_provider
        if args.add_dir:
            dirs = config.get("dirs", [])
            for entry in args.add_dir:
                parts    = entry.split(":", 1)
                path_str = str(Path(parts[0]).expanduser())
                label    = parts[1] if len(parts) > 1 else ""
                if not any(d["path"] == path_str for d in dirs):
                    d = {"path": path_str}
                    if label:
                        d["label"] = label
                    dirs.append(d)
            config["dirs"] = dirs

        # Store provider API keys
        providers_cfg = config.setdefault("providers", {})
        if args.anthropic_key:
            providers_cfg.setdefault("anthropic", {})["api_key"] = args.anthropic_key
        if args.minimax_key:
            providers_cfg.setdefault("minimax", {})["api_key"] = args.minimax_key
        if args.zai_key:
            providers_cfg.setdefault("zai", {})["api_key"] = args.zai_key

        save_config(config)
        print(f"✓ Config saved to {CONFIG_FILE}")
        print(f"  Token           : {token[:12]}...")
        print(f"  User ID         : {user_id}")
        print(f"  Default provider: {config.get('default_provider', 'anthropic')}")
        for p, v in config.get("providers", {}).items():
            key = v.get("api_key", "")
            print(f"  {p} key       : {key[:12]}..." if key else f"  {p} key       : (not set)")
        print("\nStart the bot:")
        print("  python3 telegram_bot.py")
        return

    logger.info(f"Starting bot — user ID {user_id}, default provider: {config.get('default_provider', 'anthropic')}")

    app = Application.builder().token(token).build()
    app.bot_data["config"] = config

    user_filter = make_allowed_filter(user_id)

    app.add_handler(CommandHandler("start",    start_handler,    filters=user_filter))
    app.add_handler(CommandHandler("help",     start_handler,    filters=user_filter))
    app.add_handler(CommandHandler("clear",     clear_handler,     filters=user_filter))
    app.add_handler(CommandHandler("provider",  provider_handler,  filters=user_filter))
    app.add_handler(CommandHandler("adddir",    adddir_handler,    filters=user_filter))
    app.add_handler(CommandHandler("listdirs",  listdirs_handler,  filters=user_filter))
    app.add_handler(CommandHandler("removedir", removedir_handler, filters=user_filter))

    # Register all ps: skill commands
    for skill in PS_COMMANDS.values():
        app.add_handler(CommandHandler(skill["cmd"], make_ps_handler(skill), filters=user_filter))

    app.add_handler(CallbackQueryHandler(provider_callback, pattern="^provider:"))
    app.add_handler(MessageHandler(filters.TEXT & user_filter, message_handler))

    # Register command list with BotFather so they show in autocomplete
    async def set_bot_commands(app):
        from telegram import BotCommand
        commands = [
            BotCommand("start",          "Show welcome message"),
            BotCommand("help",           "Show help"),
            BotCommand("clear",          "Reset conversation history"),
            BotCommand("provider",       "Switch AI provider (MiniMax/ZAI/Anthropic)"),
            BotCommand("adddir",         "Add a codebase or knowledge directory"),
            BotCommand("listdirs",       "List all added directories"),
            BotCommand("removedir",      "Remove a directory by number"),
            BotCommand("slack_summary",  "Summarize a Slack thread"),
            BotCommand("slack_answer",   "Research codebase and draft Slack reply"),
            BotCommand("tube_summary",   "Summarize a YouTube video"),
            BotCommand("medium_summary", "Summarize a Medium article"),
            BotCommand("jira_summary",   "Summarize a Jira issue"),
            BotCommand("jira_plantask",  "Plan & break a Jira issue into subtasks"),
            BotCommand("excalidraw",     "Generate an Excalidraw diagram"),
            BotCommand("web",            "Launch history web UI"),
        ]
        await app.bot.set_my_commands(commands)
        logger.info(f"Registered {len(commands)} bot commands with BotFather")

    app.post_init = set_bot_commands

    logger.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
