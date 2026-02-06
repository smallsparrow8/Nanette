import { Telegraf } from 'telegraf';
import { message } from 'telegraf/filters';
import { config } from 'dotenv';
import { analyzeCommand } from './commands/analyze';
import { helpCommand } from './commands/help';
import { aboutCommand } from './commands/about';
import { greetCommand } from './commands/greet';
import { rintintinCommand } from './commands/rintintin';
import { handleChatMessage, handleChatMediaMessage } from './commands/chat';
import { handleGroupMessage, handleGroupMediaMessage } from './commands/channel';
import { interactionsCommand } from './commands/interactions';
import { traceCommand } from './commands/trace';
import { configCommand } from './commands/config';
import { priceCommand } from './commands/price';
import { gasCommand } from './commands/gas';
import { infoCommand } from './commands/info';
import { trendingCommand } from './commands/trending';
import { caCommand } from './commands/ca';
import {
  memeCommand,
  jokeCommand,
  tipCommand,
  factCommand,
  eightBallCommand,
  flipCommand,
  rollCommand,
  quoteCommand,
  fortuneCommand,
  pawCommand,
  borkCommand,
} from './commands/fun';
import { withPermission } from './services/permissions';

// Load environment variables
config({ path: '../../.env' });

const TOKEN = process.env.TELEGRAM_BOT_TOKEN;

if (!TOKEN) {
  console.error('Missing TELEGRAM_BOT_TOKEN in environment variables');
  process.exit(1);
}

// Create Telegram bot
const bot = new Telegraf(TOKEN);

// Bot commands
bot.command('start', (ctx) => {
  return ctx.reply(
    `${ctx.from?.first_name}. I've been expecting you.

I am Nanette — an ancient guardian of the $RIN community. I read smart contracts, trace the wallets behind them, and protect those who seek my guidance.

Send me a contract address, ask me anything, or just talk to me.

Type /help to see my full range.`
  );
});

// Admin configuration — always available
bot.command('nanette_config', configCommand);

// Core commands — wrapped with permission checks
bot.command('analyze', withPermission('analyze', analyzeCommand));
bot.command('interactions', withPermission('interactions', interactionsCommand));
bot.command('trace', withPermission('trace', traceCommand));
bot.command('help', helpCommand);
bot.command('about', aboutCommand);
bot.command('greet', greetCommand);
bot.command('rintintin', rintintinCommand);

// Crypto commands
bot.command('price', withPermission('price', priceCommand));
bot.command('gas', withPermission('gas', gasCommand));
bot.command('info', withPermission('info', infoCommand));
bot.command('trending', withPermission('trending', trendingCommand));
bot.command('ca', withPermission('ca', caCommand));

// Fun commands
bot.command('meme', withPermission('meme', memeCommand));
bot.command('joke', withPermission('joke', jokeCommand));
bot.command('tip', withPermission('tip', tipCommand));
bot.command('fact', withPermission('fact', factCommand));
bot.command('8ball', withPermission('8ball', eightBallCommand));
bot.command('flip', withPermission('flip', flipCommand));
bot.command('roll', withPermission('roll', rollCommand));
bot.command('quote', withPermission('quote', quoteCommand));
bot.command('fortune', withPermission('fortune', fortuneCommand));
bot.command('paw', withPermission('paw', pawCommand));
bot.command('bork', withPermission('bork', borkCommand));

// Handle regular text messages — route by chat type
bot.on(message('text'), async (ctx) => {
  // Skip if it's a command
  if (ctx.message.text.startsWith('/')) {
    return;
  }

  // Group/supergroup messages → channel analyzer
  if (ctx.chat.type === 'group' || ctx.chat.type === 'supergroup') {
    await handleGroupMessage(ctx);
    return;
  }

  // DMs → conversational chat handler
  await handleChatMessage(ctx);
});

// Handle all media types — route by chat type
// Photos
bot.on(message('photo'), async (ctx) => {
  if (ctx.chat.type === 'group' || ctx.chat.type === 'supergroup') {
    await handleGroupMediaMessage(ctx);
  } else {
    await handleChatMediaMessage(ctx);
  }
});

// Documents (files, PDFs, images sent as files, etc.)
bot.on(message('document'), async (ctx) => {
  if (ctx.chat.type === 'group' || ctx.chat.type === 'supergroup') {
    await handleGroupMediaMessage(ctx);
  } else {
    await handleChatMediaMessage(ctx);
  }
});

// Stickers
bot.on(message('sticker'), async (ctx) => {
  if (ctx.chat.type === 'group' || ctx.chat.type === 'supergroup') {
    await handleGroupMediaMessage(ctx);
  } else {
    await handleChatMediaMessage(ctx);
  }
});

// Videos
bot.on(message('video'), async (ctx) => {
  if (ctx.chat.type === 'group' || ctx.chat.type === 'supergroup') {
    await handleGroupMediaMessage(ctx);
  } else {
    await handleChatMediaMessage(ctx);
  }
});

// Video notes (round videos)
bot.on(message('video_note'), async (ctx) => {
  if (ctx.chat.type === 'group' || ctx.chat.type === 'supergroup') {
    await handleGroupMediaMessage(ctx);
  } else {
    await handleChatMediaMessage(ctx);
  }
});

// Voice messages
bot.on(message('voice'), async (ctx) => {
  if (ctx.chat.type === 'group' || ctx.chat.type === 'supergroup') {
    await handleGroupMediaMessage(ctx);
  } else {
    await handleChatMediaMessage(ctx);
  }
});

// Audio files
bot.on(message('audio'), async (ctx) => {
  if (ctx.chat.type === 'group' || ctx.chat.type === 'supergroup') {
    await handleGroupMediaMessage(ctx);
  } else {
    await handleChatMediaMessage(ctx);
  }
});

// Animations (GIFs)
bot.on(message('animation'), async (ctx) => {
  if (ctx.chat.type === 'group' || ctx.chat.type === 'supergroup') {
    await handleGroupMediaMessage(ctx);
  } else {
    await handleChatMediaMessage(ctx);
  }
});

// Error handling
bot.catch((err, ctx) => {
  console.error('Error in bot:', err);
  ctx.reply('Something disrupted my senses. Try again in a moment.');
});

// Start bot
bot.launch()
  .then(() => {
    console.log('✅ Nanette Telegram bot is online!');
    console.log('Nanette is watching the chain.');
  })
  .catch((error) => {
    console.error('Failed to start bot:', error);
    process.exit(1);
  });

// Enable graceful stop
process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));
