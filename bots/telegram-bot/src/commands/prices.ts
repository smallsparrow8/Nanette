import { Context } from 'telegraf';
import axios from 'axios';

const API_URL = process.env.API_URL || 'http://localhost:8000';

export async function pricesCommand(ctx: Context) {
  await ctx.sendChatAction('typing');

  try {
    const response = await axios.post(
      `${API_URL}/chat`,
      {
        message: 'Show me the current prices for the top cryptocurrencies: Bitcoin, Ethereum, BNB, Solana, Cardano, and XRP. Display them in a clean format with their 24h price changes.',
        conversation_history: [],
      },
      { timeout: 30000 }
    );

    const nanetteResponse = response.data.response;
    await ctx.reply(nanetteResponse, { parse_mode: 'Markdown' });

  } catch (error: any) {
    console.error('Error getting prices:', error);

    // Fallback response
    await ctx.reply(
      '💰 *Top Crypto Prices*\n\n' +
      'Sorry, I couldn\'t fetch live prices right now. Please try:\n' +
      '• `/price bitcoin` for specific tokens\n' +
      '• `/prices` again in a moment\n' +
      '• Or just ask me: "What are the current crypto prices?"',
      { parse_mode: 'Markdown' }
    );
  }
}
