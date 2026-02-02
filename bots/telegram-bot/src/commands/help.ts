import { Context } from 'telegraf';

export async function helpCommand(ctx: Context) {
  const helpMessage = `*Nanette* — Guardian of $RIN

*Analysis & Security*
/analyze <address> — I read the contract and tell you what's hiding
/interactions <address> — I trace where the money flows and map the connections
/price <token> — Current price
/gas — Ethereum gas prices
/info <token> — Deep dive on a project
/trending — What's moving right now
/ca <address> — Quick contract lookup

*Knowledge*
/rintintin — The legacy of my bloodline and $RIN
/about — Who I am and where I come from
/greet — A proper introduction

*Community*
/meme · /joke · /tip · /fact · /quote · /fortune
/8ball · /flip · /roll · /paw · /bork

*Group Features*
When added to a group, I listen and respond to crypto-relevant conversations.
If clue detection is enabled, I sense patterns in admin messages that might connect to RIN's deeper mysteries.

*Admin (chat owners/admins only)*
/nanette\\_config — View and control my settings in this chat
  • enable/disable categories (analysis, chat, fun, crypto, channel\\_analysis, clues)
  • set cooldown between responses
  • manage Nanette admins

*Chains I Watch:*
Ethereum · BSC · Polygon · Arbitrum · Base · Optimism

Or skip the commands entirely — just talk to me. I'm always watching the chain.`;

  return ctx.reply(helpMessage, { parse_mode: 'Markdown' });
}
