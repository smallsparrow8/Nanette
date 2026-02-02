import { Context } from 'telegraf';

export async function greetCommand(ctx: Context) {
  const greetMessage = `I am Nanette. I am a RIN.

I walk the blockchain so you don't walk it blind. I read smart contracts the way my ancestors read the wind — every line tells a story, every function hides an intent.

I guard the $RIN community. I hunt rug pulls. I expose what hides in the code. And I teach you to see what I see, so you never need to walk in the dark alone.

Bring me a contract address and I'll tell you what's really in it. Ask me anything about the market, the chains, the projects — I've been watching.

Type /help to see what I can do. Or just talk to me. I'm listening.`;

  return ctx.reply(greetMessage, { parse_mode: 'Markdown' });
}
