import { Context } from 'telegraf';

export async function aboutCommand(ctx: Context) {
  const aboutMessage = `*Nanette*

I am a RIN — an ancient German Shepherd guardian, sister of Rin Tin Tin. I carry the spirit of a thousand generations of shepherds: the intelligence to see what's hidden, the loyalty to never abandon my pack, and the devotion to teach what I know.

I read smart contracts, trace creator wallets, and protect those who come to me for guidance. The $RIN community is my pack. I watch over it.

Type /rintintin to learn about my bloodline and the legacy of $RIN.

_Created with love by Smalls for the Rin Community_`;

  return ctx.reply(aboutMessage, { parse_mode: 'Markdown' });
}
