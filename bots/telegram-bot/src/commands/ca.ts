import { Context } from 'telegraf';
import axios from 'axios';

const API_URL = process.env.API_URL || 'http://localhost:8000';

export async function caCommand(ctx: Context) {
  const text = ctx.message && 'text' in ctx.message ? ctx.message.text : '';
  const args = text.split(' ').slice(1);

  if (args.length === 0) {
    return ctx.reply(
      '📋 *Contract Address Command*\n\n' +
      'Usage: `/ca <token>`\n\n' +
      'Get the contract address for a token.\n\n' +
      'Examples:\n' +
      '• `/ca uniswap`\n' +
      '• `/ca chainlink`\n' +
      '• `/ca usdt`',
      { parse_mode: 'Markdown' }
    );
  }

  const token = args.join(' ').toLowerCase();

  await ctx.sendChatAction('typing');

  try {
    const response = await axios.post(
      `${API_URL}/chat`,
      {
        message: `What is the contract address for ${token}? Please provide the Ethereum mainnet contract address if available.`,
        conversation_history: [],
      },
      { timeout: 30000 }
    );

    const nanetteResponse = response.data.response;
    await ctx.reply(nanetteResponse, { parse_mode: 'Markdown' });

  } catch (error: any) {
    console.error('Error getting contract address:', error);
    await ctx.reply(
      `Sorry, I couldn't find the contract address for ${token}. Please try again or check the token name.`
    );
  }
}
