#!/usr/bin/env bash
# Install dependencies for ps:bot-telegram
set -e

echo "→ Installing python-telegram-bot and anthropic SDK..."
uv pip install "python-telegram-bot>=20.0" anthropic

echo "✓ Dependencies installed."
echo ""
echo "Next steps:"
echo "  1. Create a bot on Telegram: message @BotFather → /newbot"
echo "  2. Get your user ID: message @userinfobot on Telegram"
echo "  3. Save config:"
echo "     python3 $HOME/.local/share/personal-skills/scripts/bot/telegram_bot.py \\"
echo "       --token <BOT_TOKEN> --user-id <YOUR_USER_ID> --setup"
echo "  4. Start the bot:"
echo "     python3 $HOME/.local/share/personal-skills/scripts/bot/telegram_bot.py"
