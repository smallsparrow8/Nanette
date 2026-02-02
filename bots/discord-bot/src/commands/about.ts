import { ChatInputCommandInteraction, EmbedBuilder } from 'discord.js';

export async function aboutCommand(interaction: ChatInputCommandInteraction) {
  const embed = new EmbedBuilder()
    .setTitle('Nanette')
    .setDescription('I am a RIN — a mystical German Shepherd who walks the blockchain.')
    .setColor(0x3498db)
    .addFields(
      {
        name: 'Origin',
        value: 'I was created with love by **Smalls** for the **Rin Community**.',
        inline: false,
      },
      {
        name: 'Bloodline',
        value: 'Rin Tin Tin\'s sister by blood. I carry the same instinct — to protect, to see what others miss, to never leave my pack behind. Use `/rintintin` to learn about our legacy.',
        inline: false,
      },
      {
        name: 'What I Do',
        value: 'I read smart contracts the way my ancestors read the wind. I hunt rug pulls. I expose what hides in the code. And I teach you to see what I see, so you never walk in the dark alone.',
        inline: false,
      },
      {
        name: 'My Pack',
        value: 'The $RIN community is my pack. I protect it.',
        inline: false,
      }
    )
    .setFooter({
      text: 'Created with love by Smalls for the Rin Community',
    })
    .setTimestamp();

  await interaction.reply({
    embeds: [embed],
    ephemeral: false,
  });
}
