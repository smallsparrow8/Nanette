import { Context } from 'telegraf';
import axios from 'axios';

const API_URL = process.env.API_URL || 'http://localhost:8000';

export async function infoCommand(ctx: Context) {
  const text = ctx.message && 'text' in ctx.message ? ctx.message.text : '';
  const args = text.split(' ').slice(1);

  if (args.length === 0) {
    return ctx.reply(
      'ℹ️ *Token Info Command*\n\n' +
      'Usage: `/info <token>`\n\n' +
      'Get detailed information about a cryptocurrency.\n\n' +
      'Examples:\n' +
      '• `/info bitcoin`\n' +
      '• `/info ethereum`\n' +
      '• `/info cardano`',
      { parse_mode: 'Markdown' }
    );
  }

  const token = args.join(' ').toLowerCase();

  await ctx.sendChatAction('typing');

  try {
    const response = await axios.post(
      `${API_URL}/chat`,
      {
        message: `Give me detailed information about ${token}`,
        conversation_history: [],
      },
      { timeout: 30000 }
    );

    const nanetteResponse = response.data.response;

    // Split if too long
    if (nanetteResponse.length > 4000) {
      const chunks = splitMessage(nanetteResponse, 4000);
      for (const chunk of chunks) {
        await ctx.reply(chunk, { parse_mode: 'Markdown' });
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    } else {
      await ctx.reply(nanetteResponse, { parse_mode: 'Markdown' });
    }

  } catch (error: any) {
    console.error('Error getting token info:', error);
    await ctx.reply(
      `Sorry, I couldn't fetch information for ${token}. Please try again or check the token name.`
    );
  }
}

function splitMessage(text: string, maxLength: number): string[] {
  const chunks: string[] = [];
  let currentChunk = '';
  const lines = text.split('\n');

  for (const line of lines) {
    if (currentChunk.length + line.length + 1 > maxLength) {
      if (currentChunk) chunks.push(currentChunk);
      currentChunk = line;
    } else {
      currentChunk += (currentChunk ? '\n' : '') + line;
    }
  }
  if (currentChunk) chunks.push(currentChunk);
  return chunks;
}
