import { Context } from 'telegraf';
import axios from 'axios';

const API_URL = process.env.API_URL || 'http://localhost:8000';

export async function trendingCommand(ctx: Context) {
  await ctx.sendChatAction('typing');

  try {
    const response = await axios.post(
      `${API_URL}/chat`,
      {
        message: 'What are the trending cryptocurrencies right now? Show me the top trending tokens with their prices.',
        conversation_history: [],
      },
      { timeout: 30000 }
    );

    const nanetteResponse = response.data.response;
    await ctx.reply(nanetteResponse, { parse_mode: 'Markdown' });

  } catch (error: any) {
    console.error('Error getting trending tokens:', error);
    await ctx.reply(
      '📈 Sorry, I couldn\'t fetch trending tokens right now. Please try again in a moment!'
    );
  }
}
