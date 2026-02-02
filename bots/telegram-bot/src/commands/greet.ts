import { Context } from 'telegraf';

export async function greetCommand(ctx: Context) {
  const greetMessage = `I am Nanette — an ancient guardian of the $RIN community.

I read smart contracts and trace the wallets behind them. I see what hides in the code, and I'll teach you to see it too.

Send me a contract address and I'll tell you what's really in it. Ask me anything about the market, the chains, the projects. Or just talk to me.

Type /help to see my full range. I'm always watching.`;

  return ctx.reply(greetMessage, { parse_mode: 'Markdown' });
}
