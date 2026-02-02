FROM python:3.11-slim

# Install Node.js 20
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Telegram bot dependencies
COPY bots/telegram-bot/package.json bots/telegram-bot/package-lock.json bots/telegram-bot/
RUN cd bots/telegram-bot && npm install

# Copy all source code
COPY . .

# Expose API port
EXPOSE 8000

# Start both Python API and Telegram bot
CMD python -m api.main & cd bots/telegram-bot && npx ts-node src/index.ts
