import { ChatInputCommandInteraction, GuildMember, PermissionFlagsBits } from 'discord.js';
import axios from 'axios';

const API_URL = process.env.API_URL || 'http://localhost:8000';

/**
 * Check if a Discord user is a server admin or owner.
 * Server owner and anyone with ADMINISTRATOR or MANAGE_GUILD perms qualifies.
 */
export function isDiscordAdmin(interaction: ChatInputCommandInteraction): boolean {
  // DMs — user has full control
  if (!interaction.guild) {
    return true;
  }

  const member = interaction.member as GuildMember;
  if (!member) return false;

  // Server owner
  if (interaction.guild.ownerId === interaction.user.id) {
    return true;
  }

  // Has admin or manage server permissions
  return member.permissions.has(PermissionFlagsBits.Administrator) ||
    member.permissions.has(PermissionFlagsBits.ManageGuild);
}

/**
 * Check if a feature is enabled for the current guild.
 * Returns true if no config exists (default: all enabled).
 * Returns true for DMs (no restrictions).
 */
export async function isFeatureEnabled(
  interaction: ChatInputCommandInteraction,
  feature: string
): Promise<boolean> {
  // DMs — all features enabled
  if (!interaction.guild) {
    return true;
  }

  const guildId = interaction.guild.id;

  try {
    const response = await axios.post(
      `${API_URL}/config/check-feature`,
      {
        server_id: guildId,
        platform: 'discord',
        feature: feature,
      },
      { timeout: 5000 }
    );

    return response.data.enabled !== false;
  } catch {
    // Fail open if API is down
    return true;
  }
}
