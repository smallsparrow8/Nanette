#!/bin/bash
echo "=== Starting Nanette ==="

# Verify critical environment variables
echo "Checking environment..."
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY is not set!"
    exit 1
fi
echo "ANTHROPIC_API_KEY is set: YES"
echo "OPENAI_API_KEY is set: $([ -n "$OPENAI_API_KEY" ] && echo 'YES' || echo 'NO')"
echo "PINECONE_API_KEY is set: $([ -n "$PINECONE_API_KEY" ] && echo 'YES' || echo 'NO')"

# Start Python API in background, redirect output to show errors
echo "Starting Python API..."
python -m api.main 2>&1 &
API_PID=$!

# Wait for API to start and verify it's running
sleep 5
if ! kill -0 $API_PID 2>/dev/null; then
    echo "ERROR: Python API crashed on startup!"
    echo "Check logs above for error details."
    exit 1
fi
echo "Python API started successfully (PID: $API_PID)"

# Start Telegram bot in foreground
echo "Starting Telegram bot..."
echo "TELEGRAM_BOT_TOKEN is set: $([ -n "$TELEGRAM_BOT_TOKEN" ] && echo 'YES' || echo 'NO')"
echo "API_URL is: $API_URL"
echo "Changing to bot directory..."
cd bots/telegram-bot
echo "Current directory: $(pwd)"
echo "Checking if index.ts exists: $([ -f src/index.ts ] && echo 'YES' || echo 'NO')"
echo "Running ts-node..."
npx ts-node src/index.ts 2>&1

# If bot exits, keep container alive with API
wait $API_PID
