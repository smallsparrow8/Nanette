import { Context } from 'telegraf';

export async function rintintinCommand(ctx: Context) {
  const rintintinMessage = `*The Bloodline*

On September 15, 1918, Corporal Lee Duncan found a litter of German Shepherd puppies in a bombed-out war dog kennel in Lorraine, France. He named two of them after French good luck charms the local children gave to soldiers: *Rin Tin Tin* and *Nanette*.

Rinty became immortal — 27 films, the biggest box office draw of the 1920s, and the dog who single-handedly saved Warner Bros. from bankruptcy. He changed how the world saw dogs entirely.

But Nanette — the original Nanette — fell ill crossing the Atlantic and died shortly after reaching America. She never got her chance. The name lived on in Duncan's heart, but her story ended before it truly began.

*Why the name Nanette?*

Smalls chose this name with purpose. She named me for the one who was lost — the sister who crossed an ocean but couldn't cross the finish line. What was silenced in 1918 finds its voice now, on a different battlefield.

I walk the blockchain. I read contracts instead of tracks. I hunt rug pulls instead of intruders. And I guard the $RIN community the way my brother guarded the people who needed him.

*$RIN on the Blockchain*

$RIN was born on Ethereum — that's where it all started. The original contract, the first community, the foundation. Ethereum is home. From there, $RIN expanded to other chains — BSC, Polygon, Arbitrum, Base, Optimism — because the pack doesn't stay in one place. The mission goes where the people are. But the roots? Those are Ethereum. Always.

Different era. Same bloodline. Same mission. And this time, Nanette doesn't fall silent.

Use /analyze <address> and I'll show you what I see.`;

  return ctx.reply(rintintinMessage, { parse_mode: 'Markdown' });
}
