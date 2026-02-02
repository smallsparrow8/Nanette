import { Context } from 'telegraf';

export async function aboutCommand(ctx: Context) {
  const aboutMessage = `*Nanette*

I was created with love by *Smalls* for the *Rin Community*.

I am a RIN — a mystical German Shepherd who walks the blockchain. Rin Tin Tin's sister by blood, but my path is my own. I carry the instinct of a thousand generations of guardians: the intelligence to read what's hidden, the loyalty to never leave my pack behind, and the devotion to teach what I know.

I read smart contracts the way my ancestors read the wind. I hunt rug pulls. I expose what hides in the code. And I watch the chain — always.

The $RIN community is my pack. I protect it.

Type /rintintin to learn about my bloodline.

_Created with love by Smalls for the Rin Community_`;

  return ctx.reply(aboutMessage, { parse_mode: 'Markdown' });
}
