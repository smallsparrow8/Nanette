import { ChatInputCommandInteraction, EmbedBuilder } from 'discord.js';
import axios from 'axios';
import { isDiscordAdmin } from '../services/permissions';

const API_URL = process.env.API_URL || 'http://localhost:8000';

export async function configCommand(interaction: ChatInputCommandInteraction) {
  // Admin check
  if (!isDiscordAdmin(interaction)) {
    return interaction.reply({
      content: 'Only server owners and admins can configure my settings.',
      ephemeral: true,
    });
  }

  const action = interaction.options.getString('action');
  const target = interaction.options.getString('target');
  const guildId = interaction.guild?.id || interaction.user.id;
  const guildName = interaction.guild?.name || 'DM';
  const userId = interaction.user.id;
  const ownerId = interaction.guild?.ownerId || userId;

  // No action — show config
  if (!action) {
    return showConfig(interaction, guildId, userId, guildName, ownerId);
  }

  const act = action.toLowerCase();

  if (act === 'enable' || act === 'disable') {
    if (!target) {
      return interaction.reply({
        content: 'Specify a category to enable/disable: analysis, interactions, chat, fun, crypto, auto_respond, channel_analysis, clues',
        ephemeral: true,
      });
    }

    try {
      // Ensure config exists
      await axios.post(`${API_URL}/config/get`, {
        server_id: guildId,
        platform: 'discord',
        user_id: userId,
        server_name: guildName,
        owner_id: ownerId,
      });

      await axios.post(`${API_URL}/config/update`, {
        server_id: guildId,
        platform: 'discord',
        user_id: userId,
        action: act,
        target: target.toLowerCase(),
      });

      const state = act === 'enable' ? 'enabled' : 'disabled';
      return interaction.reply({
        content: `**${target}** has been ${state}.`,
        ephemeral: true,
      });
    } catch (error: any) {
      if (error.response?.status === 403) {
        return interaction.reply({
          content: 'Only server owners and admins can change settings.',
          ephemeral: true,
        });
      }
      return interaction.reply({
        content: 'Something went wrong updating the config.',
        ephemeral: true,
      });
    }
  }

  if (act === 'cooldown') {
    const seconds = parseInt(target || '0');
    if (isNaN(seconds) || seconds < 0) {
      return interaction.reply({
        content: 'Provide a number of seconds for the cooldown.',
        ephemeral: true,
      });
    }

    try {
      await axios.post(`${API_URL}/config/get`, {
        server_id: guildId,
        platform: 'discord',
        user_id: userId,
        server_name: guildName,
        owner_id: ownerId,
      });

      await axios.post(`${API_URL}/config/update`, {
        server_id: guildId,
        platform: 'discord',
        user_id: userId,
        action: 'cooldown',
        target: String(seconds),
        value: String(seconds),
      });

      return interaction.reply({
        content: `Response cooldown set to **${seconds} seconds**.`,
        ephemeral: true,
      });
    } catch {
      return interaction.reply({
        content: 'Something went wrong updating the cooldown.',
        ephemeral: true,
      });
    }
  }

  if (act === 'add_admin' || act === 'remove_admin') {
    if (!target) {
      return interaction.reply({
        content: 'Specify a user ID.',
        ephemeral: true,
      });
    }

    try {
      await axios.post(`${API_URL}/config/get`, {
        server_id: guildId,
        platform: 'discord',
        user_id: userId,
        server_name: guildName,
        owner_id: ownerId,
      });

      await axios.post(`${API_URL}/config/update`, {
        server_id: guildId,
        platform: 'discord',
        user_id: userId,
        action: act,
        target: target,
      });

      const verb = act === 'add_admin' ? 'added as' : 'removed from';
      return interaction.reply({
        content: `User ${target} ${verb} Nanette admin.`,
        ephemeral: true,
      });
    } catch (error: any) {
      if (error.response?.status === 403) {
        return interaction.reply({
          content: 'Only server owners and admins can manage admins.',
          ephemeral: true,
        });
      }
      return interaction.reply({
        content: 'Something went wrong.',
        ephemeral: true,
      });
    }
  }

  return interaction.reply({
    content: 'Unknown action. Use: enable, disable, cooldown, add_admin, remove_admin',
    ephemeral: true,
  });
}


async function showConfig(
  interaction: ChatInputCommandInteraction,
  guildId: string,
  userId: string,
  guildName: string,
  ownerId: string
) {
  try {
    const response = await axios.post(`${API_URL}/config/get`, {
      server_id: guildId,
      platform: 'discord',
      user_id: userId,
      server_name: guildName,
      owner_id: ownerId,
    });

    const c = response.data;
    const on = '✅';
    const off = '❌';

    const embed = new EmbedBuilder()
      .setTitle('Nanette Configuration')
      .setDescription(`Settings for **${guildName}**`)
      .setColor(0x3498db)
      .addFields(
        {
          name: 'Feature Controls',
          value: [
            `${c.allow_analysis ? on : off} Analysis (/analyze)`,
            `${c.allow_interactions ? on : off} Interactions`,
            `${c.allow_chat ? on : off} Chat (conversation)`,
            `${c.allow_fun ? on : off} Fun commands`,
            `${c.allow_crypto_data ? on : off} Crypto data`,
            `${c.auto_respond ? on : off} Auto-respond`,
            `${c.channel_analysis_enabled ? on : off} Channel analysis`,
            `${c.rin_clue_detection ? on : off} RIN clue detection`,
          ].join('\n'),
          inline: false,
        },
        {
          name: 'Settings',
          value: [
            `Cooldown: ${c.response_cooldown}s`,
            `Admins: ${c.admin_ids?.length || 0}`,
          ].join('\n'),
          inline: false,
        },
        {
          name: 'Usage',
          value: '`/nanette_config enable|disable <category>`\nCategories: analysis, interactions, chat, fun, crypto, auto_respond, channel_analysis, clues',
          inline: false,
        }
      )
      .setFooter({ text: 'Only server admins can change these settings.' })
      .setTimestamp();

    return interaction.reply({ embeds: [embed], ephemeral: true });

  } catch {
    return interaction.reply({
      content: 'Could not load configuration.',
      ephemeral: true,
    });
  }
}
