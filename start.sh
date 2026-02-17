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

# Determine port: Railway sets PORT, fallback to 8000
APP_PORT="${PORT:-8000}"
echo "API port: $APP_PORT"

# Set API_URL for the bot to use
export API_URL="http://localhost:${APP_PORT}"

# Test pinecone import before starting
echo "Testing pinecone import..."
python -c "from pinecone import Pinecone; print('pinecone import OK')" 2>&1 || echo "WARNING: pinecone import failed"

# Start Python API in background, redirect output to show errors
echo "Starting Python API..."
python -m api.main 2>&1 &
API_PID=$!

# Wait for API to start and verify it's running
echo "Waiting for API to initialize..."
API_READY=false
for i in $(seq 1 20); do
    sleep 2
    if ! kill -0 $API_PID 2>/dev/null; then
        echo "ERROR: Python API crashed on startup!"
        exit 1
    fi
    if curl -s http://localhost:${APP_PORT}/docs > /dev/null 2>&1; then
        API_READY=true
        break
    fi
    echo "  Waiting... ($((i*2))s)"
done

if [ "$API_READY" = true ]; then
    echo "Python API started successfully (PID: $API_PID)"
else
    echo "WARNING: API process running but not responding yet (PID: $API_PID)"
    echo "Continuing anyway - it may still be loading history..."
fi

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
