#!/bin/bash
echo "=== Starting Nanette ==="

# Start Python API in background
echo "Starting Python API..."
python -m api.main &
API_PID=$!

# Wait a moment for API to start
sleep 3

# Start Telegram bot in foreground
echo "Starting Telegram bot..."
echo "TELEGRAM_BOT_TOKEN is set: $([ -n "$TELEGRAM_BOT_TOKEN" ] && echo 'YES' || echo 'NO')"
echo "API_URL is: $API_URL"
cd bots/telegram-bot
npx ts-node src/index.ts

# If bot exits, keep container alive with API
wait $API_PID
