import { ChatInputCommandInteraction, EmbedBuilder } from 'discord.js';

export async function helpCommand(interaction: ChatInputCommandInteraction) {
  const embed = new EmbedBuilder()
    .setTitle('Nanette — Guardian of $RIN')
    .setDescription('I walk the blockchain so you don\'t walk it blind.')
    .setColor(0x3498db)
    .addFields(
      {
        name: 'Analysis & Security',
        value: [
          '`/analyze <address> [blockchain]` — I read the contract and tell you what\'s hiding',
          '`/interactions <address> [blockchain]` — I trace where the money flows',
          '`/help` — This guide',
          '`/greet` — A proper introduction',
          '`/about` — Who I am',
          '`/rintintin` — My bloodline',
        ].join('\n'),
        inline: false,
      },
      {
        name: 'Chains I Watch',
        value: 'Ethereum · BSC · Polygon · Arbitrum · Base · Optimism',
        inline: false,
      },
      {
        name: 'Safety Score Levels',
        value: [
          '🟢 85-100: Clear skies',
          '🟢 70-84: Low risk',
          '🟡 50-69: Proceed with caution',
          '🟠 30-49: Danger in the air',
          '🔴 0-29: Walk away',
        ].join('\n'),
        inline: false,
      },
      {
        name: 'Admin Controls',
        value: '`/nanette_config` — View and manage my settings (analysis, chat, fun, crypto, channel analysis, clue detection, cooldown, admin list)',
        inline: false,
      },
      {
        name: 'Conversation',
        value: 'Mention me or DM me directly. No commands needed — just talk to me. I\'m always watching the chain.',
        inline: false,
      }
    )
    .setFooter({
      text: 'The chain doesn\'t lie — but it doesn\'t explain itself either. That\'s what I\'m for.',
    })
    .setTimestamp();

  await interaction.reply({
    embeds: [embed],
    ephemeral: false,
  });
}
