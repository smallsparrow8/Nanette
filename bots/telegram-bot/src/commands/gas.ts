import { Context } from 'telegraf';
import axios from 'axios';

const API_URL = process.env.API_URL || 'http://localhost:8000';

export async function gasCommand(ctx: Context) {
  await ctx.sendChatAction('typing');

  try {
    const response = await axios.post(
      `${API_URL}/chat`,
      {
        message: 'What are the current gas prices on Ethereum?',
        conversation_history: [],
      },
      { timeout: 30000 }
    );

    const nanetteResponse = response.data.response;
    await ctx.reply(nanetteResponse, { parse_mode: 'Markdown' });

  } catch (error: any) {
    console.error('Error getting gas prices:', error);
    await ctx.reply(
      '⛽ Sorry, I couldn\'t fetch current gas prices. Please try again in a moment!'
    );
  }
}
