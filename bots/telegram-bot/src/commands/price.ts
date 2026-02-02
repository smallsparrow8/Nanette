import { Context } from 'telegraf';
import axios from 'axios';

const API_URL = process.env.API_URL || 'http://localhost:8000';

export async function priceCommand(ctx: Context) {
  const text = ctx.message && 'text' in ctx.message ? ctx.message.text : '';
  const args = text.split(' ').slice(1);

  if (args.length === 0) {
    return ctx.reply(
      '💰 *Price Command*\n\n' +
      'Usage: `/price <token>`\n\n' +
      'Examples:\n' +
      '• `/price bitcoin`\n' +
      '• `/price ethereum`\n' +
      '• `/price btc`\n' +
      '• `/price eth`',
      { parse_mode: 'Markdown' }
    );
  }

  const token = args[0].toLowerCase();

  await ctx.sendChatAction('typing');

  try {
    const response = await axios.post(
      `${API_URL}/chat`,
      {
        message: `What's the current price of ${token}?`,
        conversation_history: [],
      },
      { timeout: 30000 }
    );

    const nanetteResponse = response.data.response;
    await ctx.reply(nanetteResponse, { parse_mode: 'Markdown' });

  } catch (error: any) {
    console.error('Error getting price:', error);
    await ctx.reply(
      `Sorry, I couldn't fetch the price for ${token}. Please try again or use a different token symbol.`
    );
  }
}
