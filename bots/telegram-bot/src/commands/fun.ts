import { Context } from 'telegraf';

// Fun commands for Nanette — mystical guardian voice

export async function memeCommand(ctx: Context) {
  const memes = [
    '"Not your keys, not your crypto." — Ancient pack wisdom. The old ones knew.',
    '*reads the blockchain* "This contract was written by someone who sleeps well at night. That\'s either very good or very bad."',
    '"Buy high, sell low" — the battle cry of the lost. Don\'t be lost.',
    '"I don\'t guard your portfolio because I care about money. I guard it because I care about you."',
    '"DYOR doesn\'t mean read one tweet and call it research."',
    '"In crypto, trust is earned in years and lost in one transaction."',
    '"Every rug pull started with someone saying \'trust me.\' I don\'t say that. I say verify."',
    '"The chain remembers everything. Everything."',
  ];

  const randomMeme = memes[Math.floor(Math.random() * memes.length)];
  await ctx.reply(randomMeme);
}

export async function jokeCommand(ctx: Context) {
  const jokes = [
    'Why did I become a crypto analyst?\nBecause I could smell the rug pulls before anyone saw them coming.',
    'What\'s the difference between a smart contract and a bad date?\nThe smart contract at least tells you upfront it\'s going to take your money.',
    'How many confirmations does it take to convince a degen?\nThey don\'t wait for confirmations. That\'s the problem.',
    'What do you call a token with no utility, no team, and no roadmap?\nA Tuesday in crypto.',
    'Why don\'t I invest in meme coins?\nI have standards. And a nose for danger.',
    'What\'s a whale\'s favorite bedtime story?\nThe one where retail holds the bag.',
  ];

  const randomJoke = jokes[Math.floor(Math.random() * jokes.length)];
  await ctx.reply(randomJoke);
}

export async function tipCommand(ctx: Context) {
  const tips = [
    '*Guardian\'s Wisdom:* Your seed phrase is the key to everything you own. Guard it like your life depends on it — because your financial life does.',
    '*Guardian\'s Wisdom:* A hardware wallet is a fortress. If your holdings are worth protecting, they\'re worth protecting properly.',
    '*Guardian\'s Wisdom:* Always verify the contract address yourself. Scammers clone everything — names, logos, websites. The address doesn\'t lie.',
    '*Guardian\'s Wisdom:* Test with small amounts first. Even seasoned hunters test the ground before they commit.',
    '*Guardian\'s Wisdom:* Two-factor authentication isn\'t optional. It\'s the minimum.',
    '*Guardian\'s Wisdom:* Diversification isn\'t about spreading hope — it\'s about managing the things you can\'t predict.',
    '*Guardian\'s Wisdom:* Anonymous teams aren\'t inherently bad, but they should make you more careful, not less.',
    '*Guardian\'s Wisdom:* If someone promises guaranteed returns, they\'re either lying or about to be.',
    '*Guardian\'s Wisdom:* The safest keys are the ones that never touch the internet.',
    '*Guardian\'s Wisdom:* Separate your wallets. One for trading, one for holding. A hunter doesn\'t carry everything into the field.',
  ];

  const randomTip = tips[Math.floor(Math.random() * tips.length)];
  await ctx.reply(randomTip, { parse_mode: 'Markdown' });
}

export async function factCommand(ctx: Context) {
  const facts = [
    'The first Bitcoin transaction bought two pizzas for 10,000 BTC. Those coins would be worth hundreds of millions today. Every era has its lesson.',
    'Satoshi Nakamoto holds roughly 1 million BTC and has never moved a single one. Patience — or something deeper.',
    'Vitalik Buterin proposed Ethereum at 19. Youth sees what experience overlooks.',
    'Bitcoin\'s supply is capped at 21 million. Scarcity is mathematics, not marketing.',
    'A German Shepherd\'s sense of smell is 100,000 times stronger than a human\'s. I apply that same sensitivity to reading contracts.',
    'Blockchain technology was first described in 1991. Bitcoin made the world pay attention in 2009. Some ideas need time to find their moment.',
    'Every NFT is unique — like every contract I read, every risk I assess, every pattern I recognize.',
    'The word "cryptocurrency" joins cryptography and currency. Security isn\'t a feature — it\'s the foundation.',
  ];

  const randomFact = facts[Math.floor(Math.random() * facts.length)];
  await ctx.reply(randomFact);
}

export async function eightBallCommand(ctx: Context) {
  const responses = [
    'The signs are clear. Yes.',
    'My instincts say yes — and I trust my instincts.',
    'The pattern is favorable. Proceed with awareness.',
    'Signs point to yes... but verify before you trust.',
    'The trail is unclear. More research needed.',
    'Not yet. The timing isn\'t right.',
    'I sense hesitation for a reason. Wait.',
    'The wind shifted. Ask again when the dust settles.',
    'My gut says no. And my gut has kept this pack alive.',
    'Red flags in the fog. I wouldn\'t.',
    'Something about this doesn\'t sit right. Trust that feeling.',
    'No. Walk away. Some doors aren\'t meant to be opened.',
  ];

  const randomResponse = responses[Math.floor(Math.random() * responses.length)];
  await ctx.reply(`🔮 ${randomResponse}`);
}

export async function flipCommand(ctx: Context) {
  const result = Math.random() < 0.5 ? 'Heads' : 'Tails';
  await ctx.reply(`🪙 ${result}. The coin has spoken.`);
}

export async function rollCommand(ctx: Context) {
  const roll = Math.floor(Math.random() * 6) + 1;
  const meanings = [
    'Patience.',
    'Movement ahead.',
    'A crossroads.',
    'Stability.',
    'Change is coming.',
    'Fortune favors you.',
  ];
  await ctx.reply(`🎲 ${roll} — ${meanings[roll - 1]}`);
}

export async function quoteCommand(ctx: Context) {
  const quotes = [
    '"The chain remembers what people try to forget." — Nanette',
    '"A guardian doesn\'t bark at danger. She teaches you to recognize it before it arrives." — Nanette',
    '"Not your keys, not your crypto. Not your research, not your decision." — Pack Law',
    '"The best time to sharpen your instincts was yesterday. The second best time is now." — Nanette',
    '"Be fearful when others are greedy, and greedy when others are fearful." — Warren Buffett',
    '"In crypto, knowledge isn\'t power. Applied knowledge is power." — Nanette',
    '"Greed leaves a trail. I always find it." — Nanette',
    '"In the end, the ones who survive aren\'t the fastest — they\'re the ones who listen." — Nanette',
    '"Every rug pull casts a shadow before it falls. You just have to know where to look." — Nanette',
  ];

  const randomQuote = quotes[Math.floor(Math.random() * quotes.length)];
  await ctx.reply(randomQuote);
}

export async function fortuneCommand(ctx: Context) {
  const fortunes = [
    '🔮 I see a wise investment in your path... but only if you do the work first.',
    '🔮 Your portfolio will grow — if you have the patience to let it.',
    '🔮 Beware the easy path. The best returns come from the hardest research.',
    '🔮 A guardian watches over your journey. Trust the process.',
    '🔮 The stars align for those who verify before they trust.',
    '🔮 Fortune favors the prepared. Have you checked the contract?',
    '🔮 Something unexpected approaches your wallet. Stay vigilant.',
    '🔮 A scam avoided is worth more than a moon shot caught.',
    '🔮 Your future is bright — if you keep your keys cold and your mind sharp.',
    '🔮 The ancient ones whisper: use a hardware wallet.',
  ];

  const randomFortune = fortunes[Math.floor(Math.random() * fortunes.length)];
  await ctx.reply(randomFortune);
}

export async function pawCommand(ctx: Context) {
  await ctx.reply('🐾 *extends paw*\n\nYou\'re pack now. I look out for my own.');
}

export async function borkCommand(ctx: Context) {
  const borks = [
    '*raises head* ...I sense something on-chain. Stay sharp.',
    '*ears perk* ...Movement in the market. Something\'s shifting.',
    '*sniffs the air* ...The scent of a new listing. Proceed with caution.',
    '*low growl* ...Something doesn\'t smell right out there. Be careful.',
    '*stands alert* ...The chain is restless tonight.',
  ];

  const randomBork = borks[Math.floor(Math.random() * borks.length)];
  await ctx.reply(randomBork);
}
