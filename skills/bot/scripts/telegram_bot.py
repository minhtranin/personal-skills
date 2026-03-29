#!/usr/bin/env python3
"""
personal-skills Telegram bot — chat with Claude Code from your phone.

Features:
  - Runs any ps: command by mentioning it: "slack-answer <url>"
  - Conversational: multi-turn chat with Claude (streaming)
  - Secure: only responds to your Telegram user ID
  - Runs ps: scripts directly, or passes freeform prompts to Claude SDK

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
from pathlib import Path

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
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
CONFIG_FILE = Path.home() / ".local/share/personal-skills/bot-config.json"

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# In-memory conversation history per chat
conversation_history: dict[int, list[dict]] = {}

SYSTEM_PROMPT = """You are a personal assistant with access to the user's personal-skills toolkit.
You can help with:
- Summarizing Slack threads (/ps:slack-summary)
- Answering Slack threads by researching the codebase (/ps:slack-answer)
- Summarizing YouTube videos (/ps:tube-summary)
- Summarizing Medium articles (/ps:medium-summary)
- Summarizing Jira issues (/ps:jira-summary)
- Running shell commands when needed

When the user gives you a Slack/YouTube/Medium/Jira URL or asks to run a ps: command,
use the run_script tool to execute the relevant Python script directly.

Be concise and conversational — this is a mobile chat interface.
For long outputs, summarize key points first, then offer details.
"""

# ---------------------------------------------------------------------------
# Tools for Claude
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
                    "description": "The full shell command to run, e.g. 'python3 ~/.local/share/personal-skills/scripts/slack/fetch_slack_thread.py <url>'"
                }
            },
            "required": ["command"]
        }
    }
]


def run_tool(command: str) -> str:
    """Execute a shell command and return stdout+stderr."""
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


async def ask_claude(chat_id: int, user_message: str) -> str:
    """Send message to Claude with tool use loop, return final text response."""
    client = anthropic.Anthropic()

    history = conversation_history.setdefault(chat_id, [])
    history.append({"role": "user", "content": user_message})

    # Keep last 20 turns to avoid token bloat
    if len(history) > 20:
        history[:] = history[-20:]

    messages = list(history)

    for _ in range(10):  # max tool call rounds
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Collect text from this response turn
        text_parts = [b.text for b in response.content if hasattr(b, "text")]

        if response.stop_reason == "end_turn":
            final_text = "\n".join(text_parts).strip()
            history.append({"role": "assistant", "content": response.content})
            return final_text or "(done)"

        if response.stop_reason == "tool_use":
            # Execute all tool calls
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    logger.info(f"Tool call: {block.name}({block.input})")
                    tool_output = run_tool(block.input["command"])
                    logger.info(f"Tool output: {tool_output[:200]}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": tool_output,
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
            continue

        break

    return "Sorry, something went wrong with the AI response."


# ---------------------------------------------------------------------------
# Telegram handlers
# ---------------------------------------------------------------------------

def make_allowed_filter(user_id: int):
    return filters.User(user_id=user_id)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *personal-skills bot*\n\n"
        "Send me:\n"
        "• A Slack thread URL → I'll summarize or answer it\n"
        "• A YouTube/Medium URL → I'll summarize it\n"
        "• A Jira issue key → I'll summarize it\n"
        "• Any question about your codebase\n\n"
        "Commands:\n"
        "`/clear` — reset conversation\n"
        "`/help` — show this message",
        parse_mode="Markdown"
    )


async def clear_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conversation_history.pop(chat_id, None)
    await update.message.reply_text("🗑️ Conversation cleared.")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_text = update.message.text.strip()

    if not user_text:
        return

    # Show typing indicator
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        reply = await ask_claude(chat_id, user_text)
    except Exception as e:
        logger.error(f"Claude error: {e}")
        reply = f"❌ Error: {e}"

    # Telegram message limit is 4096 chars — split if needed
    if len(reply) <= 4096:
        await update.message.reply_text(reply)
    else:
        chunks = [reply[i:i+4000] for i in range(0, len(reply), 4000)]
        for chunk in chunks:
            await update.message.reply_text(chunk)
            await asyncio.sleep(0.3)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(token: str, user_id: int):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({"token": token, "user_id": user_id}, indent=2))
    CONFIG_FILE.chmod(0o600)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token",   help="Telegram bot token (from @BotFather)")
    parser.add_argument("--user-id", type=int, help="Your Telegram user ID (from @userinfobot)")
    parser.add_argument("--setup",   action="store_true", help="Save token+user-id to config and exit")
    args = parser.parse_args()

    config = load_config()

    token   = args.token   or config.get("token")   or os.environ.get("TELEGRAM_BOT_TOKEN")
    user_id = args.user_id or config.get("user_id") or os.environ.get("TELEGRAM_ALLOWED_USER_ID")

    if not token:
        print("ERROR: No Telegram bot token provided.")
        print("Get one from @BotFather on Telegram, then run:")
        print("  python3 telegram_bot.py --token <TOKEN> --user-id <YOUR_ID> --setup")
        sys.exit(1)

    if not user_id:
        print("ERROR: No allowed user ID provided.")
        print("Get your user ID from @userinfobot on Telegram, then run:")
        print("  python3 telegram_bot.py --token <TOKEN> --user-id <YOUR_ID> --setup")
        sys.exit(1)

    user_id = int(user_id)

    if args.setup:
        save_config(token, user_id)
        print(f"✓ Config saved to {CONFIG_FILE}")
        print(f"  Token : {token[:10]}...")
        print(f"  User ID: {user_id}")
        print("\nNow run without --setup to start the bot:")
        print("  python3 telegram_bot.py")
        return

    logger.info(f"Starting bot — only responding to user ID {user_id}")

    app = Application.builder().token(token).build()

    user_filter = make_allowed_filter(user_id)

    app.add_handler(CommandHandler("start", start_handler,   filters=user_filter))
    app.add_handler(CommandHandler("help",  start_handler,   filters=user_filter))
    app.add_handler(CommandHandler("clear", clear_handler,   filters=user_filter))
    app.add_handler(MessageHandler(filters.TEXT & user_filter, message_handler))

    logger.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
